"""Dukaan Radar: continuous anomaly detection on today's sales.

For every product with enough recent history, compares how much has sold
*today so far* against what's normal for this point in the day (its trailing
daily average, prorated by how much of the day has elapsed) and flags
products selling meaningfully more or less than usual.

Deliberately deterministic, not LLM-based — this needs to be fast, free of
network/rate-limit risk, and safe to poll frequently, and every number here
(stockout timeline, reorder quantity) reuses stock_advisor_service's already
-verified math rather than recomputing it a second, possibly-diverging way.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models import Product, Sale, SaleItem
from . import inventory_service
from .stock_advisor_service import (
    DEFAULT_SUPPLIER_LEAD_TIME_DAYS,
    RECOMMEND_BUY_MORE,
    SAFETY_STOCK_DAYS,
    _order_quantity,
    _stockout_timeline,
)

BASELINE_DAYS = 14
MIN_BASELINE_UNITS = 5      # need at least this many units in the baseline window to trust it
MIN_DAY_FRACTION = 0.12     # ~3 hours — don't judge "today" before enough of it has happened
MIN_EXPECTED_UNITS = 0.4    # today's prorated baseline must be at least this many units
SPIKE_THRESHOLD_PERCENT = 30.0

DIRECTION_UP = "up"
DIRECTION_DOWN = "down"

CAUSE_STOCKOUT = "stockout"
CAUSE_LOW_STOCK = "low_stock"
CAUSE_DEMAND_CHANGE = "demand_change"
CAUSE_UNKNOWN = "unknown"


def _cause_for_drop(current_stock: int, reorder_point: int) -> tuple[str, str]:
    if current_stock <= 0:
        return CAUSE_STOCKOUT, "You were out of stock today — that fully explains the drop."
    if reorder_point > 0 and current_stock <= reorder_point:
        return (
            CAUSE_LOW_STOCK,
            "Stock is running low, which may be limiting sales — consider reordering soon.",
        )
    return (
        CAUSE_DEMAND_CHANGE,
        "Stock is healthy, so this doesn't look like a stockout. Possible cause: demand change "
        "— worth checking pricing, a nearby competitor, or the season.",
    )


def detect_signals(db: Session, shop_id: int, lead_time_days: int | None = None) -> dict:
    lead = lead_time_days or DEFAULT_SUPPLIER_LEAD_TIME_DAYS
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed_fraction = min(1.0, (now - today_start).total_seconds() / 86400)

    if elapsed_fraction < MIN_DAY_FRACTION:
        return {
            "signals": [],
            "headline": "Too early in the day to compare against normal yet.",
            "checked_at": now.isoformat(),
        }

    window_start = (today_start - timedelta(days=BASELINE_DAYS)).isoformat()
    today_start_iso = today_start.isoformat()

    rows = (
        db.query(SaleItem.product_id, SaleItem.quantity, Sale.created_at)
        .join(Sale, SaleItem.sale_id == Sale.id)
        .filter(Sale.shop_id == shop_id, Sale.created_at >= window_start)
        .all()
    )

    baseline_units: dict[int, int] = {}
    today_units: dict[int, int] = {}
    for product_id, quantity, created_at in rows:
        bucket = today_units if created_at >= today_start_iso else baseline_units
        bucket[product_id] = bucket.get(product_id, 0) + quantity

    products = {p.id: p for p in db.query(Product).filter(Product.shop_id == shop_id).all()}

    signals: list[dict] = []

    for product_id, baseline_total in baseline_units.items():
        if baseline_total < MIN_BASELINE_UNITS:
            continue

        product = products.get(product_id)
        if not product:
            continue

        baseline_rate = baseline_total / BASELINE_DAYS
        expected_so_far = baseline_rate * elapsed_fraction
        if expected_so_far < MIN_EXPECTED_UNITS:
            continue

        actual_today = today_units.get(product_id, 0)
        percent_change = (actual_today - expected_so_far) / expected_so_far * 100

        if abs(percent_change) < SPIKE_THRESHOLD_PERCENT:
            continue

        display_name = inventory_service.display_name(product)

        if percent_change > 0:
            today_rate = actual_today / elapsed_fraction
            timeline = _stockout_timeline(product.current_stock, today_rate, lead, now)

            order_qty = 0
            if timeline["urgency"] in ("critical", "order-soon", "watch"):
                order_qty = _order_quantity(RECOMMEND_BUY_MORE, product.current_stock, today_rate, lead)

            signals.append({
                "product_id": product_id,
                "display_name": display_name,
                "direction": DIRECTION_UP,
                "percent_change": round(percent_change),
                "current_stock": product.current_stock,
                "days_until_stockout": timeline["days_until_stockout"],
                "urgency": timeline["urgency"],
                "recommended_order_quantity": order_qty,
                "cause": CAUSE_UNKNOWN,
                "cause_note": "Possible cause: a promotion, price change, or seasonal demand.",
                "headline": f"{display_name} sales are {abs(round(percent_change))}% higher than normal today.",
            })
        else:
            reorder_point = round(baseline_rate * (lead + SAFETY_STOCK_DAYS))
            cause, cause_note = _cause_for_drop(product.current_stock, reorder_point)

            signals.append({
                "product_id": product_id,
                "display_name": display_name,
                "direction": DIRECTION_DOWN,
                "percent_change": round(percent_change),
                "current_stock": product.current_stock,
                "days_until_stockout": None,
                "urgency": None,
                "recommended_order_quantity": 0,
                "cause": cause,
                "cause_note": cause_note,
                "headline": f"{display_name} sales suddenly dropped {abs(round(percent_change))}%.",
            })

    signals.sort(key=lambda s: abs(s["percent_change"]), reverse=True)

    if signals:
        headline = f"{len(signals)} unusual change{'s' if len(signals) != 1 else ''} detected today."
    else:
        headline = "No unusual changes detected today — everything looks normal."

    return {
        "signals": signals,
        "headline": headline,
        "checked_at": now.isoformat(),
    }
