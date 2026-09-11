from datetime import datetime
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Invoice, Shop, Sale, Customer, Product
from ..schemas import InvoiceCreate, InvoiceResponse
from .invoice_pdf import generate_invoice_pdf


router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)


@router.post("/", response_model=InvoiceResponse)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db)
):
    shop = db.query(Shop).filter(
        Shop.id == invoice_data.shop_id
    ).first()

    if not shop:
        raise HTTPException(
            status_code=404,
            detail="Shop not found"
        )

    if invoice_data.sale_id:
        sale = db.query(Sale).filter(
            Sale.id == invoice_data.sale_id,
            Sale.shop_id == invoice_data.shop_id
        ).first()

        if not sale:
            raise HTTPException(
                status_code=404,
                detail="Sale not found"
            )

    # Generate the next invoice number (per shop, based on existing numbers)
    existing_numbers = db.query(Invoice.invoice_number).filter(
        Invoice.shop_id == invoice_data.shop_id
    ).all()

    max_sequence = 0

    for (number,) in existing_numbers:
        try:
            max_sequence = max(max_sequence, int(number.split("-")[1]))
        except (IndexError, ValueError):
            continue

    invoice_number = f"INV-{max_sequence + 1:06d}"

    invoice = Invoice(
        shop_id=invoice_data.shop_id,
        customer_id=invoice_data.customer_id,
        sale_id=invoice_data.sale_id,
        invoice_number=invoice_number,
        total_amount=invoice_data.total_amount,
        payment_method=invoice_data.payment_method,
        status=invoice_data.status,
        created_at=datetime.now().isoformat()
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice

@router.get("/")
def get_invoices(
    shop_id: int,
    db: Session = Depends(get_db)
):
    invoices = db.query(Invoice).filter(
        Invoice.shop_id == shop_id
    ).order_by(
        Invoice.id.desc()
    ).all()

    result = []

    for invoice in invoices:

        customer = None
        if invoice.customer_id:
            customer = db.query(Customer).filter(
                Customer.id == invoice.customer_id
            ).first()

        sale = None
        if invoice.sale_id:
            sale = db.query(Sale).filter(
                Sale.id == invoice.sale_id
            ).first()

        items = []

        if sale:
            for item in sale.items:

                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).first()

                items.append({
                    "product_id": item.product_id,
                    "brand": product.brand if product else None,
                    "name": product.name if product else None,
                    "variant": product.variant if product else None,
                    "pack_size": product.pack_size if product else None,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                })

        result.append({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "shop_id": invoice.shop_id,
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone
            } if customer else None,
            "sale_id": invoice.sale_id,
            "items": items,
            "total_amount": invoice.total_amount,
            "payment_method": invoice.payment_method,
            "status": invoice.status,
            "created_at": invoice.created_at
        })

    return result

@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    shop_id: int,
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.shop_id == shop_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    customer = None

    if invoice.customer_id:
        customer = db.query(Customer).filter(
            Customer.id == invoice.customer_id
        ).first()

    sale = None

    if invoice.sale_id:
        sale = db.query(Sale).filter(
            Sale.id == invoice.sale_id
        ).first()

    items = []

    if sale:
        for item in sale.items:

            product = db.query(Product).filter(
                Product.id == item.product_id
            ).first()

            items.append({
                "product_id": item.product_id,
                "brand": product.brand if product else None,
                "name": product.name if product else None,
                "variant": product.variant if product else None,
                "pack_size": product.pack_size if product else None,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price
            })

    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "shop_id": invoice.shop_id,
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone
        } if customer else None,
        "sale_id": invoice.sale_id,
        "items": items,
        "total_amount": invoice.total_amount,
        "payment_method": invoice.payment_method,
        "status": invoice.status,
        "created_at": invoice.created_at
    }
@router.get("/{invoice_id}/pdf")
def generate_invoice(
    invoice_id: int,
    shop_id: int,
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.shop_id == shop_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    customer = None

    if invoice.customer_id:
        customer = db.query(Customer).filter(
            Customer.id == invoice.customer_id
        ).first()

    sale = None

    if invoice.sale_id:
        sale = db.query(Sale).filter(
            Sale.id == invoice.sale_id
        ).first()

    items = []

    if sale:
        for item in sale.items:

            product = db.query(Product).filter(
                Product.id == item.product_id
            ).first()

            items.append({
                "product_id": item.product_id,
                "brand": product.brand if product else None,
                "name": product.name if product else None,
                "variant": product.variant if product else None,
                "pack_size": product.pack_size if product else None,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price
            })

    invoice_data = {
        "invoice_number": invoice.invoice_number,
        "created_at": invoice.created_at,
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone
        } if customer else None,
        "items": items,
        "total_amount": invoice.total_amount,
        "payment_method": invoice.payment_method
    }

    file_path = f"invoice_{invoice.invoice_number}.pdf"

    generate_invoice_pdf(
        invoice_data,
        file_path
    )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=file_path
    )