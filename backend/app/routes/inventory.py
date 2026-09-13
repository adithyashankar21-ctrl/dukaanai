from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import PriceUpdate, ProductResponse, StockAdjustmentCreate
from ..services import inventory_service

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)


@router.get("/search", response_model=list[ProductResponse])
def search_products(
    shop_id: int,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return inventory_service.search_products(db, shop_id, q)


@router.post("/adjust")
def adjust_stock(
    data: StockAdjustmentCreate,
    db: Session = Depends(get_db)
):
    try:
        result = inventory_service.adjust_stock(
            db,
            data.shop_id,
            data.product_id,
            data.delta,
            adjustment_type=data.adjustment_type,
            reason=data.reason,
            supplier=data.supplier,
            unit_cost=data.unit_cost,
            confirmed=data.confirmed,
        )
    except inventory_service.ConfirmationRequired as e:
        raise HTTPException(status_code=409, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    product = result["product"]

    return {
        "message": "Stock adjusted successfully",
        "product_id": product.id,
        "current_stock": product.current_stock,
    }


@router.put("/{product_id}/price", response_model=ProductResponse)
def update_price(
    product_id: int,
    data: PriceUpdate,
    db: Session = Depends(get_db)
):
    try:
        return inventory_service.update_price(
            db,
            data.shop_id,
            product_id,
            selling_price=data.selling_price,
            purchase_price=data.purchase_price,
            selling_price_delta=data.selling_price_delta,
            purchase_price_delta=data.purchase_price_delta,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/adjustments")
def list_adjustments(
    shop_id: int,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    adjustments = inventory_service.list_adjustments(db, shop_id, product_id)

    return [
        {
            "id": a.id,
            "product_id": a.product_id,
            "delta": a.delta,
            "adjustment_type": a.adjustment_type,
            "reason": a.reason,
            "supplier": a.supplier,
            "unit_cost": a.unit_cost,
            "created_at": a.created_at,
        }
        for a in adjustments
    ]
