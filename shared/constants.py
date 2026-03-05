"""Constants for IndMoney RAG Chatbot."""

import re

# PII patterns - block these in user input and chunk content
PII_PATTERNS = [
    re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),  # PAN
    re.compile(r"\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b"),  # Aadhaar (simplified)
    re.compile(r"\b\d{9,18}\b"),  # Account numbers (generic)
    re.compile(r"\b\d{4,6}\b"),  # OTP-like sequences
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # Email
    re.compile(r"\b(?:\+91[- ]?)?[6-9]\d{9}\b"),  # Indian phone
]

# Refusal messages
REFUSAL_PII = "We don't accept or store personal identifiers (PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers)."
REFUSAL_OPINION = (
    "We only provide factual information. For investment decisions, please consult a SEBI-registered advisor. "
    "Learn more: https://www.sebi.gov.in/investor/frequently-asked-questions.html"
)
REFUSAL_COMPARE = (
    "We don't compute or compare returns. Please check the fund page directly for performance data."
)

# Educational link for refused opinionated queries
EDUCATIONAL_LINK = "https://www.sebi.gov.in/investor/frequently-asked-questions.html"

# Opinionated query patterns (to refuse)
OPINION_PATTERNS = [
    r"should\s+i\s+(buy|sell|invest)",
    r"(buy|sell|invest)\s+(in|into)\s+",
    r"is\s+it\s+(good|bad)\s+to",
    r"recommend",
    r"advice",
    r"opinion\s+on",
    r"what\s+do\s+you\s+think",
]

# Comparison/compute patterns (to refuse)
COMPARE_PATTERNS = [
    r"compare\s+(returns?|performance)",
    r"which\s+(fund|one)\s+(is\s+)?better",
    r"calculate\s+(returns?|performance)",
    r"compute\s+(returns?|performance)",
]
