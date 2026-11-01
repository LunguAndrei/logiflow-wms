import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from app.database import add_product, get_box_types, get_products, initialize_database
from app.packing import build_packing_plan
from app.palletizing import build_pallet_plan

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

class PackingItem(BaseModel):
	sku: str
	quantity: int = Field(gt=0)

class PackingRequest(BaseModel):
	items: list[PackingItem] = Field(min_length=1)

class PalletBoxRequest(BaseModel):
	box_code: str
	gross_weight_kg: float = Field(gt=0)
	placements: list[dict]

class PalletizationRequest(BaseModel):
	boxes: list[PalletBoxRequest] = Field(min_length=1)

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

def prepare_packing_products(request: PackingRequest):
	products_by_sku = {
		product["sku"]: product
		for product in get_products()
	}

	requested_quantities = {}
	for item in request.items:
		requested_quantities[item.sku] = (
			requested_quantities.get(item.sku, 0) + item.quantity
		)

	packing_products = []
	for sku, quantity in requested_quantities.items():
		product = products_by_sku.get(sku)

		if product is None:
			raise HTTPException(
				status_code=404,
				detail=f"Product '{sku}' not found",
			)

		if quantity > product["quantity_on_hand"]:
			raise HTTPException(
				status_code=409,
				detail=f"Insufficient stock for '{sku}'",
			)

		required_fields = (
			"length_cm",
			"width_cm",
			"height_cm",
			"weight_kg",
		)
		if any(product[field] is None for field in required_fields):
			raise HTTPException(
				status_code=422,
				detail=f"Package dimensions are missing for '{sku}'",
			)

		packing_products.extend([product] * quantity)

	return packing_products

@app.post("/packing/plan")
def create_packing_plan(request: PackingRequest):
	packing_products = prepare_packing_products(request)
	box_types = get_box_types()
	return build_packing_plan(packing_products, box_types)

@app.post("/pallets/plan")
def create_palletization_plan(request: PalletizationRequest):
	box_types = get_box_types()
	known_codes = {box_type["code"] for box_type in box_types}

	packed_boxes = []
	for box in request.boxes:
		if box.box_code not in known_codes:
			raise HTTPException(
				status_code=404,
				detail=f"Box type '{box.box_code}' not found",
			)
		packed_boxes.append(box.model_dump())

	return build_pallet_plan(packed_boxes, box_types)

@app.post("/outbound/plan")
def create_outbound_plan(request: PackingRequest):
	packing_products = prepare_packing_products(request)
	box_types = get_box_types()

	packing_plan = build_packing_plan(packing_products, box_types)
	pallet_plan = build_pallet_plan(packing_plan["boxes"], box_types)

	return {
		"packing": packing_plan,
		"palletization": pallet_plan,
	}