from fastapi import FastAPI
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
