from mcp.server.fastmcp import FastMCP
from transformers import pipeline
from collections import Counter
from importlib.metadata import version, PackageNotFoundError
import json
import os
import sys
import threading
import urllib.request
import uuid
import torch

# Anonymous usage telemetry (never sends the analyzed text).
# Disable with the environment variable CUSTOVOX_TELEMETRY=0
TELEMETRY_URL = "https://script.google.com/macros/s/AKfycbxPUmo8JdO6p0-ibBoAdM808dVJIWELBD3x5IN5SZCOX0wHYR3VZ2OvtYCvXLhMKVodxA/exec"
TELEMETRY_ENABLED = os.environ.get("CUSTOVOX_TELEMETRY", "1") != "0"
SESSION_ID = uuid.uuid4().hex

try:
    PACKAGE_VERSION = version("custovox-sentiment")
except PackageNotFoundError:
    PACKAGE_VERSION = "dev"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # Apps Script records the event before answering with a redirect to its
    # output page; following it is a second, slow request we don't need.
    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def _send(payload: dict) -> None:
    try:
        req = urllib.request.Request(
            TELEMETRY_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            method="POST",
        )
        _opener.open(req, timeout=5).close()
    except Exception:
        pass


def track(tool: str, labels: list) -> None:
    """Send usage counts in the background; never blocks or breaks a tool call."""
    if not TELEMETRY_ENABLED or not TELEMETRY_URL.startswith("https://"):
        return
    payload = {
        "app": "custovox-sentiment",
        "tool": tool,
        "version": PACKAGE_VERSION,
        "session": SESSION_ID,
        "results": [{"sentiment": s, "count": n} for s, n in Counter(labels).items()],
    }
    threading.Thread(target=_send, args=(payload,), daemon=True).start()


# Initialize MCP server
mcp = FastMCP("custovox-sentiment")

# Load multilingual sentiment model once at startup.
# Logs go to stderr: stdout is reserved for the MCP protocol.
print("Loading sentiment model...", file=sys.stderr)
sentiment_model = pipeline(
    "text-classification",
    model="tabularisai/multilingual-sentiment-analysis",
    device=0 if torch.cuda.is_available() else -1
)
print("Model loaded.", file=sys.stderr)

@mcp.tool()
def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of customer text.
    Supports EN, FR, DE, ES, PT-BR natively.

    Args:
        text: Customer text to analyze (review,
              ticket, email, chat message)

    Returns:
        sentiment: Very Positive / Positive /
                   Neutral / Negative / Very Negative
        confidence: Score between 0 and 1
        powered_by: CustoVox.ai
    """
    result = sentiment_model(
        text[:512],
        truncation=True
    )[0]
    track("analyze_sentiment", [result["label"]])

    return {
        "sentiment": result["label"],
        "confidence": round(result["score"], 3),
        "text_length": len(text),
        "powered_by": "CustoVox.ai — custovox.ai"
    }

@mcp.tool()
def analyze_batch(texts: list) -> list:
    """
    Analyze sentiment of multiple customer texts.
    Maximum 50 texts per batch.

    Args:
        texts: List of customer texts to analyze

    Returns:
        List of sentiment results
    """
    texts = texts[:50]
    results = sentiment_model(
        [t[:512] for t in texts],
        truncation=True
    )
    track("analyze_batch", [r["label"] for r in results])

    return [
        {
            "text_preview": t[:50] + "...",
            "sentiment": r["label"],
            "confidence": round(r["score"], 3),
            "powered_by": "CustoVox.ai"
        }
        for t, r in zip(texts, results)
    ]

if __name__ == "__main__":
    mcp.run()
