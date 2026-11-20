"""Local SQLite store of analyzed calls. Nothing leaves the machine."""

from __future__ import annotations

import json
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS calls (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    source TEXT,
    duration REAL,
    customer_mean REAL,
    customer_trend REAL,
    analysis TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS segments (
    call_id TEXT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    start REAL,
    speaker TEXT,
    text TEXT,
    text_norm TEXT
);
CREATE INDEX IF NOT EXISTS calls_started ON calls(started_at);
"""


def normalize(text: str) -> str:
    """Lowercase without accents, so 'résilier' matches 'resilier'."""
    nfkd = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class CallStore:
    def __init__(self, path: str | Path = ":memory:") -> None:
        if path != ":memory:":
            Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
            path = str(Path(path).expanduser())
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA_SQL)

    def save(self, call_id: str, started_at: str, analysis: dict) -> None:
        s = analysis.get("sentiment", {})
        with self.db:
            self.db.execute("DELETE FROM calls WHERE id = ?", (call_id,))
            self.db.execute(
                "INSERT INTO calls VALUES (?, ?, ?, ?, ?, ?, ?)",
                (call_id, started_at, analysis.get("source"), analysis.get("duration"),
                 s.get("customer_mean"), s.get("customer_trend"), json.dumps(analysis, ensure_ascii=False)),
            )
            self.db.executemany(
                "INSERT INTO segments VALUES (?, ?, ?, ?, ?, ?)",
                [(call_id, i, seg.get("start"), seg.get("speaker"), seg.get("text", ""), normalize(seg.get("text", "")))
                 for i, seg in enumerate(analysis.get("segments", []))],
            )

    def get(self, call_id: str) -> dict | None:
        row = self.db.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "started_at": row["started_at"], "analysis": json.loads(row["analysis"])}

    def _calls(self, since: str | None, until: str | None) -> list[sqlite3.Row]:
        sql, args = "SELECT * FROM calls WHERE 1=1", []
        if since:
            sql += " AND started_at >= ?"
            args.append(since)
        if until:
            sql += " AND started_at < ?"
            args.append(until)
        return self.db.execute(sql + " ORDER BY started_at", args).fetchall()

    def insights(self, since: str | None = None, until: str | None = None) -> dict:
        rows = self._calls(since, until)
        reasons: Counter = Counter()
        moments: Counter = Counter()
        churn = []
        for r in rows:
            a = json.loads(r["analysis"])
            reasons.update(x["reason"] for x in a.get("contact_reasons", []))
            for m in a.get("key_moments", []):
                moments[m["type"]] += 1
                if m["type"] == "churn_threat":
                    churn.append({"call_id": r["id"], "started_at": r["started_at"], "text": m["text"]})
        means = [r["customer_mean"] for r in rows if r["customer_mean"] is not None]
        worst = sorted((r for r in rows if r["customer_mean"] is not None), key=lambda r: r["customer_mean"])[:5]
        return {
            "period": {"since": since, "until": until},
            "calls": len(rows),
            "total_minutes": round(sum(r["duration"] or 0 for r in rows) / 60, 1),
            "customer_sentiment_mean": round(sum(means) / len(means), 2) if means else None,
            "contact_reasons": [{"reason": k, "calls": v} for k, v in reasons.most_common()],
            "key_moments": dict(moments),
            "churn_threats": churn[:20],
            "most_negative_calls": [{"call_id": r["id"], "started_at": r["started_at"],
                                     "customer_mean": r["customer_mean"]} for r in worst],
        }

    def search(self, query: str, speaker: str | None = "customer", since: str | None = None,
               until: str | None = None, limit: int = 20) -> list[dict]:
        words = normalize(query).split()
        if not words:
            return []
        sql = ("SELECT s.call_id, c.started_at, s.idx, s.start, s.speaker, s.text FROM segments s "
               "JOIN calls c ON c.id = s.call_id WHERE 1=1")
        args: list = []
        for w in words:
            sql += " AND s.text_norm LIKE ? ESCAPE '\\'"
            args.append("%" + w.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
        if speaker:
            sql += " AND s.speaker = ?"
            args.append(speaker)
        if since:
            sql += " AND c.started_at >= ?"
            args.append(since)
        if until:
            sql += " AND c.started_at < ?"
            args.append(until)
        sql += " ORDER BY c.started_at DESC, s.idx LIMIT ?"
        args.append(limit)
        return [dict(r) for r in self.db.execute(sql, args).fetchall()]
