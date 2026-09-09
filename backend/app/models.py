from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    language = Column(String, default="English")

    products = relationship(
        "Product",
        back_populates="shop",
        cascade="all, delete-orphan"
    )

    customers = relationship(
        "Customer",
        back_populates="shop",
        cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    shop_id = Column(
        Integer,
        ForeignKey("shops.id"),
        nullable=False
    )

    brand = Column(String, nullable=True)
    name = Column(String, nullable=False)
    variant = Column(String, nullable=True)
    pack_size = Column(String, nullable=True)
    unit = Column(String, nullable=True)

    sku = Column(String, nullable=True)
    barcode = Column(String, nullable=True)

    purchase_price = Column(Float, nullable=True)
    selling_price = Column(Float, nullable=False)

    current_stock = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=5)

    supplier = Column(String, nullable=True)

    shop = relationship(
        "Shop",
        back_populates="products"
    )


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    shop_id = Column(
        Integer,
        ForeignKey("shops.id"),
        nullable=False
    )

    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)

    shop = relationship(
        "Shop",
        back_populates="customers"
    )
class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)

    shop_id = Column(
        Integer,
        ForeignKey("shops.id"),
        nullable=False
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=True
    )

    total_amount = Column(Float, nullable=False)

    payment_method = Column(
        String,
        nullable=False,
        default="cash"
    )

    created_at = Column(String, nullable=False)

    items = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan"
    )


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)

    sale_id = Column(
        Integer,
        ForeignKey("sales.id"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False)

    unit_price = Column(Float, nullable=False)

    total_price = Column(Float, nullable=False)

    sale = relationship(
        "Sale",
        back_populates="items"
    )

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)

    shop_id = Column(
        Integer,
        ForeignKey("shops.id"),
        nullable=False
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    amount = Column(Float, nullable=False)

    transaction_type = Column(
        String,
        nullable=False
    )

    note = Column(String, nullable=True)

    created_at = Column(
        String,
        nullable=False
    )
class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    shop_id = Column(
        Integer,
        ForeignKey("shops.id"),
        nullable=False
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=True
    )

    sale_id = Column(
        Integer,
        ForeignKey("sales.id"),
        nullable=True
    )

    invoice_number = Column(
        String,
        nullable=False
    )

    total_amount = Column(
        Float,
        nullable=False
    )

    payment_method = Column(
        String,
        nullable=False
    )

    status = Column(
        String,
        nullable=False,
        default="paid"
    )

    created_at = Column(
        String,
        nullable=False
    )