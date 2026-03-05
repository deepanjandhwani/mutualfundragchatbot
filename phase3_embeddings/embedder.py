"""Load embedding model and generate embeddings for chunk text."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, List

logger = logging.getLogger(__name__)

_model = None

# Use project-local cache so Hugging Face can write inside workspace.
# At deploy: set EMBEDDING_CACHE_DIR to a path that already contains the model (e.g. baked into image).
_CACHE_DIR = Path(
    os.environ.get("EMBEDDING_CACHE_DIR")
    or (Path(__file__).resolve().parent.parent / ".cache" / "huggingface")
)
os.environ.setdefault("HF_HOME", str(_CACHE_DIR))
os.environ.setdefault("TRANSFORMERS_CACHE", str(_CACHE_DIR))


def _get_cached_model_path(cache_dir: Path, model_name: str) -> Path | None:
    """Return path to cached model snapshot if present, else None. Enables fully offline load."""
    safe = model_name.replace("/", "--")
    models_dir = cache_dir / "hub" / f"models--{safe}"
    snapshots_dir = models_dir / "snapshots"
    if not snapshots_dir.exists():
        return None
    for snapshot in snapshots_dir.iterdir():
        if snapshot.is_dir() and (snapshot / "config.json").exists():
            return snapshot
    return None


def get_embedding_model(model_name: str):
    """Load and cache the sentence-transformers model. Uses local cache when present to avoid network."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        cache_dir = Path(_CACHE_DIR)
        cache_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = _get_cached_model_path(cache_dir, model_name)
        if snapshot_path is not None:
            # Load by path so no Hugging Face connection is attempted
            os.environ["HF_HUB_OFFLINE"] = "1"
            logger.info("Loading embedding model from local cache: %s", snapshot_path)
            try:
                _model = SentenceTransformer(str(snapshot_path), local_files_only=True)
            finally:
                os.environ.pop("HF_HUB_OFFLINE", None)
        else:
            logger.info("Loading embedding model: %s (may download from Hugging Face)", model_name)
            _model = SentenceTransformer(
                model_name,
                cache_folder=str(cache_dir),
                local_files_only=False,
            )
    return _model


def content_to_text(content: Any) -> str:
    """Convert chunk content to a single string for embedding (str or dict → str)."""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    return str(content)


def encode(texts: List[str], model_name: str) -> List[List[float]]:
    """Generate embeddings for a list of texts. Returns list of embedding vectors."""
    if not texts:
        return []
    model = get_embedding_model(model_name)
    embeddings = model.encode(texts, show_progress_bar=len(texts) > 10)
    return embeddings.tolist()
