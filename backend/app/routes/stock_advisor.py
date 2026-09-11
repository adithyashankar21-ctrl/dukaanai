from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.stock_advisor_service import analyze_shop_stock

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
