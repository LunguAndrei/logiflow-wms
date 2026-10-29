from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="LogiFlow WMS")


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

products = [
	{
		"sku": "BRG-001",
		"name": "Industrial bearing",
		"category": "Components",
		"unit": "piece",
		"quantity_on_hand": 120,
		"reorder_point": 30,
	},
	{
		"sku": "CAB-002",
		"name": "Electrical cable",
		"category": "Electrical",
		"unit": "meter",
		"quantity_on_hand": 500,
		"reorder_point": 100,
	},
	{
		"sku": "GLV-003",
		"name": "Safety gloves",
		"category": "PPE",
		"unit": "pair",
		"quantity_on_hand": 200,
		"reorder_point": 40,
	},
]

@app.get("/products", response_model=list[Product])
def list_products():
	return products

@app.post("/products", response_model=Product, status_code=201)
def create_product(product: Product):
	if any(item["sku"] == product.sku for item in products):
		raise HTTPException(status_code=409, detail="SKU already exists")

	product_data = product.model_dump()
	products.append(product_data)
	return product_data
