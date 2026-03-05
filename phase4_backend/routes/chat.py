"""POST /chat: RAG endpoint with safety checks."""

from __future__ import annotations

import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from phase4_backend.safety.input_validator import validate_user_message
from phase4_backend.safety.query_classifier import classify_query
from phase4_backend.rag.retriever import retrieve
from phase4_backend.rag.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from phase4_backend.rag.response_formatter import format_sources, ensure_last_updated_suffix
from phase4_backend import config

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    refused: bool
    refusal_reason: str | None = None


# Base message when GROQ free-tier rate limit (429) is hit; timing is appended when available
RATE_LIMIT_BASE = (
    "We've hit the free-tier limit for this demo. This project uses a free-tier model with a daily cap. "
)

# Match "Please try again in 14m14.496s" or "1h3m9.504s"
_RETRY_IN_PATTERN = re.compile(
    r"try again in\s+([\dhm.]+s)",
    re.IGNORECASE,
)


def _parse_retry_time(err_message: str) -> str | None:
    """Extract human-readable retry time from GROQ 429 message. Returns e.g. '14 minutes' or '1 hour 3 minutes'."""
    if not err_message:
        return None
    m = _RETRY_IN_PATTERN.search(err_message)
    if not m:
        return None
    raw = m.group(1).strip().rstrip(".")  # e.g. "14m14.496s" or "1h3m9.504s"
    parts = []
    h = re.search(r"(\d+)h", raw, re.IGNORECASE)
    if h:
        hr = int(h.group(1))
        parts.append(f"{hr} hour" if hr == 1 else f"{hr} hours")
    mn = re.search(r"(\d+)m", raw, re.IGNORECASE)
    if mn:
        mins = int(mn.group(1))
        parts.append(f"{mins} minute" if mins == 1 else f"{mins} minutes")
    s = re.search(r"(\d+)\.?\d*s", raw, re.IGNORECASE)
    if s and not parts:  # only add seconds if no hours/minutes
        secs = int(s.group(1))
        parts.append(f"{secs} second" if secs == 1 else f"{secs} seconds")
    elif s and int(s.group(1)) >= 30 and mn and int(mn.group(1)) == 0:
        # e.g. "45s" -> round to 1 minute
        parts.append("1 minute")
    if not parts:
        return None
    return " ".join(parts)


def _rate_limit_type(err_message: str) -> str:
    """Identify which limit was hit from GROQ 429 body: 'daily' (TPD) or 'per-minute' (TPM)."""
    if not err_message:
        return "rate limit"
    t = err_message.lower()
    if "per day" in t or "tpd" in t or "tokens per day" in t:
        return "daily limit"
    if "per minute" in t or "tpm" in t or "tokens per minute" in t:
        return "per-minute limit"
    return "rate limit"


def _build_rate_limit_message(retry_in: str | None, limit_type: str | None = None) -> str:
    if retry_in:
        limit_note = f" ({limit_type})" if limit_type else ""
        return (
            RATE_LIMIT_BASE
            + f"The service suggests waiting about {retry_in} before retrying{limit_note}. "
            + "The service uses both a per-minute and a daily cap, so the wait time can refer to either. "
            + "We're sorry for the inconvenience."
        )
    return (
        RATE_LIMIT_BASE
        + "Please try again in a few minutes when the limit resets, or try again later. We're sorry for the inconvenience."
    )


def _call_groq(system_prompt: str, user_prompt: str) -> tuple[str, bool]:
    """
    Call GROQ API. Returns (answer, is_rate_limit_error).
    On 429 rate limit, returns a friendly message and True so the route can omit sources.
    """
    if not config.GROQ_API_KEY:
        return "GROQ API key not configured. Set GROQ_API_KEY in environment.", False
    try:
        from groq import Groq
        from groq import RateLimitError as GroqRateLimitError
        client = Groq(api_key=config.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=256,
            temperature=0.1,
        )
        if resp.choices and len(resp.choices) > 0:
            return (resp.choices[0].message.content or "").strip(), False
    except GroqRateLimitError as e:
        err_msg = getattr(e, "message", None) or str(e)
        retry_in = _parse_retry_time(err_msg)
        limit_type = _rate_limit_type(err_msg)
        return _build_rate_limit_message(retry_in, limit_type), True
    except Exception as e:
        err_str = str(e).lower()
        if "429" in err_str or "rate_limit" in err_str or "rate limit" in err_str:
            err_msg = str(e)
            retry_in = _parse_retry_time(err_msg)
            limit_type = _rate_limit_type(err_msg)
            return _build_rate_limit_message(retry_in, limit_type), True
        return f"Error generating answer: {e}", False
    return "", False


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
            answer=refusal_msg,
            sources=[],
            refused=True,
            refusal_reason=refusal_msg,
        )
    # 3) Retrieve
    retrieved = retrieve(
        message,
        config.CHROMA_PERSIST_DIR,
        config.COLLECTION_NAME,
        config.EMBEDDING_MODEL_NAME,
        top_k=config.RETRIEVAL_TOP_K,
    )
    context_docs = [r["document"] for r in retrieved]
    user_prompt = build_user_prompt(message, context_docs)
    # 4) GROQ
    answer, is_rate_limit = _call_groq(SYSTEM_PROMPT, user_prompt)
    if not is_rate_limit:
        answer = ensure_last_updated_suffix(answer)
    # On rate limit, show friendly message and no sources
    if is_rate_limit:
        return ChatResponse(
            answer=answer,
            sources=[],
            refused=False,
            refusal_reason=None,
        )
    # Include sources for funds mentioned in the answer; fallback to query-based match if none.
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
