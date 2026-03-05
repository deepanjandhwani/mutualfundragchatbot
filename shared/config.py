"""Shared configuration for IndMoney RAG Chatbot."""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Phase 1: Source URLs
FUND_URLS = [
    {
        "id": "2989",
        "name": "HDFC Large Cap Fund Direct Plan Growth",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-large-cap-fund-direct-plan-growth-option-2989",
    },
    {
        "id": "3184",
        "name": "HDFC Flexi Cap Fund Direct Plan Growth",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth-option-3184",
    },
    {
        "id": "2685",
        "name": "HDFC ELSS Tax Saver Direct Plan Growth",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-elss-taxsaver-direct-plan-growth-option-2685",
    },
    {
        "id": "1040010",
        "name": "HDFC Nifty Next 50 Index Fund Direct Growth",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-nifty-next-50-index-fund-direct-growth-1040010",
    },
    {
        "id": "3097",
        "name": "HDFC Mid Cap Fund Direct Plan Growth",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-mid-cap-fund-direct-plan-growth-option-3097",
    },
    {
        "id": "9006",
        "name": "HDFC Housing Opportunities Fund Direct Growth",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-housing-opportunities-fund-direct-growth-9006",
    },
    {
        "id": "1047724",
        "name": "HDFC Nifty LargeMidcap 250 Index Fund Direct Growth",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-nifty-largemidcap-250-index-fund-direct-growth-1047724",
    },
    {
        "id": "2874",
        "name": "HDFC Large and Mid Cap Fund Direct Growth",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth-2874",
    },
]

# Paths
PHASE1_OUTPUT = PROJECT_ROOT / "phase1_data_ingestion" / "output"
PHASE2_INPUT = PROJECT_ROOT / "phase2_processing" / "input"
PHASE2_OUTPUT = PROJECT_ROOT / "phase2_processing" / "output" / "chunks"
PHASE3_CHROMA_PATH = PROJECT_ROOT / "phase3_embeddings" / "chroma_db"

# ChromaDB
CHROMA_COLLECTION_NAME = "indmoney_fund_chunks"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # or BAAI/bge-small-en-v1.5

# Phase 6: last refresh timestamp (written by scheduler after successful pipeline run)
LAST_REFRESH_FILE = PROJECT_ROOT / "shared" / "last_refresh.json"
