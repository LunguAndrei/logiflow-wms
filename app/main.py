import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from app.database import add_product, get_products, initialize_database
from app.database import add_product, get_box_types, get_products, initialize_database

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
	length_cm: float | None = Field(default=None, gt=0)
	width_cm: float | None = Field(default=None, gt=0)
	height_cm: float | None = Field(default=None, gt=0)
	weight_kg: float | None = Field(default=None, gt=0)

class BoxType(BaseModel):
	code: str
	capacity_liters: float = Field(gt=0)
	inner_length_cm: float = Field(gt=0)
	inner_width_cm: float = Field(gt=0)
	inner_height_cm: float = Field(gt=0)
	outer_length_cm: float = Field(gt=0)
	outer_width_cm: float = Field(gt=0)
	outer_height_cm: float = Field(gt=0)
	empty_weight_kg: float = Field(gt=0)
	max_payload_kg: float = Field(gt=0)

@app.get("/products", response_model=list[Product])
def list_products():
	return get_products()

@app.get("/products/low-stock", response_model=list[Product])
def list_low_stock_products():
	return [
		product
		for product in get_products()
		if product["quantity_on_hand"] <= product["reorder_point"]
	]

@app.get("/box-types", response_model=list[BoxType])
def list_box_types():
	return get_box_types()

@app.post("/products", response_model=Product, status_code=201)
def create_product(product: Product):
	product_data = product.model_dump()
	try:
		add_product(product_data)
	except sqlite3.IntegrityError:
		raise HTTPException(status_code=409, detail="SKU already exists")
	return product_data
