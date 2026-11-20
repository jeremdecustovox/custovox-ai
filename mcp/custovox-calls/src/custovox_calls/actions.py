"""Follow-up actions derived from a callscope analysis, and optional webhook delivery."""

from __future__ import annotations

import json
import urllib.request

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def suggest(call_id: str, analysis: dict) -> list[dict]:
    """Rule-based suggestions. Every action carries the reason and the words that triggered it."""
    actions: list[dict] = []
    moments = analysis.get("key_moments", [])
    sentiment = analysis.get("sentiment", {})
    reasons = [r["reason"] for r in analysis.get("contact_reasons", [])]
    mean = sentiment.get("customer_mean") or 0.0

    for m in moments:
        if m["type"] == "churn_threat":
            actions.append({"type": "manager_alert", "priority": "high",
                            "reason": "The customer mentioned leaving.", "evidence": m["text"], "at": m["start"]})
        elif m["type"] == "complaint":
            actions.append({"type": "manager_alert", "priority": "medium",
                            "reason": "The customer complained.", "evidence": m["text"], "at": m["start"]})
        elif m["type"] == "agent_promise":
            actions.append({"type": "customer_callback", "priority": "medium",
                            "reason": "The agent made a promise: check it is kept.", "evidence": m["text"], "at": m["start"]})

    if mean < -0.15 or any(m["type"] == "complaint" for m in moments):
        actions.append({"type": "crm_ticket", "priority": "high" if mean < -0.4 else "medium",
                        "reason": f"Negative customer sentiment ({mean:+.2f})"
                                  + (f" about {', '.join(reasons)}" if reasons else "") + ".",
                        "evidence": None, "at": None})

    # One manager alert is enough: keep the most urgent one.
    alerts = sorted((a for a in actions if a["type"] == "manager_alert"), key=lambda a: PRIORITY_ORDER[a["priority"]])
    actions = [a for a in actions if a["type"] != "manager_alert"] + alerts[:1]
    actions.sort(key=lambda a: PRIORITY_ORDER[a["priority"]])
    for i, a in enumerate(actions, 1):
        a["id"] = f"{call_id}#{i}"
    return actions


def send_webhook(url: str, call: dict, action: dict, timeout: float = 10.0) -> int:
    """POST the action as JSON. A `text` field is included so Slack incoming webhooks display it."""
    text = f"[{action['priority']}] {action['type']} for call {call['id']}: {action['reason']}"
    if action.get("evidence"):
        text += f' "{action["evidence"]}"'
    body = json.dumps({"text": text, "source": "custovox-calls", "call": call, "action": action},
                      ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "custovox-calls"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - URL set by the user
        return resp.status
