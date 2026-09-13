from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Customer, Invoice, Product, Sale, Shop


def _next_invoice_number(db: Session, shop_id: int) -> str:
    existing_numbers = db.query(Invoice.invoice_number).filter(
        Invoice.shop_id == shop_id
    ).all()

    max_sequence = 0
    for (number,) in existing_numbers:
        try:
            max_sequence = max(max_sequence, int(number.split("-")[1]))
        except (IndexError, ValueError):
            continue

    return f"INV-{max_sequence + 1:06d}"


def create_invoice(
    db: Session,
    shop_id: int,
    customer_id: int | None = None,
    sale_id: int | None = None,
    total_amount: float | None = None,
    payment_method: str | None = None,
    status: str = "paid",
) -> Invoice:
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise LookupError("Shop not found")

    sale = None
    if sale_id:
        sale = db.query(Sale).filter(Sale.id == sale_id, Sale.shop_id == shop_id).first()
        if not sale:
            raise LookupError(f"Sale {sale_id} not found")

        if total_amount is None:
            total_amount = sale.total_amount
        if customer_id is None:
            customer_id = sale.customer_id
        if payment_method is None:
            payment_method = sale.payment_method

    if total_amount is None:
        raise ValueError("total_amount is required when an invoice isn't created from a sale")

    invoice = Invoice(
        shop_id=shop_id,
        customer_id=customer_id,
        sale_id=sale_id,
        invoice_number=_next_invoice_number(db, shop_id),
        total_amount=total_amount,
        payment_method=payment_method or "cash",
        status=status,
        created_at=datetime.now().isoformat(),
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice


def get_invoice(db: Session, shop_id: int, invoice_id: int) -> Invoice:
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.shop_id == shop_id
    ).first()

    if not invoice:
        raise LookupError(f"Invoice {invoice_id} not found")

    return invoice


def get_invoice_by_number(db: Session, shop_id: int, invoice_number: str) -> Invoice:
    invoice_number = (invoice_number or "").strip()
    if not invoice_number:
        raise ValueError("Invoice number is required")

    invoice = db.query(Invoice).filter(
        Invoice.shop_id == shop_id,
        Invoice.invoice_number == invoice_number,
    ).first()

    if not invoice:
        raise LookupError(f"Invoice '{invoice_number}' not found")

    return invoice


def serialize_invoice(db: Session, invoice: Invoice) -> dict:
    shop = db.query(Shop).filter(Shop.id == invoice.shop_id).first()

    customer = None
    if invoice.customer_id:
        customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()

    sale = None
    if invoice.sale_id:
        sale = db.query(Sale).filter(Sale.id == invoice.sale_id).first()

    items = []
    if sale:
        for item in sale.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            items.append({
                "product_id": item.product_id,
                "brand": product.brand if product else None,
                "name": product.name if product else None,
                "variant": product.variant if product else None,
                "pack_size": product.pack_size if product else None,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            })

    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "shop_id": invoice.shop_id,
        "shop": {
            "name": shop.name,
            "owner_name": shop.owner_name,
            "phone": shop.phone,
            "location": shop.location,
        } if shop else None,
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
        } if customer else None,
        "sale_id": invoice.sale_id,
        "items": items,
        "total_amount": invoice.total_amount,
        "payment_method": invoice.payment_method,
        "status": invoice.status,
        "created_at": invoice.created_at,
    }


def list_invoices(db: Session, shop_id: int) -> list[dict]:
    invoices = db.query(Invoice).filter(
        Invoice.shop_id == shop_id
    ).order_by(Invoice.id.desc()).all()

    return [serialize_invoice(db, invoice) for invoice in invoices]
