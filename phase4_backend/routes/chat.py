"""POST /chat: RAG endpoint with safety checks."""

from __future__ import annotations

import logging
from fastapi import APIRouter
from pydantic import BaseModel

from phase4_backend.safety.input_validator import validate_user_message
from phase4_backend.safety.query_classifier import classify_query
from phase4_backend.rag.retriever import retrieve, detect_mentioned_funds
from phase4_backend.rag.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from phase4_backend.rag.response_formatter import format_sources, ensure_last_updated_suffix
from phase4_backend import config

log = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    fund_ids: list[str] | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    refused: bool
    refusal_reason: str | None = None


RATE_LIMIT_BASE = (
    "We've hit the free-tier limit for this demo. This project uses a free-tier model with a daily cap. "
    "Please try again in a few minutes. We're sorry for the inconvenience."
)


def _call_gemini(system_prompt: str, user_prompt: str, max_tokens: int = 256) -> tuple[str, bool]:
    """Call Google Gemini API. Returns (answer, is_rate_limit_error)."""
    if not config.GEMINI_API_KEY:
        return "Gemini API key not configured. Set GEMINI_API_KEY in environment.", False
    try:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=config.GEMINI_MODEL,
            system_instruction=system_prompt,
        )
        resp = model.generate_content(
            user_prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.1,
            ),
        )
        if resp and resp.text:
            return resp.text.strip(), False
        return "No answer generated.", False
    except Exception as e:
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "rate" in err_str or "resource" in err_str:
            log.warning("Gemini rate limit: %s", e)
            return RATE_LIMIT_BASE, True
        return f"Error generating answer: {e}", False


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    message = (request.message or "").strip()
    # 1) PII check
    valid, refusal = validate_user_message(message)
    if not valid:
        return ChatResponse(
            answer="",
            sources=[],
            refused=True,
            refusal_reason=refusal,
        )
    # 2) Opinion / compare check
    action, refusal_msg = classify_query(message)
    if action != "answer" and refusal_msg:
        return ChatResponse(
            answer="",
            sources=[],
            refused=True,
            refusal_reason=refusal_msg,
        )
    # 3) Fund mismatch check
    if request.fund_ids:
        mentioned = detect_mentioned_funds(message)
        unselected = [(fid, name) for fid, name in mentioned if fid not in request.fund_ids]
        if unselected:
            names = ", ".join(name for _, name in unselected)
            return ChatResponse(
                answer="",
                sources=[],
                refused=True,
                refusal_reason=f"Your question mentions {names} which is not selected in the filter. Please select it from the filter for accurate results.",
            )
    # 4) Retrieve (optionally filtered by selected funds)
    retrieved = retrieve(
        message,
        config.CHROMA_PERSIST_DIR,
        config.COLLECTION_NAME,
        config.EMBEDDING_MODEL_NAME,
        top_k=config.RETRIEVAL_TOP_K,
        fund_ids=request.fund_ids,
    )
    context_docs = [r["document"] for r in retrieved]
    unique_funds = len({r["fund_id"] for r in retrieved if r.get("fund_id")})
    user_prompt = build_user_prompt(message, context_docs, num_funds=unique_funds)
    # 4) Gemini
    max_tokens = 256 if unique_funds <= 1 else 128 + 64 * unique_funds
    answer, is_rate_limit = _call_gemini(SYSTEM_PROMPT, user_prompt, max_tokens=max_tokens)
    if not is_rate_limit:
        answer = ensure_last_updated_suffix(answer)
    if is_rate_limit:
        return ChatResponse(
            answer=answer,
            sources=[],
            refused=False,
            refusal_reason=None,
        )
    sources = format_sources(
        retrieved,
        answer=answer,
        query=message,
        max_sources=config.MAX_SOURCES_DISPLAY,
    )
    return ChatResponse(
        answer=answer,
        sources=sources,
        refused=False,
        refusal_reason=None,
    )
