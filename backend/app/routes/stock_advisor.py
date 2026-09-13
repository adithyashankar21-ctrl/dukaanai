from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import inventory_service
from ..services.stock_advisor_service import analyze_product, analyze_shop_stock

router = APIRouter(
    prefix="/stock-advisor",
    tags=["AI Stock Advisor"],
)


@router.get("/")
def get_stock_advice(
    shop_id: int,
    lead_time_days: int | None = Query(
        default=None,
        ge=0,
        le=60,
        description="Supplier lead time in days. Defaults to 2.",
    ),
    db: Session = Depends(get_db),
):
    """Deterministic AI stock advisor for every product in the shop.

    Each product is analyzed independently by its own product ID, so
    e.g. Maggi 70g and Maggi 140g never share sales data.
    """
    return analyze_shop_stock(
        db,
        shop_id,
        lead_time_days=lead_time_days,
    )


@router.get("/scan")
def scan_barcode(
    shop_id: int,
    barcode: str,
    lead_time_days: int | None = Query(default=None, ge=0, le=60),
    db: Session = Depends(get_db),
):
    """Identify a product by barcode (scanned via the shopkeeper's phone
    camera) and return the same real-time AI analysis as the stock advisor
    for it — stock, margin, velocity, predicted stockout — in one call.
    """
    try:
        product = inventory_service.get_product_by_barcode(db, shop_id, barcode)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return analyze_product(db, shop_id, product, lead_time_days=lead_time_days)


@router.get("/product/{product_id}")
def get_product_advice(
    product_id: int,
    shop_id: int,
    lead_time_days: int | None = Query(default=None, ge=0, le=60),
    db: Session = Depends(get_db),
):
    """Re-fetch one product's AI analysis by ID — used to refresh a scanned
    product's card live after a voice command changes its stock."""
    try:
        product = inventory_service.get_product(db, shop_id, product_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return analyze_product(db, shop_id, product, lead_time_days=lead_time_days)
