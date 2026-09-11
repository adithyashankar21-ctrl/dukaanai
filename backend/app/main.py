from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import invoices
from .database import Base, engine
from . import models
from .routes import products, shops, sales, customers, credit, stock_advisor
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="DukaanAI API",
    description="AI-powered operating system for Indian small businesses",
    version="0.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(shops.router)
app.include_router(sales.router)
app.include_router(customers.router)
app.include_router(credit.router)
app.include_router(invoices.router)
app.include_router(stock_advisor.router)

@app.get("/")
def root():
    return {
        "message": "DukaanAI API is running",
        "version": "0.1.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }