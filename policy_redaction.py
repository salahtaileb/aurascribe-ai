import re
from typing import Tuple, Dict, Any, List
import uuid

_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9.\-+_]+@[a-zA-Z0-9.\-+_]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"(?:(?:\+?\d{1,3})?[\s\-\.])?(?:\(?\d{3}\)?[\s\-\.]?)?\d{3}[\s\-\.]?\d{4}"),
    "mrn": re.compile(r"\b(?:MRN|Dossier|#)\s*[:#]?\s*\w+\b", re.IGNORECASE),
    "date": re.compile(r"\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"),
}

def redact_text(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    redaction_log = []
    redacted = text
    # Process sequentially to preserve offsets - simple approach for MVP
    offset_delta = 0
    for category, pattern in _PATTERNS.items():
        for m in list(pattern.finditer(text)):
            start, end = m.span()
            placeholder = f"[REDACTED_{category.upper()}]"
            token_hash = uuid.uuid5(uuid.NAMESPACE_URL, f"{category}:{m.group(0)}").hex
            # apply placeholder on redacted string considering previous deltas
            adj_start = start + offset_delta
            adj_end = end + offset_delta
            redacted = redacted[:adj_start] + placeholder + redacted[adj_end:]
            delta = len(placeholder) - (end - start)
            offset_delta += delta
            redaction_log.append({"id": token_hash, "category": category, "start": start, "length": end-start, "placeholder": placeholder})
    return redacted, redaction_log

def policy_check_and_redact(transcript: str, language: str = "fr") -> Dict[str, Any]:
    redacted, log = redact_text(transcript)
    flags = []
    lower = transcript.lower()
    if any(k in lower for k in ["agression sexuelle","viol","abuse","rape","sexual assault","child abuse"]):
        flags.append("potentielle_declaration_obligatoire")
    return {"redacted_transcript": redacted, "redaction_log": log, "flags": flags}