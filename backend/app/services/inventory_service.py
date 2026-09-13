from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import Product, Shop, StockAdjustment

VALID_ADJUSTMENT_TYPES = ("restock", "damage", "correction")

# Removals at or beyond this size should be confirmed before they happen —
# enforced here in code rather than left to the AI model's judgement, since
# an LLM won't reliably self-police a "confirm first" instruction every time.
LARGE_REMOVAL_ABS_UNITS = 10
LARGE_REMOVAL_FRACTION = 0.5  # of current stock


class ConfirmationRequired(Exception):
    """A risky action was attempted without confirmation. Retry the same
    call with confirmed=True once the caller has actually confirmed."""


def _is_large_removal(product: Product, delta: int) -> bool:
    if delta >= 0:
        return False
    magnitude = abs(delta)
    if magnitude >= LARGE_REMOVAL_ABS_UNITS:
        return True
    if product.current_stock > 0 and magnitude >= product.current_stock * LARGE_REMOVAL_FRACTION:
        return True
    return False


def display_name(product: Product) -> str:
    """brand + name + variant + pack_size, e.g. 'Nestle Maggi Masala 70g'."""
    parts = [product.brand, product.name, product.variant, product.pack_size]
    return " ".join(p for p in parts if p)


def search_products(db: Session, shop_id: int, query: str | None = None, limit: int = 15) -> list[Product]:
    q = db.query(Product).filter(Product.shop_id == shop_id)

    if query and query.strip():
        like = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Product.name.ilike(like),
                Product.brand.ilike(like),
                Product.variant.ilike(like),
                Product.pack_size.ilike(like),
                Product.sku.ilike(like),
                Product.barcode.ilike(like),
            )
        )

    return q.order_by(Product.id).limit(limit).all()


def list_products(db: Session, shop_id: int) -> list[Product]:
    return db.query(Product).filter(Product.shop_id == shop_id).order_by(Product.id).all()


def get_product(db: Session, shop_id: int, product_id: int) -> Product:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.shop_id == shop_id
    ).first()

    if not product:
        raise LookupError(f"Product {product_id} not found")

    return product


def get_product_by_barcode(db: Session, shop_id: int, barcode: str) -> Product:
    barcode = (barcode or "").strip()
    if not barcode:
        raise ValueError("Barcode is required")

    product = db.query(Product).filter(
        Product.shop_id == shop_id,
        Product.barcode == barcode,
    ).first()

    if not product:
        raise LookupError(f"No product with barcode '{barcode}'")

    return product


def create_product(
    db: Session,
    shop_id: int,
    name: str,
    brand: str | None = None,
    variant: str | None = None,
    pack_size: str | None = None,
    unit: str | None = None,
    sku: str | None = None,
    barcode: str | None = None,
    purchase_price: float | None = None,
    selling_price: float | None = None,
    current_stock: int = 0,
    minimum_stock: int = 5,
    supplier: str | None = None,
) -> Product:
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise LookupError("Shop not found")

    if not name or not name.strip():
        raise ValueError("Product name is required")

    if selling_price is None:
        raise ValueError("Selling price is required")

    if selling_price < 0:
        raise ValueError("Selling price cannot be negative")

    product = Product(
        shop_id=shop_id,
        brand=brand,
        name=name.strip(),
        variant=variant,
        pack_size=pack_size,
        unit=unit,
        sku=sku,
        barcode=barcode,
        purchase_price=purchase_price,
        selling_price=selling_price,
        current_stock=current_stock or 0,
        minimum_stock=minimum_stock if minimum_stock is not None else 5,
        supplier=supplier,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def adjust_stock(
    db: Session,
    shop_id: int,
    product_id: int,
    delta: int,
    adjustment_type: str = "correction",
    reason: str | None = None,
    supplier: str | None = None,
    unit_cost: float | None = None,
    confirmed: bool = False,
) -> dict:
    if delta == 0:
        raise ValueError("Adjustment quantity must not be zero")

    if adjustment_type not in VALID_ADJUSTMENT_TYPES:
        raise ValueError(f"adjustment_type must be one of {VALID_ADJUSTMENT_TYPES}")

    product = get_product(db, shop_id, product_id)

    new_stock = product.current_stock + delta
    if new_stock < 0:
        raise ValueError(
            f"Cannot remove {abs(delta)} units of {display_name(product)} — "
            f"only {product.current_stock} in stock"
        )

    if not confirmed and _is_large_removal(product, delta):
        raise ConfirmationRequired(
            f"Removing {abs(delta)} units of {display_name(product)} (currently "
            f"{product.current_stock} in stock) is a big change — confirm before I proceed."
        )

    product.current_stock = new_stock

    if unit_cost is not None:
        product.purchase_price = unit_cost

    if supplier:
        product.supplier = supplier

    adjustment = StockAdjustment(
        shop_id=shop_id,
        product_id=product_id,
        delta=delta,
        adjustment_type=adjustment_type,
        reason=reason,
        supplier=supplier,
        unit_cost=unit_cost,
        created_at=datetime.now().isoformat(),
    )

    db.add(adjustment)
    db.commit()
    db.refresh(product)
    db.refresh(adjustment)

    return {"product": product, "adjustment": adjustment}


def update_price(
    db: Session,
    shop_id: int,
    product_id: int,
    selling_price: float | None = None,
    purchase_price: float | None = None,
    selling_price_delta: float | None = None,
    purchase_price_delta: float | None = None,
) -> Product:
    product = get_product(db, shop_id, product_id)

    if selling_price is None and selling_price_delta is not None:
        selling_price = round(product.selling_price + selling_price_delta, 2)

    if purchase_price is None and purchase_price_delta is not None:
        purchase_price = round((product.purchase_price or 0) + purchase_price_delta, 2)

    if selling_price is None and purchase_price is None:
        raise ValueError("Provide a new price or a price change amount")

    if selling_price is not None:
        if selling_price < 0:
            raise ValueError("Selling price cannot be negative")
        product.selling_price = selling_price

    if purchase_price is not None:
        if purchase_price < 0:
            raise ValueError("Purchase price cannot be negative")
        product.purchase_price = purchase_price

    db.commit()
    db.refresh(product)

    return product


def list_adjustments(
    db: Session,
    shop_id: int,
    product_id: int | None = None,
    limit: int = 50,
) -> list[StockAdjustment]:
    q = db.query(StockAdjustment).filter(StockAdjustment.shop_id == shop_id)

    if product_id:
        q = q.filter(StockAdjustment.product_id == product_id)

    return q.order_by(StockAdjustment.id.desc()).limit(limit).all()
