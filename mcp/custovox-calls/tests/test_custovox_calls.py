import asyncio
import json

import pytest

from custovox_calls import actions as actions_mod
from custovox_calls import server as server_mod
from custovox_calls.server import build_server, create_app
from custovox_calls.store import CallStore, normalize


def call(srv, name, **args):
    res = asyncio.run(srv.call_tool(name, args))
    if isinstance(res, tuple):
        return res[1].get("result", res[1])
    return json.loads(res[0].text)


def tools(srv):
    return {t.name for t in asyncio.run(srv.list_tools())}


SEGMENTS = [
    {"start": 0, "end": 3, "text": "Bonjour, vous parlez à Léa, comment puis-je vous aider ?"},
    {"start": 4, "end": 9, "text": "Ma facture est fausse, c'est inadmissible, je vais résilier."},
    {"start": 10, "end": 14, "text": "Je vais vérifier. Je vous rappelle avant demain."},
]


@pytest.fixture
def seg_file(tmp_path):
    p = tmp_path / "call.json"
    p.write_text(json.dumps(SEGMENTS, ensure_ascii=False), encoding="utf-8")
    return p


def test_default_tools_send_nothing():
    assert tools(build_server(CallStore())) == {
        "analyze_call", "get_call_insights", "search_feedback", "suggest_actions"}
    assert "send_action" in tools(build_server(CallStore(), webhook_url="https://hook.test"))


def test_analyze_json_segments_and_store(seg_file):
    store = CallStore()
    out = call(build_server(store), "analyze_call", source=str(seg_file), call_id="c1",
               started_at="2026-11-10T10:00:00")
    assert out["call_id"] == "c1" and "billing" in out["contact_reasons"]
    types = {m["type"] for m in out["key_moments"]}
    assert {"complaint", "churn_threat", "agent_promise"} <= types
    assert out["suggested_actions"] >= 3
    assert store.get("c1")["started_at"] == "2026-11-10T10:00:00"


def test_analyze_errors_are_clear(tmp_path):
    srv = build_server(CallStore())
    assert "not found" in call(srv, "analyze_call", source=str(tmp_path / "nope.wav"))["error"]
    bad = tmp_path / "bad.json"
    bad.write_text('{"foo": 1}', encoding="utf-8")
    assert "segments" in call(srv, "analyze_call", source=str(bad))["error"]
    assert "error" in call(srv, "analyze_call", source="demo-1", started_at="yesterday")


def test_audio_without_whisper_explains(tmp_path, monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"RIFF")
    out = call(build_server(CallStore()), "analyze_call", source=str(wav))
    assert "custovox-calls[whisper]" in out["error"]


def test_url_is_downloaded_then_removed(monkeypatch):
    seen = {}

    def fake_download(url):
        import os, tempfile, pathlib
        fd, name = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        p = pathlib.Path(name)
        seen["path"] = p
        return p

    monkeypatch.setattr(server_mod, "_download", fake_download)
    monkeypatch.setattr(server_mod, "_analyze_audio", lambda p, l, m: server_mod.callscope.analyze(SEGMENTS))
    out = call(build_server(CallStore()), "analyze_call", source="https://example.test/call.wav")
    assert "error" not in out and not seen["path"].exists()


def test_insights_period_filter():
    srv = create_app({"CUSTOVOX_CALLS_DEMO": "1"})
    all_ = call(srv, "get_call_insights")
    assert all_["calls"] == 6
    reasons = {r["reason"] for r in all_["contact_reasons"]}
    assert {"billing", "outage", "delivery", "cancellation"} <= reasons
    assert {c["call_id"] for c in all_["churn_threats"]} >= {"demo-1", "demo-5"}
    early = call(srv, "get_call_insights", since="2026-11-01", until="2026-11-06")
    assert early["calls"] == 3


def test_search_ignores_accents_and_case():
    srv = create_app({"CUSTOVOX_CALLS_DEMO": "1"})
    out = call(srv, "search_feedback", query="RESILIER")
    assert out["count"] >= 2 and all(r["speaker"] == "customer" for r in out["results"])
    assert call(srv, "search_feedback", query="100% _x")["count"] == 0
    assert "error" in call(srv, "search_feedback", query="x", speaker="boss")
    assert normalize("Résilié") == "resilie"


def test_suggest_actions_rules():
    srv = create_app({"CUSTOVOX_CALLS_DEMO": "1"})
    acts = call(srv, "suggest_actions", call_id="demo-1")["actions"]
    kinds = [a["type"] for a in acts]
    assert kinds.count("manager_alert") == 1 and "customer_callback" in kinds and "crm_ticket" in kinds
    alert = next(a for a in acts if a["type"] == "manager_alert")
    assert alert["priority"] == "high" and "résilier" in alert["evidence"]
    assert call(srv, "suggest_actions", call_id="demo-4")["actions"] == []
    assert "error" in call(srv, "suggest_actions", call_id="nope")


def test_send_action_uses_webhook_without_network():
    sent = []
    store = CallStore()
    srv = build_server(store, webhook_url="https://hook.test/x",
                       sender=lambda url, c, a: sent.append((url, c, a)) or 200)
    call(srv, "analyze_call", source="demo-1")
    out = call(srv, "send_action", action_id="demo-1#1")
    assert out["sent"] is True and sent[0][0] == "https://hook.test/x"
    assert sent[0][2]["id"] == "demo-1#1"
    assert "error" in call(srv, "send_action", action_id="demo-1#99")


def test_webhook_payload_has_slack_text(monkeypatch):
    captured = {}

    class Resp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout):
        captured["body"] = json.loads(req.data)
        return Resp()

    monkeypatch.setattr(actions_mod.urllib.request, "urlopen", fake_urlopen)
    action = {"id": "c#1", "type": "manager_alert", "priority": "high", "reason": "r", "evidence": "e", "at": 1}
    assert actions_mod.send_webhook("https://hook.test", {"id": "c"}, action) == 200
    assert captured["body"]["text"].startswith("[high] manager_alert") and captured["body"]["action"] == action


def test_database_file_persists(tmp_path):
    db = tmp_path / "sub" / "calls.db"
    srv = create_app({"CUSTOVOX_CALLS_DB": str(db)})
    call(srv, "analyze_call", source="demo-2")
    again = create_app({"CUSTOVOX_CALLS_DB": str(db)})
    assert call(again, "get_call_insights")["calls"] == 1
