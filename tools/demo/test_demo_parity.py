"""The /demo page (demo-engine.js) must give the same result as the Python packages.

Reference = callscope-ai's analyze() + custovox-calls' actions.suggest(), applied to each text
as a customer segment. Needs node on PATH. Run: python -m pytest tools/demo
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mcp" / "callscope-ai" / "src"))
sys.path.insert(0, str(ROOT / "mcp" / "custovox-calls" / "src"))
from callscope import analyze  # noqa: E402
from custovox_calls.actions import suggest  # noqa: E402

from fixtures import ALL_TEXTS  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def run_js(texts):
    code = ("const e=require(process.argv[1]);let d='';process.stdin.on('data',c=>d+=c)"
            ".on('end',()=>process.stdout.write(JSON.stringify(e.report(JSON.parse(d)))));")
    out = subprocess.run(["node", "-e", code, str(ROOT / "demo-engine.js")], input=json.dumps(texts),
                         capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(out.stdout)


def py_one(text):
    a = analyze([{"start": 0.0, "end": 1.0, "text": text, "speaker": "customer"}])
    return a, round(a["sentiment"]["customer_mean"], 2)


def test_engine_is_up_to_date():
    from callscope import __version__
    assert f"callscope-ai {__version__}" in (ROOT / "demo-engine.js").read_text(encoding="utf-8")


def test_per_text_parity():
    js = run_js(ALL_TEXTS)
    for j, text in zip(js["per"], ALL_TEXTS):
        a, score = py_one(text)
        assert j["score"] == score, text
        assert [r["reason"] for r in j["reasons"]] == [r["reason"] for r in a["contact_reasons"]], text
        assert [m["type"] for m in j["moments"]] == [m["type"] for m in a["key_moments"]], text
        py_actions = [(x["type"], x["priority"]) for x in suggest("t", a)]
        assert py_actions == [(x["type"], x["priority"]) for x in j["actions"]], text


def test_report_shape_and_limits():
    r = run_js(ALL_TEXTS[:8])
    assert r["count"] == 8 and sum(r["labels"].values()) == 8
    assert len(r["actions"]) <= 3 and len({a["index"] for a in r["actions"]}) == len(r["actions"])
