"""Timestamped transcription with faster-whisper (optional dependency)."""

from __future__ import annotations


def transcribe(path: str, model_size: str = "small", language: str | None = None, device: str = "cpu") -> list[dict]:
    """Return segments ``[{"start": s, "end": s, "text": str}]``. Runs locally."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError("Transcription needs faster-whisper: pip install 'callscope-ai[whisper]'") from exc
    model = WhisperModel(model_size, device=device, compute_type="int8")
    segments, _info = model.transcribe(path, language=language, vad_filter=True)
    return [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segments]
