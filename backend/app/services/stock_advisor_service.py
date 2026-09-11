from datetime import datetime, timedelta
from math import ceil

from sqlalchemy.orm import Session

from ..models import Product, Sale, SaleItem

# --- Configurable advisor assumptions -------------------------------------
DEFAULT_SUPPLIER_LEAD_TIME_DAYS = 2
SAFETY_STOCK_DAYS = 2          # extra buffer to reduce stockout risk
REVIEW_PERIOD_DAYS = 7         # order enough to cover lead time + one week
MIN_UNITS_FOR_PREDICTION = 5   # below this in 14 days -> insufficient history
TREND_THRESHOLD_PERCENT = 20.0 # +/-20% counts as increasing/decreasing
MAX_ORDER_CAP_DAYS = 30        # never recommend more than ~a month of stock

RECOMMEND_BUY_MORE = "BUY MORE"
RECOMMEND_BUY_LESS = "BUY LESS"
RECOMMEND_HOLD = "HOLD"
RECOMMEND_ORDER_NOW = "ORDER NOW"
RECOMMEND_WAIT = "WAIT"
RECOMMEND_INSUFFICIENT = "INSUFFICIENT DATA"

TREND_INCREASING = "increasing"
TREND_STABLE = "stable"
TREND_DECREASING = "decreasing"

URGENCY_CRITICAL = "critical"     # order today or risk stockout
URGENCY_ORDER_SOON = "order-soon" # order within a couple of days
URGENCY_WATCH = "watch"           # order within the week
URGENCY_OK = "ok"                 # plenty of runway
URGENCY_UNKNOWN = "unknown"       # not enough history

DO_NOT_WAIT_DAYS = 3  # if stockout is closer than this, do not wait

DISCLAIMER = (
    "Recommendations are estimates based on historical sales and assumed "
    "supplier lead times. They do not guarantee a product will never run "
    "out of stock."
)


def _build_display_name(product: Product) -> str:
    """brand + name + variant + pack_size, e.g. 'Nestle Maggi 2-Minute
    Noodles Masala 70g'. Each product ID is analyzed independently so
    different pack sizes are never combined."""
    parts = [
        product.brand,
        product.name,
        product.variant,
        product.pack_size,
    ]
    return " ".join(p for p in parts if p)


def _trend_and_growth(last7: int, prev7: int) -> tuple[str, float | None]:
    if prev7 > 0:
        growth = (last7 - prev7) / prev7 * 100.0
    elif last7 > 0:
        # Sales started recently; growth vs nothing is not meaningful.
        return TREND_INCREASING, None
    else:
        return TREND_STABLE, None

    if growth >= TREND_THRESHOLD_PERCENT:
        trend = TREND_INCREASING
    elif growth <= -TREND_THRESHOLD_PERCENT:
        trend = TREND_DECREASING
    else:
        trend = TREND_STABLE

    return trend, round(growth, 1)


def _demand_rate(last7: int, growth: float | None) -> float:
    """Trend-adjusted daily demand used for reorder math. The growth
    factor is capped between 0.5x and 1.5x so small datasets cannot
    produce extreme recommendations."""
    base = last7 / 7.0

    if growth is None:
        return base

    factor = min(1.5, max(0.5, 1.0 + growth / 100.0))
    return base * factor


def _recommendation(
    current_stock: int,
    reorder_point: int,
    days_until_stockout: float | None,
    trend: str,
    lead_time_days: int,
) -> str:
    if current_stock <= 0:
        return RECOMMEND_ORDER_NOW

    if current_stock <= reorder_point:
        if trend == TREND_INCREASING:
            return RECOMMEND_BUY_MORE
        if trend == TREND_DECREASING:
            if days_until_stockout is not None and days_until_stockout <= lead_time_days:
                return RECOMMEND_ORDER_NOW
            return RECOMMEND_BUY_LESS
        return RECOMMEND_ORDER_NOW

    # Stock is comfortably above the reorder point.
    if trend == TREND_DECREASING:
        return RECOMMEND_BUY_LESS
    if trend == TREND_INCREASING:
        return RECOMMEND_WAIT
    return RECOMMEND_HOLD


def _order_quantity(
    recommendation: str,
    current_stock: int,
    rate: float,
    lead_time_days: int,
) -> int:
    if recommendation not in (RECOMMEND_ORDER_NOW, RECOMMEND_BUY_MORE):
        return 0

    # Cover lead time + one review period + safety stock, minus what is
    # already on the shelf. Capped so we never suggest excessive stock.
    target = rate * (lead_time_days + REVIEW_PERIOD_DAYS) + rate * SAFETY_STOCK_DAYS
    quantity = ceil(target - current_stock)
    cap = ceil(rate * MAX_ORDER_CAP_DAYS)

    return max(1, min(quantity, cap))


def _explanation(
    recommendation: str,
    display_name: str,
    current_stock: int,
    avg_daily: float,
    days_until_stockout: float | None,
    trend: str,
    growth: float | None,
    reorder_point: int,
    order_qty: int,
    lead_time_days: int,
) -> str:
    name = display_name or "This product"

    if recommendation == RECOMMEND_INSUFFICIENT:
        return (
            f"Insufficient sales history for {name} in the last 14 days, "
            f"so no confident prediction can be made yet."
        )

    stock_line = f"Current stock is {current_stock} units"

    if avg_daily > 0 and days_until_stockout is not None:
        stock_line += (
            f", expected to last about {round(days_until_stockout, 1)} days "
            f"at the current pace of {round(avg_daily, 1)} units/day"
        )
    else:
        stock_line += " with no sales recorded in the last 7 days"

    trend_line = {
        TREND_INCREASING: "Demand is rising",
        TREND_DECREASING: "Demand is falling",
        TREND_STABLE: "Demand is steady",
    }[trend]

    if growth is not None:
        direction = "faster" if growth >= 0 else "slower"
        trend_line += f" — selling {abs(round(growth))}% {direction} than the previous week"

    lead_line = f"Supplier lead time is estimated at {lead_time_days} days"

    if recommendation == RECOMMEND_ORDER_NOW:
        return (
            f"Order {order_qty} units. {name} is at or below its reorder "
            f"point ({reorder_point}). {stock_line}. {trend_line}. {lead_line}."
        )

    if recommendation == RECOMMEND_BUY_MORE:
        return (
            f"Order {order_qty} units soon. {trend_line}, and {stock_line}, "
            f"which is at or below the reorder point ({reorder_point}). "
            f"{lead_line}."
        )

    if recommendation == RECOMMEND_BUY_LESS:
        return (
            f"Hold off on reordering {name}. {trend_line}. {stock_line} — "
            f"well above the reorder point ({reorder_point}). Existing stock "
            f"should cover expected demand."
        )

    if recommendation == RECOMMEND_HOLD:
        return (
            f"Keep stocking {name} at the same pace. {trend_line}, and "
            f"{stock_line}, comfortably above the reorder point ({reorder_point})."
        )

    # WAIT
    return (
        f"No order needed yet for {name}. {stock_line}, above the reorder "
        f"point ({reorder_point}). {trend_line} — recheck in a few days. "
        f"{lead_line}."
    )


# --- Stock timeline helpers ----------------------------------------------


def _stockout_timeline(
    current_stock: int,
    avg_daily: float,
    lead_time_days: int,
    now: datetime,
) -> dict:
    """When stock runs out and when the order must be placed.

    Outflow-based: stock / units-per-day = days left. The order-by date is
    the stockout date minus supplier lead time (order must ARRIVE before
    the shelf is empty, so it must be PLACED lead-time days earlier).
    """
    if avg_daily <= 0 or current_stock <= 0:
        return {
            "stockout_date": None,
            "days_until_stockout": None,
            "order_by_date": None,
            "days_until_order_by": None,
            "urgency": URGENCY_UNKNOWN if current_stock > 0 else URGENCY_CRITICAL,
        }

    days_left = current_stock / avg_daily
    stockout_dt = now + timedelta(days=days_left)
    order_by_dt = stockout_dt - timedelta(days=lead_time_days)

    days_until_order_by = round((order_by_dt - now).total_seconds() / 86400, 1)

    if days_until_order_by <= 0:
        urgency = URGENCY_CRITICAL
    elif days_until_order_by <= 1:
        urgency = URGENCY_ORDER_SOON
    elif days_until_order_by <= DO_NOT_WAIT_DAYS:
        urgency = URGENCY_WATCH
    else:
        urgency = URGENCY_OK

    return {
        "stockout_date": stockout_dt.strftime("%Y-%m-%d"),
        "days_until_stockout": round(days_left, 1),
        "order_by_date": order_by_dt.strftime("%Y-%m-%d"),
        "days_until_order_by": max(0.0, days_until_order_by),
        "urgency": urgency,
    }


def _timeline_sentence(timeline: dict, lead_time_days: int) -> str:
    urgency = timeline["urgency"]

    if urgency == URGENCY_UNKNOWN:
        return "Stockout date cannot be estimated without recent sales."

    stockout = timeline["stockout_date"]
    days_left = timeline["days_until_stockout"]

    if urgency == URGENCY_CRITICAL:
        return (
            f"Stock is expected to run out around {stockout} (about "
            f"{days_left} days left) — that is sooner than the "
            f"{lead_time_days}-day supplier lead time, so order today."
        )

    order_by = timeline["order_by_date"]
    days_to_order = timeline["days_until_order_by"]

    if urgency == URGENCY_ORDER_SOON:
        return (
            f"Stock lasts until around {stockout}; with a "
            f"{lead_time_days}-day lead time the order should be placed by "
            f"{order_by} — about {days_to_order} days from now."
        )

    if urgency == URGENCY_WATCH:
        return (
            f"Stock lasts until around {stockout}. Latest safe order date is "
            f"{order_by} ({days_to_order} days away)."
        )

    return (
        f"Stock is expected to last until around {stockout}; no rush — the "
        f"latest safe order date is {order_by}."
    )


# --- Shop-level AI analysis ------------------------------------------------


def _at_risk_products(recommendations: list[dict]) -> list[str]:
    """Products whose stockout arrives before an order could arrive."""
    risky = []
    for r in recommendations:
        if r["recommendation"] == RECOMMEND_INSUFFICIENT:
            continue
        if (
            r["urgency"] == URGENCY_CRITICAL
            or (
                r["days_until_stockout"] is not None
                and r["days_until_stockout"] <= DO_NOT_WAIT_DAYS
                and r["recommended_order_quantity"] > 0
            )
        ):
            name = r["display_name"]
            days = r["days_until_stockout"]
            risky.append(
                f"{name} — only about {days} days of stock left"
                if days is not None
                else f"{name} — out of stock"
            )
    return risky


def _oversupply_products(recommendations: list[dict]) -> list[str]:
    """Products where money is sitting on the shelf: falling demand and
    far more stock than the reorder point."""
    oversupplied = []
    for r in recommendations:
        if (
            r["demand_trend"] == TREND_DECREASING
            and r["current_stock"] > 0
            and r["reorder_point"] > 0
            and r["current_stock"] >= r["reorder_point"] * 4
        ):
            days = r["days_until_stockout"]
            oversupplied.append(
                f"{r['display_name']} — about {days} days of stock at the "
                f"current falling pace"
                if days is not None
                else f"{r['display_name']}"
            )
    return oversupplied


def _inventory_health_score(recommendations: list[dict]) -> int:
    """0-100. Starts perfect; deductions for each structural problem."""
    if not recommendations:
        return 100

    score = 100.0

    score -= 18 * sum(
        1 for r in recommendations if r["urgency"] == URGENCY_CRITICAL
    )
    score -= 6 * sum(
        1 for r in recommendations if r["urgency"] == URGENCY_ORDER_SOON
    )
    score -= 3 * sum(
        1 for r in recommendations if r["urgency"] == URGENCY_WATCH
    )
    score -= 4 * sum(
        1 for r in recommendations if r["recommendation"] == RECOMMEND_INSUFFICIENT
    )
    score -= 2 * sum(
        1 for r in recommendations if r["demand_trend"] == TREND_DECREASING
    )

    return max(0, min(100, round(score)))


def _shop_analysis(
    recommendations: list[dict],
    lead_time_days: int,
    now: datetime,
) -> dict:
    """Human-readable shop-level analysis built from the per-product data."""
    order_list = [
        r for r in recommendations
        if r["recommendation"] in (RECOMMEND_ORDER_NOW, RECOMMEND_BUY_MORE)
        and r["recommended_order_quantity"] > 0
    ]
    order_list.sort(key=lambda r: (r["days_until_order_by"] is None, r["days_until_order_by"]))

    total_units = sum(r["recommended_order_quantity"] for r in order_list)

    today_orders = [r for r in order_list if r["urgency"] == URGENCY_CRITICAL]
    this_week_orders = [
        r for r in order_list if r["urgency"] in (URGENCY_ORDER_SOON, URGENCY_WATCH)
    ]

    risky = _at_risk_products(recommendations)
    oversupplied = _oversupply_products(recommendations)
    health = _inventory_health_score(recommendations)

    # --- headline
    if not recommendations:
        headline = "Add products to your shop to unlock AI stock analysis."
    elif today_orders:
        headline = (
            f"{len(today_orders)} product(s) need to be ordered TODAY to avoid "
            f"running out before a new order can arrive."
        )
    elif order_list:
        headline = (
            f"{len(order_list)} product(s) should be ordered soon — nothing is "
            f"immediately critical."
        )
    elif risky:
        headline = "A few products are close to their reorder point — keep an eye on them."
    else:
        headline = "Stock levels look healthy across the shop."

    # --- what to do next
    actions: list[str] = []
    for r in today_orders:
        actions.append(
            f"Order {r['recommended_order_quantity']} units of "
            f"{r['display_name']} today (stockout ~{r['stockout_date']})."
        )
    for r in this_week_orders[:3]:
        actions.append(
            f"Order {r['recommended_order_quantity']} units of "
            f"{r['display_name']} by {r['order_by_date']}."
        )
    if not actions and order_list:
        for r in order_list[:3]:
            actions.append(
                f"Plan to order {r['recommended_order_quantity']} units of "
                f"{r['display_name']} by {r['order_by_date']}."
            )
    for name in oversupplied[:2]:
        actions.append(f"Slow down reordering: {name}.")

    insights = {
        "headline": headline,
        "actions": actions,
        "order_today": [
            {
                "product_id": r["product_id"],
                "display_name": r["display_name"],
                "order_quantity": r["recommended_order_quantity"],
                "stockout_date": r["stockout_date"],
                "order_by_date": r["order_by_date"],
            }
            for r in today_orders
        ],
        "order_this_week": [
            {
                "product_id": r["product_id"],
                "display_name": r["display_name"],
                "order_quantity": r["recommended_order_quantity"],
                "stockout_date": r["stockout_date"],
                "order_by_date": r["order_by_date"],
            }
            for r in this_week_orders
        ],
        "at_risk": risky,
        "oversupplied": oversupplied,
        "total_units_to_order": total_units,
    }

    return {"health_score": health, "insights": insights}


def analyze_shop_stock(
    db: Session,
    shop_id: int,
    lead_time_days: int | None = None,
) -> dict:
    lead = lead_time_days or DEFAULT_SUPPLIER_LEAD_TIME_DAYS

    products = (
        db.query(Product)
        .filter(Product.shop_id == shop_id)
        .order_by(Product.id)
        .all()
    )

    now = datetime.now()
    start_7d = (now - timedelta(days=7)).isoformat()
    start_14d = (now - timedelta(days=14)).isoformat()

    # One query for all sale items in the last 14 days for this shop.
    rows = (
        db.query(
            SaleItem.product_id,
            SaleItem.quantity,
            Sale.created_at,
        )
        .join(Sale, SaleItem.sale_id == Sale.id)
        .filter(
            Sale.shop_id == shop_id,
            Sale.created_at >= start_14d,
        )
        .all()
    )

    last7_units: dict[int, int] = {}
    prev7_units: dict[int, int] = {}

    for product_id, quantity, created_at in rows:
        if created_at >= start_7d:
            last7_units[product_id] = last7_units.get(product_id, 0) + quantity
        else:
            prev7_units[product_id] = prev7_units.get(product_id, 0) + quantity

    recommendations: list[dict] = []

    for product in products:
        last7 = last7_units.get(product.id, 0)
        prev7 = prev7_units.get(product.id, 0)
        display_name = _build_display_name(product)

        avg_daily = round(last7 / 7.0, 1)
        trend, growth = _trend_and_growth(last7, prev7)
        rate = _demand_rate(last7, growth)

        if avg_daily > 0:
            days_until_stockout = round(product.current_stock / avg_daily, 1)
        else:
            days_until_stockout = None

        reorder_point = ceil(rate * (lead + SAFETY_STOCK_DAYS))

        total_14d = last7 + prev7
        if total_14d < MIN_UNITS_FOR_PREDICTION:
            recommendation = RECOMMEND_INSUFFICIENT
        else:
            recommendation = _recommendation(
                product.current_stock,
                reorder_point,
                days_until_stockout,
                trend,
                lead,
            )

        order_qty = _order_quantity(
            recommendation,
            product.current_stock,
            rate,
            lead,
        )

        explanation = _explanation(
            recommendation,
            display_name,
            product.current_stock,
            avg_daily,
            days_until_stockout,
            trend,
            growth,
            reorder_point,
            order_qty,
            lead,
        )

        timeline = _stockout_timeline(
            product.current_stock,
            avg_daily,
            lead,
            now,
        )

        timeline_sentence = _timeline_sentence(timeline, lead)

        recommendations.append({
            "product_id": product.id,
            "brand": product.brand,
            "name": product.name,
            "variant": product.variant,
            "pack_size": product.pack_size,
            "display_name": display_name,
            "current_stock": product.current_stock,
            "units_sold_last_7_days": last7,
            "units_sold_prev_7_days": prev7,
            "avg_daily_sales": avg_daily,
            "sales_growth_percent": growth,
            "demand_trend": trend,
            "days_until_stockout": days_until_stockout,
            "reorder_point": reorder_point,
            "recommended_order_quantity": order_qty,
            "recommendation": recommendation,
            "explanation": explanation,
            "stockout_date": timeline["stockout_date"],
            "order_by_date": timeline["order_by_date"],
            "days_until_order_by": timeline["days_until_order_by"],
            "urgency": timeline["urgency"],
            "timeline": timeline_sentence,
        })

    summary = {
        "total_products": len(recommendations),
        "order_now": sum(
            1 for r in recommendations
            if r["recommendation"] in (RECOMMEND_ORDER_NOW, RECOMMEND_BUY_MORE)
        ),
        "trending_up": sum(
            1 for r in recommendations if r["demand_trend"] == TREND_INCREASING
        ),
        "trending_down": sum(
            1 for r in recommendations if r["demand_trend"] == TREND_DECREASING
        ),
        "can_wait": sum(
            1 for r in recommendations
            if r["recommendation"] in (RECOMMEND_WAIT, RECOMMEND_HOLD, RECOMMEND_BUY_LESS)
        ),
        "insufficient_data": sum(
            1 for r in recommendations
            if r["recommendation"] == RECOMMEND_INSUFFICIENT
        ),
    }

    shop_level = _shop_analysis(recommendations, lead, now)

    return {
        "shop_id": shop_id,
        "lead_time_days": lead,
        "summary": summary,
        "health_score": shop_level["health_score"],
        "insights": shop_level["insights"],
        "products": recommendations,
        "disclaimer": DISCLAIMER,
    }
