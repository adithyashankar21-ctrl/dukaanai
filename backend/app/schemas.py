from typing import Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    shop_id: int

    brand: Optional[str] = None
    name: str
    variant: Optional[str] = None
    pack_size: Optional[str] = None
    unit: Optional[str] = None

    sku: Optional[str] = None
    barcode: Optional[str] = None

    purchase_price: Optional[float] = None
    selling_price: float

    current_stock: int = 0
    minimum_stock: int = 5

    supplier: Optional[str] = None


class ProductResponse(ProductCreate):
    id: int

    class Config:
        from_attributes = True
        
class ShopCreate(BaseModel):
    name: str
    owner_name: str
    phone: Optional[str] = None
    location: Optional[str] = None
    language: str = "English"


class ShopResponse(ShopCreate):
    id: int

    class Config:
        from_attributes = True

class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class SaleCreate(BaseModel):
    shop_id: int
    customer_id: Optional[int] = None
    payment_method: str = "cash"
    items: list[SaleItemCreate]

class CustomerCreate(BaseModel):
    shop_id: int
    name: str
    phone: Optional[str] = None


class CustomerResponse(CustomerCreate):
    id: int

    class Config:
        from_attributes = True

class CreditTransactionCreate(BaseModel):
    shop_id: int
    customer_id: int
    amount: float
    transaction_type: str
    note: Optional[str] = None
    
class InvoiceCreate(BaseModel):
    shop_id: int
    customer_id: Optional[int] = None
    sale_id: Optional[int] = None
    total_amount: float
    payment_method: str
    status: str = "paid"


class InvoiceResponse(BaseModel):
    id: int
    shop_id: int
    customer_id: Optional[int]
    sale_id: Optional[int]
    invoice_number: str
    total_amount: float
    payment_method: str
    status: str
    created_at: str

    class Config:
        from_attributes = True