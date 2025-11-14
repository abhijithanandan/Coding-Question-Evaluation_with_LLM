from __future__ import annotations
import json
from typing import Any, Dict


def normalize_json_response(raw: Any, provider: str, model: str) -> Dict:
    """Try to normalize various provider outputs into a dict.

    The original repository attempted multiple heuristics. Keep the
    same behaviour here in a single helper.
    """
    # If SDK returned structured tuple/list (score, breakdown) keep it
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        try:
            score = float(raw[0])
            breakdown = str(raw[1])
            return {"score": score, "breakdown": breakdown}
        except Exception:
            return {
                "__parse_error__": True,
                "raw": str(raw)[:500],
                "provider": provider,
                "model": model,
            }

    if isinstance(raw, dict):
        return raw

    # string or other: try json loads
    try:
        return json.loads(raw)
    except Exception:
        s = str(raw)
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start : end + 1])
            except Exception:
                pass
        return {
            "__parse_error__": True,
            "error": "Failed to parse/normalize response",
            "raw": s[:500],
            "provider": provider,
            "model": model,
        }
