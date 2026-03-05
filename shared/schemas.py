"""Shared schemas for IndMoney RAG Chatbot."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FundSource:
    """Source URL for a fund."""

    url: str
    label: str


@dataclass
class ChatResponse:
    """Response from the chat API."""

    answer: str
    sources: list[FundSource]
    refused: bool = False
    refusal_reason: Optional[str] = None


@dataclass
class Chunk:
    """Processed chunk for embedding."""

    chunk_id: str
    fund_id: str
    fund_name: str
    section: str
    content: str
    source_url: str
    last_updated: str
