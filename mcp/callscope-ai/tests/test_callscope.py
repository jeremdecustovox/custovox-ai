import json

import pytest

import callscope
from callscope import analyze, contact_reasons, diarize, key_moments, sentiment
from callscope.cli import main
from callscope.demo import DEMO_SEGMENTS


def test_diarize_alternates_and_agent_first():
    out = diarize(DEMO_SEGMENTS)
    assert [s["speaker"] for s in out] == ["agent", "customer", "agent", "customer", "agent", "customer"]
    assert "speaker" not in DEMO_SEGMENTS[0]  # input not mutated


def test_diarize_uses_channels_and_existing_labels():
    segs = [{"start": 0, "end": 1, "text": "x", "channel": 1}, {"start": 1, "end": 2, "text": "y", "channel": 0},
            {"start": 2, "end": 3, "text": "z", "speaker": "agent"}]
    out = diarize(segs, channel_roles={0: "agent", 1: "customer"})
    assert [s["speaker"] for s in out] == ["customer", "agent", "agent"]


def test_sentiment_curve_and_negation():
    segs = diarize(DEMO_SEGMENTS)
    s = sentiment(segs)
    assert s["customer_curve"][0]["score"] < 0
    assert s["customer_curve"][-1]["score"] > 0
    assert s["customer_trend"] > 0
    neg = sentiment([{"start": 0, "end": 1, "text": "ce n'est pas bien", "speaker": "customer"}])
    assert neg["segments"][0]["score"] < 0


def test_contact_reasons():
    reasons = contact_reasons(diarize(DEMO_SEGMENTS))
    assert reasons[0]["reason"] in {"billing", "cancellation"}
    assert {r["reason"] for r in reasons} >= {"billing", "cancellation"}
    assert contact_reasons([{"start": 0, "end": 1, "text": "bonjour"}]) == []


def test_key_moments_ownership():
    moments = key_moments(diarize(DEMO_SEGMENTS))
    kinds = {(m["type"], m["speaker"]) for m in moments}
    assert ("complaint", "customer") in kinds and ("churn_threat", "customer") in kinds
    assert ("agent_promise", "agent") in kinds


def test_analyze_common_format_is_json_serialisable():
    r = analyze(DEMO_SEGMENTS)
    assert r["schema"] == callscope.SCHEMA == "callscope/1"
    assert set(r) == {"schema", "source", "duration", "segments", "sentiment", "contact_reasons", "key_moments"}
    assert r["duration"] == 36.0
    json.dumps(r)


def test_analyze_empty():
    r = analyze([])
    assert r["duration"] == 0.0 and r["key_moments"] == []


def test_transcribe_without_dependency_is_clear(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    with pytest.raises(ImportError, match=r"callscope-ai\[whisper\]"):
        callscope.transcribe("x.wav")


def test_cli_demo_and_json(capsys, tmp_path):
    assert main(["demo"]) == 0
    assert json.loads(capsys.readouterr().out)["schema"] == "callscope/1"
    f = tmp_path / "c.json"
    f.write_text(json.dumps(DEMO_SEGMENTS))
    assert main(["analyze", str(f)]) == 0
    assert json.loads(capsys.readouterr().out)["contact_reasons"]


def test_keywords_match_whole_words_only():
    from callscope import contact_reasons
    seg = [{"start": 0, "end": 1, "text": "I want to downgrade, can you explain? I debug code."}]
    reasons = {r["reason"]: r["matches"] for r in contact_reasons(seg)}
    assert "outage" not in reasons and "technical_support" not in reasons
    assert reasons["subscription_change"] == ["downgrade"]


def test_foreign_speaker_labels_do_not_crash():
    from callscope import diarize
    out = diarize([{"start": 0, "end": 1, "text": "Bonjour, comment puis-je vous aider ?", "speaker": "SPEAKER_00"},
                   {"start": 2, "end": 3, "text": "J'ai un souci", "speaker": "SPEAKER_01"}])
    assert [s["speaker"] for s in out] == ["agent", "customer"]
    assert out[0]["original_speaker"] == "SPEAKER_00"


def _one(text):
    from callscope import analyze
    return analyze([{"start": 0, "end": 1, "text": text, "speaker": "customer"}])


def test_review_reasons_fr_en():
    a = _one("Chambre crasseuse et personnel impoli, je ne reviendrai plus.")
    assert {r["reason"] for r in a["contact_reasons"]} >= {"cleanliness", "staff"}
    assert [m["type"] for m in a["key_moments"]] == ["churn_threat"]
    assert a["sentiment"]["customer_mean"] < 0
    b = _one("Waited 40 minutes, the staff was rude. Never again.")
    assert {r["reason"] for r in b["contact_reasons"]} >= {"waiting_time", "staff"}
    assert _one("Lovely hotel, clean and friendly staff.")["sentiment"]["customer_mean"] > 0


def test_review_words_avoid_common_false_positives():
    a = _one("Can't wait to come back, great sale this weekend.")
    assert a["contact_reasons"] == [] and a["key_moments"] == []
