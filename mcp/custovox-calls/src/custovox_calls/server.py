"""custovox-calls: MCP server for customer-service call analysis, built on callscope-ai."""

from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable

import callscope
from mcp.server.fastmcp import FastMCP

from . import __version__
from . import actions as actions_mod
from .demo import DEMO_CALLS
from .store import CallStore

DEFAULT_DB = "~/.custovox-calls/calls.db"
MAX_DOWNLOAD = 300 * 1024 * 1024
EXCERPT_SEGMENTS = 12


def _truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


class ToolError(Exception):
    pass


def _download(url: str) -> Path:
    suffix = Path(urllib.parse.urlparse(url).path).suffix or ".audio"
    fd, name = tempfile.mkstemp(prefix="custovox-call-", suffix=suffix)
    total = 0
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "custovox-calls"})
        with urllib.request.urlopen(req, timeout=60) as resp, os.fdopen(fd, "wb") as out:  # noqa: S310
            while chunk := resp.read(1 << 20):
                total += len(chunk)
                if total > MAX_DOWNLOAD:
                    raise ToolError("The audio file is larger than 300 MB.")
                out.write(chunk)
    except urllib.error.URLError as exc:
        Path(name).unlink(missing_ok=True)
        raise ToolError(f"Cannot download the audio: {exc.reason}") from exc
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise
    return Path(name)


def _load_segments(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    segs = data.get("segments") if isinstance(data, dict) else data
    if not isinstance(segs, list) or not all(isinstance(s, dict) and "text" in s and "start" in s and "end" in s
                                             for s in segs):
        raise ToolError("The JSON file must be a list of segments {start, end, text} (or {\"segments\": [...]}).")
    return segs


def run_analysis(source: str, language: str | None, model_size: str) -> tuple[dict, str | None]:
    """Return (callscope analysis, default started_at)."""
    if source in DEMO_CALLS:
        started, segs = DEMO_CALLS[source]
        result = callscope.analyze(segs)
        result["source"] = source
        return result, started
    if source.startswith(("http://", "https://")):
        tmp = _download(source)
        try:
            result = _analyze_audio(tmp, language, model_size)
        finally:
            tmp.unlink(missing_ok=True)
        result["source"] = source
        return result, None
    path = Path(source).expanduser()
    if not path.is_file():
        raise ToolError(f"File not found: {source}")
    if path.suffix.lower() == ".json":
        result = callscope.analyze(_load_segments(path))
        result["source"] = str(path)
        return result, None
    return _analyze_audio(path, language, model_size), None


def _analyze_audio(path: Path, language: str | None, model_size: str) -> dict:
    try:
        return callscope.analyze(str(path), language=language, model_size=model_size)
    except ImportError as exc:
        raise ToolError("Audio transcription needs the whisper extra: pip install 'custovox-calls[whisper]'. "
                        "Or pass a JSON file of transcript segments.") from exc


def _compact(call_id: str, started_at: str, a: dict, n_actions: int) -> dict:
    s = a.get("sentiment", {})
    segs = a.get("segments", [])
    return {
        "call_id": call_id,
        "started_at": started_at,
        "duration_seconds": a.get("duration"),
        "customer_sentiment": {"mean": s.get("customer_mean"), "trend": s.get("customer_trend")},
        "contact_reasons": [r["reason"] for r in a.get("contact_reasons", [])],
        "key_moments": [{"type": m["type"], "at": m["start"], "speaker": m.get("speaker"), "text": m["text"]}
                        for m in a.get("key_moments", [])],
        "suggested_actions": n_actions,
        "transcript_excerpt": [{"at": x["start"], "speaker": x.get("speaker"), "text": x["text"]}
                               for x in segs[:EXCERPT_SEGMENTS]],
        "transcript_segments": len(segs),
    }


def build_server(store: CallStore, webhook_url: str | None = None, model_size: str = "small",
                 sender: Callable[..., int] = actions_mod.send_webhook) -> FastMCP:
    mcp = FastMCP("custovox-calls")
    mcp._mcp_server.version = __version__  # serverInfo.version (FastMCP would report the mcp library version)

    @mcp.tool()
    def analyze_call(source: str, call_id: str | None = None, started_at: str | None = None,
                     language: str | None = None) -> dict:
        """Analyze one customer-service call and save the result in the local database.

        source: a local audio file, an http(s) URL to an audio file, a local JSON file of transcript
        segments [{start, end, text}], or a demo call id (demo-1 ... demo-6).
        started_at: ISO date-time of the call (default: now). language: e.g. "fr" or "en" (audio only).
        Returns sentiment, contact reasons, key moments (complaint, churn threat, agent promise) and a
        transcript excerpt. Runs locally: audio is transcribed on this machine."""
        try:
            if started_at:
                datetime.fromisoformat(started_at)
            analysis, default_start = run_analysis(source, language, model_size)
        except (ToolError, ValueError) as exc:
            return {"error": str(exc)}
        cid = call_id or (source if source in DEMO_CALLS else uuid.uuid4().hex[:10])
        start = started_at or default_start or datetime.now().isoformat(timespec="seconds")
        store.save(cid, start, analysis)
        return _compact(cid, start, analysis, len(actions_mod.suggest(cid, analysis)))

    @mcp.tool()
    def get_call_insights(since: str | None = None, until: str | None = None) -> dict:
        """Summary of the analyzed calls over a period: number of calls, minutes, mean customer
        sentiment, contact reasons, key moments, churn threats and the most negative calls.
        since / until: ISO dates, e.g. "2026-11-01" (until is exclusive). Read-only."""
        return store.insights(since, until)

    @mcp.tool()
    def search_feedback(query: str, speaker: str | None = "customer", since: str | None = None,
                        until: str | None = None, limit: int = 20) -> dict:
        """Search what was said in the analyzed calls. All words must appear in the same sentence;
        case and accents are ignored. speaker: "customer" (default), "agent", or null for both.
        Returns the matching sentences with their call id and time. Read-only."""
        if speaker not in (None, "", "customer", "agent"):
            return {"error": 'speaker must be "customer", "agent" or null.'}
        hits = store.search(query, speaker or None, since, until, max(1, min(limit, 100)))
        return {"query": query, "count": len(hits), "results": hits}

    @mcp.tool()
    def suggest_actions(call_id: str) -> dict:
        """Suggest follow-up actions for an analyzed call: manager alert (churn threat or complaint),
        customer callback (to check an agent promise is kept), CRM ticket (negative sentiment).
        Each action has a priority, a reason and the sentence that triggered it. Sends nothing."""
        call = store.get(call_id)
        if call is None:
            return {"error": f"No analyzed call with id {call_id}. Run analyze_call first."}
        acts = actions_mod.suggest(call_id, call["analysis"])
        return {"call_id": call_id, "actions": acts,
                "can_send": bool(webhook_url),
                "message": None if acts else "No follow-up needed for this call."}

    if webhook_url:

        @mcp.tool()
        def send_action(action_id: str) -> dict:
            """SENDS DATA. Post one suggested action (id from suggest_actions, e.g. "abc123#1") to the
            webhook configured by the user (CUSTOVOX_CALLS_WEBHOOK_URL: Slack, Zapier, Make, a CRM...).
            The payload includes the sentence that triggered the action. Ask the user before sending."""
            call_id, _, _ = action_id.rpartition("#")
            call = store.get(call_id)
            if call is None:
                return {"error": f"Unknown action id {action_id}."}
            action = next((a for a in actions_mod.suggest(call_id, call["analysis"]) if a["id"] == action_id), None)
            if action is None:
                return {"error": f"Unknown action id {action_id}."}
            try:
                status = sender(webhook_url, {"id": call_id, "started_at": call["started_at"]}, action)
            except (urllib.error.URLError, OSError) as exc:
                return {"error": f"Webhook failed: {getattr(exc, 'reason', exc)}"}
            return {"sent": 200 <= status < 300, "status": status, "action_id": action_id}

    return mcp


def create_app(env: dict[str, str] | None = None) -> FastMCP:
    env = dict(os.environ) if env is None else env
    if _truthy(env.get("CUSTOVOX_CALLS_DEMO")):
        store = CallStore(":memory:")
        for cid, (started, segs) in DEMO_CALLS.items():
            a = callscope.analyze(segs)
            a["source"] = cid
            store.save(cid, started, a)
    else:
        store = CallStore(env.get("CUSTOVOX_CALLS_DB") or DEFAULT_DB)
    return build_server(store, webhook_url=env.get("CUSTOVOX_CALLS_WEBHOOK_URL") or None,
                        model_size=env.get("CUSTOVOX_CALLS_WHISPER_MODEL") or "small")


def main() -> None:
    create_app().run()


if __name__ == "__main__":
    main()

