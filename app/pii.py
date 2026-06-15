from __future__ import annotations

import hashlib
import re
from typing import Any


PII_PATTERNS: dict[str, str] = {
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "phone_vn": r"(?:\+84|0)[ \.-]?\d{3}[ \.-]?\d{3}[ \.-]?\d{3,4}",
    "cccd": r"\b\d{12}\b",
    "cmnd": r"\b\d{9}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "openai_key": r"sk-[A-Za-z0-9_-]{20,}",
    "google_key": r"AIza[0-9A-Za-z\-_]{20,}",
    "jwt": r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
}


def scrub_text(text: str) -> str:
    safe = text

    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(
            pattern,
            f"[REDACTED_{name.upper()}]",
            safe,
        )

    safe = re.sub(
        r"(?i)passport[:\s]*[A-Z0-9-]{5,20}",
        "[REDACTED_PASSPORT]",
        safe,
    )

    safe = re.sub(
        r"(?i)\b(?:số nhà|ngõ|ngách|hẻm|phố|đường|phường|xã|quận|huyện|tỉnh|thành phố|tp\.)[^,\n]{0,80}",
        "[REDACTED_ADDRESS]",
        safe,
    )

    return safe


def scrub_value(value: Any) -> Any:
    if isinstance(value, str):
        return scrub_text(value)

    if isinstance(value, dict):
        return {k: scrub_value(v) for k, v in value.items()}

    if isinstance(value, list):
        return [scrub_value(v) for v in value]

    if isinstance(value, tuple):
        return tuple(scrub_value(v) for v in value)

    return value


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]