from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models import Sale, SaleItem
from . import credit_service, inventory_service


def create_sale(
    db: Session,
    shop_id: int,
    items: list[dict],
    customer_id: int | None = None,
    payment_method: str = "cash",
) -> Sale:
    if not items:
        raise ValueError("A sale needs at least one item")

    if payment_method == "credit" and not customer_id:
        raise ValueError("A credit (udhaar) sale needs a customer")

    total_amount = 0.0
    prepared = []

    # Check every product before changing anything.
    for item in items:
        product = inventory_service.get_product(db, shop_id, item["product_id"])
        quantity = item["quantity"]
        unit_price = item.get("unit_price")
        if unit_price is None:
            unit_price = product.selling_price

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        if product.current_stock < quantity:
            raise ValueError(
                f"Not enough stock for {inventory_service.display_name(product)} — "
                f"only {product.current_stock} left"
            )

        item_total = quantity * unit_price
        total_amount += item_total

        prepared.append({
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": item_total,
        })

    sale = Sale(
        shop_id=shop_id,
        customer_id=customer_id,
        total_amount=total_amount,
        payment_method=payment_method,
        created_at=datetime.now().isoformat(),
    )

    db.add(sale)
    db.flush()

    for item in prepared:
        product = item["product"]
        product.current_stock -= item["quantity"]

        db.add(SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            total_price=item["total_price"],
        ))

    db.commit()
    db.refresh(sale)

    # Selling on udhaar adds the sale amount to the customer's ledger so
    # "who owes me money" / balance lookups reflect it immediately.
    if payment_method == "credit":
        credit_service.record_transaction(
            db,
            shop_id,
            customer_id,
            sale.total_amount,
            "credit",
            note=f"Udhaar sale #{sale.id}",
        )

    return sale


def list_sales(db: Session, shop_id: int) -> list[Sale]:
    return db.query(Sale).filter(Sale.shop_id == shop_id).order_by(Sale.id.desc()).all()


def get_sale(db: Session, shop_id: int, sale_id: int) -> Sale:
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.shop_id == shop_id).first()
    if not sale:
        raise LookupError(f"Sale {sale_id} not found")
    return sale


def sales_summary(db: Session, shop_id: int) -> dict:
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = now - timedelta(days=7)
    two_weeks_start = now - timedelta(days=14)

    sales = db.query(Sale).filter(
        Sale.shop_id == shop_id,
        Sale.created_at >= two_weeks_start.isoformat(),
    ).all()

    today_iso = today_start.isoformat()
    yesterday_iso = yesterday_start.isoformat()
    week_iso = week_start.isoformat()

    today_sales = [s for s in sales if s.created_at >= today_iso]
    yesterday_sales = [s for s in sales if yesterday_iso <= s.created_at < today_iso]
    this_week_sales = [s for s in sales if s.created_at >= week_iso]
    prev_week_sales = [s for s in sales if s.created_at < week_iso]

    return {
        "today_revenue": round(sum(s.total_amount for s in today_sales), 2),
        "today_sale_count": len(today_sales),
        "yesterday_revenue": round(sum(s.total_amount for s in yesterday_sales), 2),
        "yesterday_sale_count": len(yesterday_sales),
        "this_week_revenue": round(sum(s.total_amount for s in this_week_sales), 2),
        "previous_week_revenue": round(sum(s.total_amount for s in prev_week_sales), 2),
    }
