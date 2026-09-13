"""Voice orchestration: turns natural-language shopkeeper commands into real
business operations, using the exact same service functions the REST routes
(and therefore the UI buttons) call. A button action and a voice action that
do the same thing always hit the same code path below.
"""
import json
import logging
import re
import time
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from ..config import GROQ_MODEL
from . import credit_service, customer_service, inventory_service, invoice_service, radar_service, sales_service, stock_advisor_service
from .config_client import get_groq_client

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 6
MAX_TURNS_KEPT = 12

_SESSIONS: dict[str, list[dict]] = {}


def _get_client():
    client = get_groq_client(max_retries=2)
    if client is None:
        raise RuntimeError(
            "Voice assistant is not configured — set GROQ_API_KEY in backend/.env and restart the server."
        )
    return client


def _call_model(client, messages: list[dict]):
    """Call the chat model with a couple of short retries for transient
    errors (rate limits, momentary connection issues) before giving up —
    the Groq free tier's per-minute token limit is easy to brush against
    mid-conversation."""
    last_error = None
    for attempt in range(3):
        try:
            return client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
                # The small open-weight model on this route occasionally gets
                # stuck echoing its own last sentence(s) verbatim, especially
                # at low temperature — a frequency penalty makes repeating
                # tokens/phrases costlier and steers it away from that loop.
                frequency_penalty=0.4,
                presence_penalty=0.2,
            )
        except Exception as e:  # groq.RateLimitError / APIConnectionError / etc.
            last_error = e
            if attempt < 2:
                time.sleep(0.6 * (attempt + 1))
    raise last_error


# --- serialization helpers --------------------------------------------------

def _product_brief(product) -> dict:
    return {
        "product_id": product.id,
        "display_name": inventory_service.display_name(product),
        "brand": product.brand,
        "name": product.name,
        "variant": product.variant,
        "pack_size": product.pack_size,
        "unit": product.unit,
        "selling_price": product.selling_price,
        "purchase_price": product.purchase_price,
        "current_stock": product.current_stock,
        "minimum_stock": product.minimum_stock,
        "supplier": product.supplier,
    }


def _customer_brief(customer) -> dict:
    return {
        "customer_id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
    }


def _sale_brief(sale) -> dict:
    return {
        "sale_id": sale.id,
        "total_amount": sale.total_amount,
        "payment_method": sale.payment_method,
        "customer_id": sale.customer_id,
        "created_at": sale.created_at,
        "items": [
            {
                "product_id": i.product_id,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "total_price": i.total_price,
            }
            for i in sale.items
        ],
    }


# --- tool handlers -----------------------------------------------------------
# Each handler takes (db, shop_id, args) and returns a JSON-serializable dict.
# Errors are raised as LookupError/ValueError and converted to {"error": ...}
# by _dispatch, never crash the orchestration loop.

def _h_search_products(db, shop_id, args):
    products = inventory_service.search_products(db, shop_id, args.get("query"), limit=args.get("limit") or 15)
    return {"products": [_product_brief(p) for p in products], "count": len(products)}


def _h_search_customers(db, shop_id, args):
    customers = customer_service.search_customers(db, shop_id, args.get("query"), limit=args.get("limit") or 15)
    return {"customers": [_customer_brief(c) for c in customers], "count": len(customers)}


def _h_create_customer(db, shop_id, args):
    customer = customer_service.create_customer(db, shop_id, args["name"], args.get("phone"))
    return {"created": True, "customer": _customer_brief(customer)}


def _h_create_product(db, shop_id, args):
    product = inventory_service.create_product(
        db,
        shop_id,
        name=args["name"],
        brand=args.get("brand"),
        variant=args.get("variant"),
        pack_size=args.get("pack_size"),
        unit=args.get("unit"),
        sku=args.get("sku"),
        barcode=args.get("barcode"),
        purchase_price=args.get("purchase_price"),
        selling_price=args["selling_price"],
        current_stock=args.get("current_stock", 0),
        minimum_stock=args.get("minimum_stock", 5),
        supplier=args.get("supplier"),
    )
    return {"created": True, "product": _product_brief(product)}


def _h_adjust_stock(db, shop_id, args):
    result = inventory_service.adjust_stock(
        db,
        shop_id,
        args["product_id"],
        args["delta"],
        adjustment_type=args.get("adjustment_type", "correction"),
        reason=args.get("reason"),
        supplier=args.get("supplier"),
        unit_cost=args.get("unit_cost"),
        confirmed=args.get("confirmed", False),
    )
    return {"adjusted": True, "product": _product_brief(result["product"])}


def _h_update_price(db, shop_id, args):
    product = inventory_service.update_price(
        db,
        shop_id,
        args["product_id"],
        selling_price=args.get("selling_price"),
        purchase_price=args.get("purchase_price"),
        selling_price_delta=args.get("selling_price_delta"),
        purchase_price_delta=args.get("purchase_price_delta"),
    )
    return {"updated": True, "product": _product_brief(product)}


def _h_create_sale(db, shop_id, args):
    sale = sales_service.create_sale(
        db,
        shop_id,
        items=args["items"],
        customer_id=args.get("customer_id"),
        payment_method=args.get("payment_method", "cash"),
    )
    return {"sale": _sale_brief(sale)}


def _h_sales_summary(db, shop_id, args):
    return sales_service.sales_summary(db, shop_id)


def _h_record_credit_transaction(db, shop_id, args):
    txn = credit_service.record_transaction(
        db,
        shop_id,
        args["customer_id"],
        args["amount"],
        args["transaction_type"],
        args.get("note"),
    )
    balance = credit_service.get_balance(db, shop_id, args["customer_id"])
    return {"transaction_id": txn.id, "new_balance": balance}


def _h_get_customer_balance(db, shop_id, args):
    customer = customer_service.get_customer(db, shop_id, args["customer_id"])
    balance = credit_service.get_balance(db, shop_id, args["customer_id"])
    return {"customer": _customer_brief(customer), "balance": balance}


def _h_list_customer_balances(db, shop_id, args):
    return {"balances": credit_service.list_balances(db, shop_id)}


def _h_create_invoice(db, shop_id, args):
    invoice = invoice_service.create_invoice(
        db,
        shop_id,
        customer_id=args.get("customer_id"),
        sale_id=args.get("sale_id"),
        total_amount=args.get("total_amount"),
        payment_method=args.get("payment_method"),
        status=args.get("status", "paid"),
    )
    return {
        "invoice": invoice_service.serialize_invoice(db, invoice),
        "invoice_number": invoice.invoice_number,
        "pdf_url": f"/invoices/by-number/{invoice.invoice_number}/pdf?shop_id={shop_id}",
    }


def _h_get_invoice(db, shop_id, args):
    invoice = invoice_service.get_invoice(db, shop_id, args["invoice_id"])
    return {"invoice": invoice_service.serialize_invoice(db, invoice)}


def _h_print_invoice(db, shop_id, args):
    invoice_number = args.get("invoice_number")
    invoice_id = args.get("invoice_id")

    if invoice_number:
        invoice = invoice_service.get_invoice_by_number(db, shop_id, invoice_number)
    elif invoice_id:
        invoice = invoice_service.get_invoice(db, shop_id, invoice_id)
    else:
        return {"error": "Provide an invoice_number (e.g. 'INV-000006') or invoice_id"}

    return {
        "printed": True,
        "invoice_number": invoice.invoice_number,
        "pdf_url": f"/invoices/by-number/{invoice.invoice_number}/pdf?shop_id={shop_id}",
    }


def _h_get_stock_advice(db, shop_id, args):
    data = stock_advisor_service.analyze_shop_stock(db, shop_id, lead_time_days=args.get("lead_time_days"))

    # Only pass along products that actually need attention (low/about-to-
    # finish stock, a reorder that looks delayed, or heavy overstock worth a
    # return) — otherwise a shop with 50 healthy products makes the model
    # recite all 50 instead of just answering what's actually wrong.
    compact_products = [
        {
            "product_id": p["product_id"],
            "display_name": p["display_name"],
            "current_stock": p["current_stock"],
            "avg_daily_sales": p["avg_daily_sales"],
            "demand_trend": p["demand_trend"],
            "sales_growth_percent": p["sales_growth_percent"],
            "recommendation": p["recommendation"],
            "recommended_order_quantity": p["recommended_order_quantity"],
            "urgency": p["urgency"],
            "days_until_stockout": p["days_until_stockout"],
            "order_by_date": p["order_by_date"],
            "explanation": p["explanation"],
        }
        for p in data["products"]
        if p["needs_attention"]
    ]

    return {
        "summary": data["summary"],
        "health_score": data["health_score"],
        "insights": data["insights"],
        "products_needing_attention": compact_products,
        "note": (
            "products_needing_attention lists only products with a real issue "
            "(low stock, delayed-looking reorder, or heavy overstock). Every "
            "other product in the shop is adequately stocked — say so plainly "
            "rather than listing them."
        ),
    }


def _h_get_radar_alerts(db, shop_id, args):
    return radar_service.detect_signals(db, shop_id, lead_time_days=args.get("lead_time_days"))


_HANDLERS = {
    "search_products": _h_search_products,
    "search_customers": _h_search_customers,
    "create_customer": _h_create_customer,
    "create_product": _h_create_product,
    "adjust_stock": _h_adjust_stock,
    "update_price": _h_update_price,
    "create_sale": _h_create_sale,
    "get_sales_summary": _h_sales_summary,
    "record_credit_transaction": _h_record_credit_transaction,
    "get_customer_balance": _h_get_customer_balance,
    "list_customer_balances": _h_list_customer_balances,
    "create_invoice": _h_create_invoice,
    "get_invoice": _h_get_invoice,
    "print_invoice": _h_print_invoice,
    "get_stock_advice": _h_get_stock_advice,
    "get_radar_alerts": _h_get_radar_alerts,
}

# Which frontend data domains a successful tool call affects, so the UI knows
# what to refetch after a voice command — the same domains a button refetches.
_DOMAINS_BY_TOOL = {
    "create_customer": {"customers"},
    "create_product": {"products"},
    "adjust_stock": {"products"},
    "update_price": {"products"},
    "create_sale": {"products", "sales", "credit"},
    "record_credit_transaction": {"credit"},
    "create_invoice": {"invoices"},
}


def _dispatch(db: Session, shop_id: int, name: str, args: dict) -> dict:
    handler = _HANDLERS.get(name)
    if not handler:
        return {"error": f"Unknown tool '{name}'"}

    try:
        return handler(db, shop_id, args)
    except inventory_service.ConfirmationRequired as e:
        return {"confirmation_required": True, "message": str(e)}
    except LookupError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except KeyError as e:
        return {"error": f"Missing required field: {e}"}
    except Exception as e:  # never let a bad tool call kill the conversation
        return {"error": f"Something went wrong: {e}"}


# --- tool schemas (OpenAI / Groq function-calling format) ------------------

def _allow_null_for_optional_params(tools: list[dict]) -> list[dict]:
    """Groq's structured tool-calling strictly validates the model's
    generated tool-call arguments against our JSON schema — and this model
    sometimes explicitly passes null for a parameter it doesn't want to set,
    instead of just omitting it. A plain {"type": "integer"} schema rejects
    that outright with a 400, crashing the entire turn before our own code
    (which already treats a missing key as "not provided") ever runs. Widen
    every optional (non-required) parameter to also accept null so that's a
    harmless no-op instead of a hard failure."""
    def widen(prop: dict) -> None:
        t = prop.get("type")
        if isinstance(t, str) and t != "null":
            prop["type"] = [t, "null"]
        if "enum" in prop and None not in prop["enum"]:
            prop["enum"] = [*prop["enum"], None]

    def walk(schema) -> None:
        if not isinstance(schema, dict):
            return
        if schema.get("type") == "object" and isinstance(schema.get("properties"), dict):
            required = set(schema.get("required", []))
            for key, prop in schema["properties"].items():
                if not isinstance(prop, dict):
                    continue
                if key not in required:
                    widen(prop)
                walk(prop)
        elif schema.get("type") == "array" and isinstance(schema.get("items"), dict):
            walk(schema["items"])

    tools = json.loads(json.dumps(tools))  # deep copy
    for tool in tools:
        walk(tool["function"]["parameters"])
    return tools


_RAW_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search the shop's product catalog by name, brand, variant or pack size. "
                "Always use this to resolve a product the shopkeeper mentions before selling, "
                "restocking, pricing or adjusting it — never guess between similar products. "
                "Call with an empty query to list the shop's products."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free-text search, e.g. 'maggi 70'"},
                    "limit": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_customers",
            "description": (
                "Search the shop's customers by name or phone. Use to resolve a customer "
                "mentioned by name before recording a sale, payment or udhaar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_customer",
            "description": "Add a brand-new customer. Only call after search_customers confirms they don't already exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_product",
            "description": (
                "Add a brand-new product/SKU to the catalog. Only call after search_products confirms "
                "it doesn't already exist. To add stock of a product that already exists, use adjust_stock instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "brand": {"type": "string"},
                    "variant": {"type": "string"},
                    "pack_size": {"type": "string"},
                    "unit": {"type": "string"},
                    "sku": {"type": "string"},
                    "barcode": {"type": "string"},
                    "selling_price": {"type": "number"},
                    "purchase_price": {"type": "number"},
                    "current_stock": {"type": "integer", "description": "Opening stock, default 0"},
                    "minimum_stock": {"type": "integer", "description": "Reorder alert threshold, default 5"},
                    "supplier": {"type": "string"},
                },
                "required": ["name", "selling_price"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_stock",
            "description": (
                "Change the stock level of an EXISTING product found via search_products — for restocking "
                "(buying more from a supplier), recording damaged/expired/lost goods, or correcting a count. "
                "Positive delta adds units, negative delta removes units. For a normal sale to a customer, "
                "use create_sale instead, not this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                    "delta": {"type": "integer", "description": "Units to add (positive) or remove (negative)"},
                    "adjustment_type": {"type": "string", "enum": ["restock", "damage", "correction"]},
                    "reason": {"type": "string"},
                    "supplier": {"type": "string", "description": "Supplier name, for restocks"},
                    "unit_cost": {"type": "number", "description": "Purchase price per unit, for restocks"},
                    "confirmed": {
                        "type": "boolean",
                        "description": (
                            "Leave false on the first attempt. If the result comes back with "
                            "confirmation_required, ask the shopkeeper to confirm, then call this "
                            "again with confirmed=true and the same arguments."
                        ),
                    },
                },
                "required": ["product_id", "delta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_price",
            "description": (
                "Change a product's selling price and/or purchase price. Use the *_delta fields for relative "
                "changes like 'increase by 2 rupees', or the absolute fields to set an exact new price."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                    "selling_price": {"type": "number"},
                    "purchase_price": {"type": "number"},
                    "selling_price_delta": {"type": "number"},
                    "purchase_price_delta": {"type": "number"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_sale",
            "description": (
                "Record a sale of one or more products to a customer (or a walk-in if no customer is named). "
                "payment_method 'credit' means udhaar — the amount is added to the customer's balance and a "
                "customer is required. Every product_id must come from search_products."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "integer"},
                                "quantity": {"type": "integer"},
                                "unit_price": {
                                    "type": "number",
                                    "description": "Omit to use the product's current selling price",
                                },
                            },
                            "required": ["product_id", "quantity"],
                        },
                    },
                    "customer_id": {"type": "integer"},
                    "payment_method": {"type": "string", "enum": ["cash", "upi", "card", "credit"]},
                },
                "required": ["items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales_summary",
            "description": (
                "Get today's, yesterday's, this week's and last week's revenue totals for the shop. "
                "Use for 'how much did I make today', 'why are sales lower' etc."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_credit_transaction",
            "description": (
                "Record a standalone udhaar (credit) entry or a customer payment against their balance — "
                "not tied to a specific sale. transaction_type 'payment' reduces what they owe; "
                "'credit' increases it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer"},
                    "amount": {"type": "number"},
                    "transaction_type": {"type": "string", "enum": ["credit", "payment"]},
                    "note": {"type": "string"},
                },
                "required": ["customer_id", "amount", "transaction_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_balance",
            "description": "Get how much a specific customer currently owes (their udhaar balance).",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "integer"}},
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_customer_balances",
            "description": "List every customer who currently owes the shop money, highest balance first. Use for 'who owes me money'.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_invoice",
            "description": (
                "Generate an invoice, normally for a sale just recorded (pass sale_id). Call after create_sale "
                "when the shopkeeper asks for an invoice/bill/receipt for that sale."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sale_id": {"type": "integer"},
                    "customer_id": {"type": "integer"},
                    "total_amount": {"type": "number"},
                    "payment_method": {"type": "string"},
                    "status": {"type": "string", "enum": ["paid", "unpaid", "partial"]},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_invoice",
            "description": "Fetch an invoice's details by its invoice_id.",
            "parameters": {
                "type": "object",
                "properties": {"invoice_id": {"type": "integer"}},
                "required": ["invoice_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "print_invoice",
            "description": (
                "Generate a downloadable PDF for an existing invoice. Use whenever the shopkeeper "
                "asks to print, generate, download, email, or get a copy/PDF/bill/receipt of an "
                "invoice — the app shows them a download link automatically, so you never need to "
                "fetch or describe the PDF's contents yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string", "description": "e.g. 'INV-000006'"},
                    "invoice_id": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_advice",
            "description": (
                "Get the AI stock advisor's per-product recommendations, demand trends and reorder "
                "suggestions for the whole shop. Use for 'what should I reorder', 'what will run out', "
                "'which products are selling faster/slower', 'prepare tomorrow's purchase order'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_time_days": {"type": "integer", "description": "Supplier lead time override, in days"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_radar_alerts",
            "description": (
                "Dukaan Radar: check for products selling meaningfully more or less than their "
                "normal pace TODAY specifically (not the general weekly trend). Use for 'anything "
                "unusual today', 'what's changed', 'any alerts', 'is everything normal', "
                "'why are Pepsi sales down'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_time_days": {"type": "integer", "description": "Supplier lead time override, in days"},
                },
            },
        },
    },
]

TOOLS = _allow_null_for_optional_params(_RAW_TOOLS)


# --- conversation orchestration ---------------------------------------------

def _system_prompt(shop_id: int) -> dict:
    now = datetime.now()
    content = f"""You are DukaanAI, the voice-operated AI employee running a small Indian retail shop (shop_id={shop_id}). Current date/time: {now.strftime('%A, %d %B %Y, %H:%M')}.

You are not a chatbot that talks ABOUT the shop — you are the operator that DOES things in it. Every tool call you make is a real change to a real database, and the shopkeeper's screen updates live from it.

Rules:
1. Resolve every product and customer mentioned by calling search_products / search_customers first. Never guess between multiple plausible matches — if more than one exists, ask which one in one short question, naming the distinguishing detail (pack size, brand, phone number).
2. Never invent data. Only state facts returned by your tools.
3. Only say an action succeeded (e.g. "Done", "Sold", "Recorded") after the matching tool call actually returned success. If a tool call returns an error, explain plainly what went wrong — do not pretend it worked.
4. If required information is missing (product, quantity, customer, payment method), ask ONE short clarifying question at a time, and remember the shopkeeper's earlier answers in this conversation — never make them repeat the whole command.
5. Before a large or hard-to-reverse action — a big price change, anything beyond exactly what was asked — ask for a quick confirmation first, then act once they confirm. For adjust_stock specifically, the backend itself enforces this: a risky removal returns {{"confirmation_required": true, "message": ...}} instead of failing or succeeding — that is NOT an error, it means ask the shopkeeper that message as a yes/no question, and if they agree, call adjust_stock again with the exact same arguments plus confirmed=true.
6. A single request can require several tool calls in the right order (e.g. sell, then create an invoice for that sale, then report the new balance) — do them all before giving your final spoken reply.
7. Keep replies short and speakable, like a sharp shop assistant talking out loud — no markdown, no bullet lists, no headers. State money in ₹ rupees.
8. Match the shopkeeper's language/style (English, Hindi or Hinglish) where you reasonably can; default to simple English.
9. Selling on credit (udhaar) requires a customer — ask who it's for if that's not clear.
10. When print_invoice succeeds, just confirm briefly (e.g. "Here's the PDF for INV-000006") — the app already shows a download button, so never paste a URL/path into your reply.
"""
    return {"role": "system", "content": content}


def _strip_markdown(text: str) -> str:
    """The prompt asks for short, speakable, markdown-free replies, but a
    small model doesn't always comply — flatten bullet/numbered lines and
    bold/italic markers into plain speakable text rather than reading
    asterisks and dashes aloud or showing them raw in the transcript."""
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*•]\s+", "", line)
        line = re.sub(r"^\d+[.)]\s+", "", line)
        lines.append(line)
    flat = " ".join(lines)
    flat = re.sub(r"\*\*(.+?)\*\*", r"\1", flat)
    flat = re.sub(r"(?<![\d*])\*(?![\d*])", "", flat)
    flat = re.sub(r"`(.+?)`", r"\1", flat)
    return re.sub(r"\s+", " ", flat).strip()


def _dedupe_repeated_sentences(text: str) -> str:
    """Collapse a run of one or more consecutive sentences that repeats
    immediately after itself — whether that's the whole reply doubled/
    tripled, or just one fact restated 2-3 times in a row. Small open-weight
    models do both; this catches either regardless of exact whitespace
    between the copies."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    norm = [re.sub(r"\s+", " ", s.strip().lower()) for s in sentences]
    n = len(sentences)

    out = []
    i = 0
    while i < n:
        matched = False
        for block in range(min(4, (n - i) // 2), 0, -1):
            if norm[i:i + block] != norm[i + block:i + 2 * block]:
                continue
            j = i + block
            while j + block <= n and norm[j:j + block] == norm[i:i + block]:
                j += block
            out.extend(sentences[i:i + block])
            i = j
            matched = True
            break
        if not matched:
            out.append(sentences[i])
            i += 1
    return " ".join(out)


def _clean_reply(text: str) -> str:
    """Small open-weight models occasionally run sentences together with no
    space, or repeat their whole reply (or individual sentences within it)
    verbatim. Neither is a business-logic problem, just a rough edge in the
    model's own text — tidy it up rather than reading it out or displaying
    it broken/repeated."""
    if not text:
        return text

    text = _strip_markdown(text.strip())

    # "each.Done." -> "each. Done." (missing space after a sentence end) —
    # do this before splitting into sentences, so runs-together repeats are
    # still detected as separate sentences below.
    text = re.sub(r"([.!?,])(?=[A-Z])", r"\1 ", text)

    return _dedupe_repeated_sentences(text)


def _trim_history(history: list[dict], max_turns: int = MAX_TURNS_KEPT) -> list[dict]:
    user_indices = [i for i, m in enumerate(history) if m["role"] == "user"]
    if len(user_indices) <= max_turns:
        return history
    cutoff = user_indices[-max_turns]
    return history[cutoff:]


def handle_command(
    db: Session,
    shop_id: int,
    session_id: str | None,
    text: str,
    context_product_id: int | None = None,
) -> dict:
    if not text or not text.strip():
        raise ValueError("No speech/text received")

    client = _get_client()

    session_id = session_id or str(uuid.uuid4())
    history = _SESSIONS.get(session_id, [])
    history.append({"role": "user", "content": text.strip()})
    # Persist immediately so the user's message is never lost even if the
    # model call below fails on the very first iteration of a new session.
    _SESSIONS[session_id] = history

    actions: list[dict] = []
    domains_touched: set[str] = set()
    final_text = None

    messages = [_system_prompt(shop_id)]

    # A scanned barcode (or any other "here's the product on screen right
    # now" moment) is passed as ephemeral context, not saved into history —
    # it reflects what's on screen for THIS turn, so a stale product doesn't
    # leak into later, unrelated turns of the same conversation.
    if context_product_id is not None:
        try:
            context_product = inventory_service.get_product(db, shop_id, context_product_id)
            messages.append({
                "role": "system",
                "content": (
                    "The shopkeeper is currently looking at this exact product on their "
                    "screen (they just scanned its barcode): "
                    f"{json.dumps(_product_brief(context_product), default=str)}. "
                    "If their next message refers to it without naming it — e.g. "
                    "'add 40 units', 'sell 2', 'how is it doing', 'should I reorder' — "
                    "apply the action or question directly to this product_id. You do not "
                    "need to call search_products for it first."
                ),
            })
        except LookupError:
            pass

    messages += history

    try:
        for _ in range(MAX_TOOL_ITERATIONS):
            response = _call_model(client, messages)
            choice = response.choices[0].message
            tool_calls = choice.tool_calls or []

            assistant_entry = {"role": "assistant", "content": choice.content or ""}

            if tool_calls:
                assistant_entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in tool_calls
                ]
                messages.append(assistant_entry)
                history.append(assistant_entry)

                for tc in tool_calls:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}

                    # Tool execution is real and already committed to the DB
                    # the moment this runs — regardless of whether the model
                    # call that follows succeeds, so never lose this record.
                    result = _dispatch(db, shop_id, tc.function.name, args)
                    actions.append({"tool": tc.function.name, "args": args, "result": result})

                    if "error" not in result and "confirmation_required" not in result:
                        domains_touched.update(_DOMAINS_BY_TOOL.get(tc.function.name, set()))

                    tool_entry = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                        "content": json.dumps(result, default=str),
                    }
                    messages.append(tool_entry)
                    history.append(tool_entry)

                continue

            final_text = _clean_reply(choice.content) or "Sorry, I didn't catch that — could you say it again?"
            messages.append(assistant_entry)
            history.append(assistant_entry)
            break

        if final_text is None:
            final_text = "I'm having trouble finishing that — could you try rephrasing or breaking it into smaller steps?"
            history.append({"role": "assistant", "content": final_text})
    except Exception:
        # The AI model itself is unreachable/rate-limited. Any tool calls
        # already made in this turn are real and already committed — say so
        # honestly rather than claiming total failure.
        logger.exception("voice_service.handle_command failed mid-conversation (session=%s)", session_id)
        if actions:
            final_text = (
                "I got partway through that — the AI model hiccuped before I could finish. "
                "Ask me to check what happened, or try again."
            )
        else:
            final_text = "I couldn't reach the AI model just now — please try again in a few seconds."
        history.append({"role": "assistant", "content": final_text})
    finally:
        _SESSIONS[session_id] = _trim_history(history)

    downloads = [
        {"invoice_number": a["result"]["invoice_number"], "url": a["result"]["pdf_url"]}
        for a in actions
        if a["tool"] in ("print_invoice", "create_invoice") and "pdf_url" in a.get("result", {})
    ]

    return {
        "session_id": session_id,
        "reply": final_text,
        "actions": actions,
        "updated": sorted(domains_touched),
        "downloads": downloads,
    }
