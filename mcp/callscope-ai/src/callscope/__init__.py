"""callscope: local analysis of customer-service calls."""

from .analysis import analyze, contact_reasons, key_moments, sentiment
from .diarize import diarize
from .transcribe import transcribe

__version__ = "0.1.2"
SCHEMA = "callscope/1"
__all__ = ["analyze", "contact_reasons", "diarize", "key_moments", "sentiment", "transcribe", "SCHEMA"]
