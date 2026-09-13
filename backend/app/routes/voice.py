from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import VoiceCommand
from ..services import voice_service

router = APIRouter(
    prefix="/voice",
    tags=["Voice"]
)


@router.post("/command")
def voice_command(
    data: VoiceCommand,
    db: Session = Depends(get_db)
):
    try:
        return voice_service.handle_command(
            db, data.shop_id, data.session_id, data.text,
            context_product_id=data.context_product_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
