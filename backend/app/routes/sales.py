from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product, Sale, SaleItem
from ..schemas import SaleCreate


router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)


@router.post("/")
def create_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db)
):

    total_amount = 0
    sale_items = []

    # Check every product before changing anything
    for item in sale_data.items:

        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.shop_id == sale_data.shop_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )

        if item.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than zero"
            )

        if product.current_stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.name}"
            )

        item_total = item.quantity * item.unit_price
        total_amount += item_total

        sale_items.append(
            {
                "product": product,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item_total
            }
        )

    # Create the sale
    sale = Sale(
        shop_id=sale_data.shop_id,
        customer_id=sale_data.customer_id,
        total_amount=total_amount,
        payment_method=sale_data.payment_method,
        created_at=datetime.now().isoformat()
    )

    db.add(sale)
    db.flush()

    # Reduce stock and create sale items
    for item in sale_items:

        product = item["product"]

        product.current_stock -= item["quantity"]

        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            total_price=item["total_price"]
        )

        db.add(sale_item)

    db.commit()
    db.refresh(sale)

    return {
        "message": "Sale recorded successfully",
        "sale_id": sale.id,
        "total_amount": sale.total_amount
    }

@router.get("/")
def get_sales(
    shop_id: int,
    db: Session = Depends(get_db)
):
    sales = db.query(Sale).filter(
        Sale.shop_id == shop_id
    ).order_by(
        Sale.id.desc()
    ).all()

    return [
        {
            "id": sale.id,
            "shop_id": sale.shop_id,
            "customer_id": sale.customer_id,
            "total_amount": sale.total_amount,
            "payment_method": sale.payment_method,
            "created_at": sale.created_at,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                }
                for item in sale.items
            ]
        }
        for sale in sales
    ]