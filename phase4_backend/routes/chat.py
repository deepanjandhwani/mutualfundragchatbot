"""POST /chat: RAG endpoint with safety checks."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

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

_gemini_executor = ThreadPoolExecutor(max_workers=2)

# ── Lazy-init Gemini model (configured once) ────────────────────────
_genai_model = None


def _get_genai_model():
    global _genai_model
    if _genai_model is None:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        _genai_model = genai.GenerativeModel(
            model_name=config.GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
    return _genai_model


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

TIMEOUT_MSG = (
    "The model is currently unreachable from this local environment. "
    "Please check internet/VPN and try again."
)


def _call_gemini_inner(user_prompt: str, max_tokens: int) -> str:
    """Actual Gemini call (runs inside threadpool for timeout support)."""
    import google.generativeai as genai
    model = _get_genai_model()
    resp = model.generate_content(
        user_prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.1,
        ),
        request_options={"timeout": config.GEMINI_TIMEOUT_SECONDS},
    )
    if resp and resp.text:
        return resp.text.strip()
    return "No answer generated."


def _call_gemini(user_prompt: str, max_tokens: int = 256) -> tuple[str, bool]:
    """Call Google Gemini API with timeout. Returns (answer, is_rate_limit_error)."""
    if not config.GEMINI_API_KEY:
        return "Gemini API key not configured. Set GEMINI_API_KEY in environment.", False
    try:
        future = _gemini_executor.submit(_call_gemini_inner, user_prompt, max_tokens)
        answer = future.result(timeout=config.GEMINI_TIMEOUT_SECONDS + 1)
        return answer, False
    except FuturesTimeoutError:
        log.warning("Gemini call timed out after %ss", config.GEMINI_TIMEOUT_SECONDS)
        return TIMEOUT_MSG, False
    except Exception as e:
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "rate" in err_str or "resource" in err_str:
            log.warning("Gemini rate limit: %s", e)
            return RATE_LIMIT_BASE, True
        log.exception("Gemini error")
        return f"Error generating answer: {e}", False


def _effective_top_k(base_top_k: int, fund_ids: list[str] | None) -> int:
    """Reduce context window for multi-fund queries to keep latency stable."""
    if not fund_ids:
        return base_top_k
    n = len(fund_ids)
    if n == 2:
        return min(base_top_k, config.TOP_K_WHEN_2_FUNDS)
    if n >= 3:
        return min(base_top_k, config.TOP_K_WHEN_3_FUNDS)
    return base_top_k


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    t_start = time.perf_counter()
    message = (request.message or "").strip()

    # 1) PII check
    valid, refusal = validate_user_message(message)
    if not valid:
        return ChatResponse(answer="", sources=[], refused=True, refusal_reason=refusal)

    # 2) Opinion / compare check
    action, refusal_msg = classify_query(message)
    if action != "answer" and refusal_msg:
        return ChatResponse(answer="", sources=[], refused=True, refusal_reason=refusal_msg)

    # 3) Fund mismatch check
    if request.fund_ids:
        mentioned = detect_mentioned_funds(message)
        unselected = [(fid, name) for fid, name in mentioned if fid not in request.fund_ids]
        if unselected:
            names = ", ".join(name for _, name in unselected)
            return ChatResponse(
                answer="", sources=[], refused=True,
                refusal_reason=f"Your question mentions {names} which is not selected in the filter. Please select it from the filter for accurate results.",
            )

    # 4) Retrieve (optionally filtered by selected funds)
    top_k = _effective_top_k(config.RETRIEVAL_TOP_K, request.fund_ids)
    t_ret = time.perf_counter()
    retrieved = retrieve(
        message,
        config.CHROMA_PERSIST_DIR,
        config.COLLECTION_NAME,
        config.EMBEDDING_MODEL_NAME,
        top_k=top_k,
        fund_ids=request.fund_ids,
    )
    log.info("retrieve took %.2fs  (top_k=%d, docs=%d)", time.perf_counter() - t_ret, top_k, len(retrieved))

    context_docs = [r["document"] for r in retrieved]
    unique_funds = len({r["fund_id"] for r in retrieved if r.get("fund_id")})
    user_prompt = build_user_prompt(message, context_docs, num_funds=unique_funds)

    # 5) Gemini
    max_tokens = 256 if unique_funds <= 1 else 128 + 64 * unique_funds
    t_llm = time.perf_counter()
    answer, is_rate_limit = _call_gemini(user_prompt, max_tokens=max_tokens)
    log.info("gemini took %.2fs", time.perf_counter() - t_llm)

    if not is_rate_limit:
        answer = ensure_last_updated_suffix(answer)
    if is_rate_limit:
        return ChatResponse(answer=answer, sources=[], refused=False, refusal_reason=None)

    sources = format_sources(retrieved, answer=answer, query=message, max_sources=config.MAX_SOURCES_DISPLAY)
    log.info("total /chat %.2fs", time.perf_counter() - t_start)
    return ChatResponse(answer=answer, sources=sources, refused=False, refusal_reason=None)
