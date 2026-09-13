from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.radar_service import detect_signals

router = APIRouter(
    prefix="/radar",
    tags=["Dukaan Radar"],
)


@router.get("/")
def get_radar_signals(
    shop_id: int,
    lead_time_days: int | None = Query(default=None, ge=0, le=60),
    db: Session = Depends(get_db),
):
    """Continuous anomaly detection: which products are selling meaningfully
    more or less than their normal pace today, and what (if anything) to do
    about it.
    """
    return detect_signals(db, shop_id, lead_time_days=lead_time_days)
