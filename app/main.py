import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from app.database import add_product, get_products, initialize_database

@asynccontextmanager
async def lifespan(app: FastAPI):
	initialize_database()
	yield

app = FastAPI(title="LogiFlow WMS", lifespan=lifespan)


@app.get("/health")
def health_check():
	return {"status": "ok"}

class Product(BaseModel):
	sku: str
	name: str
	category: str
	unit: str
	quantity_on_hand: int = Field(ge=0)
	reorder_point: int = Field(ge=0)

@app.get("/products", response_model=list[Product])
def list_products():
	return get_products()

@app.post("/products", response_model=Product, status_code=201)
def create_product(product: Product):
    product_data = product.model_dump()
    try:
        add_product(product_data)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="SKU already exists")
    return product_data
