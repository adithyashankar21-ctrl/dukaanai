"""Shared Groq client construction for every AI-powered feature in the app
(voice, invoice notes, ...) so API-key/availability handling lives in one
place instead of being duplicated per feature.
"""
from ..config import GROQ_API_KEY

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None

_client = None


def get_groq_client(max_retries: int = 2):
    """A ready Groq client, or None if no API key is configured / the groq
    package isn't installed. Callers that can't function without AI (voice)
    should raise on None themselves; callers with a sensible non-AI fallback
    (an invoice's default thank-you line) can just use the None case."""
    global _client

    if not GROQ_API_KEY or Groq is None:
        return None

    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY, max_retries=max_retries)

    return _client
