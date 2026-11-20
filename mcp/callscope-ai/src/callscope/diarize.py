"""Who speaks when: ``agent`` or ``customer``.

Heuristic and fully local. Priority: an existing ``speaker``/``channel`` field
on the segment, then turn-taking on silence gaps with opening-phrase cues.
"""

from __future__ import annotations

import re

AGENT_CUES = re.compile(
    r"(vous parlez à|comment puis-je|puis-je vous aider|je vais (vérifier|regarder|noter)|"
    r"how can i help|you('re| are) speaking with|let me (check|look))",
    re.I,
)
ROLES = ("agent", "customer")


def diarize(segments: list[dict], channel_roles: dict[int, str] | None = None, gap: float = 0.4) -> list[dict]:
    """Return new segments with a ``speaker`` of ``agent`` or ``customer``.

    ``channel_roles`` maps a stereo channel number to a role, e.g. ``{0: "agent", 1: "customer"}``.
    """
    out = [dict(s) for s in segments]
    for s in out:
        # Labels from other tools (e.g. "SPEAKER_00") are not roles: guess them.
        if "speaker" in s and s["speaker"] not in ROLES:
            s["original_speaker"] = s.pop("speaker")
        if s.get("speaker") in ROLES:
            continue
        if channel_roles and s.get("channel") in channel_roles:
            s["speaker"] = channel_roles[s["channel"]]
    current = 0  # index into ROLES for the running turn
    first = next((s for s in out if "speaker" not in s), None)
    if first is not None and AGENT_CUES.search(first["text"]):
        current = 0
    elif first is not None:
        current = 1
    prev_end = None
    for s in out:
        if "speaker" in s:
            current = ROLES.index(s["speaker"])
            prev_end = s["end"]
            continue
        if prev_end is not None and s["start"] - prev_end >= gap and not AGENT_CUES.search(s["text"]):
            current = 1 - current
        elif AGENT_CUES.search(s["text"]):
            current = 0
        s["speaker"] = ROLES[current]
        prev_end = s["end"]
    return out
