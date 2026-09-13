import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import InvoiceCreate, InvoiceResponse
from ..services import invoice_ai_service, invoice_service
from .invoice_pdf import generate_invoice_pdf


router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)


def _pdf_response(db: Session, invoice) -> Response:
    invoice_data = invoice_service.serialize_invoice(db, invoice)
    note = invoice_ai_service.generate_thank_you_note(invoice_data)

    buffer = io.BytesIO()
    generate_invoice_pdf(invoice_data, buffer, note=note)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{invoice.invoice_number}.pdf"'},
    )


@router.post("/", response_model=InvoiceResponse)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db)
):
    try:
        return invoice_service.create_invoice(
            db,
            invoice_data.shop_id,
            customer_id=invoice_data.customer_id,
            sale_id=invoice_data.sale_id,
            total_amount=invoice_data.total_amount,
            payment_method=invoice_data.payment_method,
            status=invoice_data.status,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def get_invoices(
    shop_id: int,
    db: Session = Depends(get_db)
):
    return invoice_service.list_invoices(db, shop_id)


@router.get("/by-number/{invoice_number}")
def get_invoice_by_number(
    invoice_number: str,
    shop_id: int,
    db: Session = Depends(get_db)
):
    try:
        invoice = invoice_service.get_invoice_by_number(db, shop_id, invoice_number)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return invoice_service.serialize_invoice(db, invoice)


@router.get("/by-number/{invoice_number}/pdf")
def generate_invoice_by_number(
    invoice_number: str,
    shop_id: int,
    db: Session = Depends(get_db)
):
    try:
        invoice = invoice_service.get_invoice_by_number(db, shop_id, invoice_number)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _pdf_response(db, invoice)


@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    shop_id: int,
    db: Session = Depends(get_db)
):
    try:
        invoice = invoice_service.get_invoice(db, shop_id, invoice_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return invoice_service.serialize_invoice(db, invoice)


@router.get("/{invoice_id}/pdf")
def generate_invoice(
    invoice_id: int,
    shop_id: int,
    db: Session = Depends(get_db)
):
    try:
        invoice = invoice_service.get_invoice(db, shop_id, invoice_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _pdf_response(db, invoice)
