"""A short, personalized thank-you note printed on every invoice PDF —
the one place on the invoice where DukaanAI actually speaks, generated from
the real details of that sale rather than a canned line. Deterministic and
never blocking: if the model is unreachable, a solid default line is used
instead, so a flaky AI call can never break generating an invoice.
"""
import logging
import re

from ..config import GROQ_MODEL
from .config_client import get_groq_client

logger = logging.getLogger(__name__)

DEFAULT_NOTE = "Thank you for shopping with us — we hope to see you again soon!"

MAX_NOTE_CHARS = 140


def _clean_note(text: str) -> str:
    if not text:
        return text
    text = text.strip().strip('"').strip()
    text = re.sub(r"[*_#`]", "", text)
    text = re.sub(r"\s+", " ", text)
    if len(text) > MAX_NOTE_CHARS:
        cut = text[:MAX_NOTE_CHARS].rsplit(" ", 1)[0]
        text = cut.rstrip(",.;:") + "…"
    return text


def generate_thank_you_note(invoice_data: dict) -> str:
    client = get_groq_client(max_retries=1)
    if client is None:
        return DEFAULT_NOTE

    customer = invoice_data.get("customer")
    customer_name = customer["name"] if customer else None
    items = invoice_data.get("items") or []
    item_names = [
        " ".join(p for p in [i.get("brand"), i.get("name"), i.get("variant")] if p)
        for i in items
    ]
    total = invoice_data.get("total_amount")

    facts = []
    if customer_name:
        facts.append(f"Customer: {customer_name}")
    if item_names:
        facts.append("Items: " + ", ".join(n for n in item_names[:4] if n))
    if total is not None:
        facts.append(f"Total: Rs. {total:.2f}")

    prompt = (
        "Write exactly one short, warm sentence to print at the bottom of a shop "
        "invoice, thanking the customer. Sound like a friendly neighbourhood shop "
        "owner, not a corporation. No markdown, no quotes, no emoji, under 18 words. "
        "Mention the customer's first name naturally if given. Never invent facts "
        "beyond what's listed.\n\n" + "\n".join(facts)
    )

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            frequency_penalty=0.4,
            # This model spends a chunk of its token budget on hidden
            # reasoning before writing the visible answer (observed ~130
            # reasoning tokens even at reasoning_effort="low") — too small a
            # max_tokens here silently truncates to an empty response rather
            # than erroring, so budget generously and let _clean_note trim
            # the visible output down to one short line.
            max_tokens=300,
            reasoning_effort="low",
        )
        note = _clean_note(response.choices[0].message.content)
        return note or DEFAULT_NOTE
    except Exception:
        logger.exception("invoice_ai_service.generate_thank_you_note failed; using default note")
        return DEFAULT_NOTE
