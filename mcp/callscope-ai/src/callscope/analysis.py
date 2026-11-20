"""Sentiment, contact reasons, key moments and the one-shot ``analyze``."""

from __future__ import annotations

import re

from .diarize import diarize
from .lexicon import MOMENTS, NEGATIVE, NEGATORS, POSITIVE, REASONS

SCHEMA = "callscope/1"
_WORD = re.compile(r"[\w'’-]+", re.UNICODE)


def _words(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text)]


def _score(text: str) -> float:
    words = _words(text)
    score = 0
    for i, w in enumerate(words):
        sign = 1 if w in POSITIVE else -1 if w in NEGATIVE else 0
        if sign and any(p in NEGATORS for p in words[max(0, i - 2):i]):
            sign = -sign
        score += sign
    return max(-1.0, min(1.0, score / 3))


def _has(text: str, keyword: str) -> bool:
    """Whole-word match, so 'down' does not match 'downgrade' nor 'bug' 'debug'."""
    return re.search(r"(?<![\w])" + re.escape(keyword) + r"(?![\w])", text) is not None


def _label(score: float) -> str:
    return "positive" if score > 0.15 else "negative" if score < -0.15 else "neutral"


def sentiment(segments: list[dict]) -> dict:
    """Sentiment per segment (-1..1) plus the customer's curve over the call."""
    per = [{"index": i, "start": s["start"], "speaker": s.get("speaker"), "score": round(_score(s["text"]), 2),
            "label": _label(_score(s["text"]))} for i, s in enumerate(segments)]
    cust = [p for p in per if p["speaker"] == "customer"] or per
    curve = [{"start": p["start"], "score": p["score"]} for p in cust]
    mean = round(sum(p["score"] for p in cust) / len(cust), 2) if cust else 0.0
    half = len(cust) // 2
    trend = 0.0
    if half:
        trend = round(sum(p["score"] for p in cust[half:]) / (len(cust) - half) - sum(p["score"] for p in cust[:half]) / half, 2)
    return {"segments": per, "customer_curve": curve, "customer_mean": mean, "customer_trend": trend}


def contact_reasons(segments: list[dict]) -> list[dict]:
    """Ranked contact reasons, from the customer's words (all speakers if unlabelled)."""
    cust = [s for s in segments if s.get("speaker") == "customer"] or segments
    text = " ".join(s["text"].lower() for s in cust)
    found = []
    for reason, kws in REASONS.items():
        hits = sorted({k for k in kws if _has(text, k)})
        if hits:
            found.append({"reason": reason, "matches": hits, "score": len(hits)})
    return sorted(found, key=lambda r: (-r["score"], r["reason"]))


def key_moments(segments: list[dict]) -> list[dict]:
    """Complaints and churn threats (customer), promises (agent)."""
    owner = {"complaint": "customer", "churn_threat": "customer", "agent_promise": "agent"}
    out = []
    for i, s in enumerate(segments):
        low = s["text"].lower()
        for kind, kws in MOMENTS.items():
            if s.get("speaker") not in (None, owner[kind]):
                continue
            hit = next((k for k in kws if _has(low, k)), None)
            if hit:
                out.append({"type": kind, "segment": i, "start": s["start"], "speaker": s.get("speaker"),
                            "text": s["text"], "match": hit})
    return out


def analyze(source, **transcribe_options) -> dict:
    """Run everything. ``source`` is an audio path or a list of segments.

    The returned dict is the common callscope format (``schema`` = ``callscope/1``).
    """
    if isinstance(source, str) or hasattr(source, "__fspath__"):
        from .transcribe import transcribe
        segments = transcribe(str(source), **transcribe_options)
        origin = str(source)
    else:
        segments, origin = list(source), None
    segments = diarize(segments)
    return {
        "schema": SCHEMA,
        "source": origin,
        "duration": max((s["end"] for s in segments), default=0.0),
        "segments": segments,
        "sentiment": sentiment(segments),
        "contact_reasons": contact_reasons(segments),
        "key_moments": key_moments(segments),
    }
