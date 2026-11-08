import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from contextlib import asynccontextmanager
from app.database import transfer_inventory, get_inventory_movements, confirm_order_picks, update_order_status, get_order, create_order, confirm_inventory_picks, receive_inventory, pick_inventory, add_location, add_product, get_box_types, get_inventory_balances, get_locations, get_products, initialize_database
from app.packing import build_packing_plan
from app.palletizing import build_pallet_plan
from app.trucking import build_truck_plan
from app.picking import build_pick_plan
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
	initialize_database()
	yield

app = FastAPI(title="LogiFlow WMS", lifespan=lifespan)

STATIC_DIR = Path(__file__).resolve().parent / "static"

app.mount(
	"/static",
	StaticFiles(directory=STATIC_DIR),
	name="static",
)


@app.get("/", include_in_schema=False)
def home():
	return FileResponse(STATIC_DIR / "index.html")

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

class OrderCreateRequest(BaseModel):
	items: list[PackingItem] = Field(min_length=1)

class PalletBoxRequest(BaseModel):
	box_code: str
	gross_weight_kg: float = Field(gt=0)
	placements: list[dict]

class PalletizationRequest(BaseModel):
	boxes: list[PalletBoxRequest] = Field(min_length=1)

class StorageLocation(BaseModel):
	location_code: str = Field(
		pattern=r"^[A-Z]-(?:0[1-9]|[1-9][0-9])-(?:0[1-9]|[1-9][0-9])-(?:0[1-9]|[1-9][0-9])$"
	)

	@field_validator("location_code")
	@classmethod
	def check_location_limits(cls, value: str) -> str:
		_, rack, level, position = value.split("-")

		if int(rack) > 20:
			raise ValueError("Rack number must be between 01 and 20")
		if int(level) > 6:
			raise ValueError("Level number must be between 01 and 06")
		if int(position) > 10:
			raise ValueError("Position number must be between 01 and 10")

		return value

class InventoryBalance(BaseModel):
	sku: str
	location_code: str
	quantity: int = Field(ge=0)

class InventoryMovement(BaseModel):
	movement_id: int
	sku: str
	location_code: str
	destination_location_code: str | None = None
	movement_type: str
	quantity: int = Field(gt=0)
	order_id: int | None = None
	created_at: str

class InventoryPickRequest(BaseModel):
	sku: str
	location_code: str
	quantity: int = Field(gt=0)

class PickConfirmationRequest(BaseModel):
	picks: list[InventoryPickRequest] = Field(min_length=1)

class InventoryReceiveRequest(BaseModel):
	sku: str
	location_code: str
	quantity: int = Field(gt=0)

class InventoryTransferRequest(BaseModel):
	sku: str
	source_location_code: str
	destination_location_code: str
	quantity: int = Field(gt=0)

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

@app.get("/locations", response_model=list[StorageLocation])
def list_locations():
	return get_locations()

@app.get("/inventory/by-location", response_model=list[InventoryBalance])
def list_inventory_by_location():
	return get_inventory_balances()

@app.get(
	"/inventory/movements",
	response_model=list[InventoryMovement],
)
def list_inventory_movements():
	return get_inventory_movements()

@app.post("/inventory/pick")
def pick_inventory_item(request: InventoryPickRequest):
	picked = pick_inventory(
		request.sku,
		request.location_code,
		request.quantity,
	)

	if not picked:
		raise HTTPException(
			status_code=409,
			detail="No matching balance or insufficient stock at this location",
		)

	return {
		"sku": request.sku,
		"location_code": request.location_code,
		"quantity_picked": request.quantity,
		"status": "picked",
	}

@app.post("/inventory/receive")
def receive_inventory_item(request: InventoryReceiveRequest):
	try:
		received = receive_inventory(
			request.sku,
			request.location_code,
			request.quantity,
		)
	except sqlite3.IntegrityError:
		raise HTTPException(
			status_code=404,
			detail="Product or location not found",
		)
	if not received:
		raise HTTPException(
			status_code=409,
			detail="Location already contains a different SKU",
		)
	return {
		"sku": request.sku,
		"location_code": request.location_code,
		"quantity_received": request.quantity,
		"status": "received",
	}

@app.post("/inventory/transfer")
def transfer_inventory_item(request: InventoryTransferRequest):
	try:
		transferred = transfer_inventory(
			request.sku,
			request.source_location_code,
			request.destination_location_code,
			request.quantity,
		)
	except sqlite3.IntegrityError:
		raise HTTPException(
			status_code=404,
			detail="Product or location not found",
		)

	if not transferred:
		raise HTTPException(
			status_code=409,
			detail="Transfer blocked: insufficient source stock, same location, or destination occupied by another SKU",
		)

	return {
		"sku": request.sku,
		"source_location_code": request.source_location_code,
		"destination_location_code": request.destination_location_code,
		"quantity_transferred": request.quantity,
		"status": "transferred",
	}

@app.post("/outbound/pick/confirm")
def confirm_outbound_pick(request: PickConfirmationRequest):
	picks = [pick.model_dump() for pick in request.picks]

	confirmed = confirm_inventory_picks(picks)
	if not confirmed:
		raise HTTPException(
			status_code=409,
			detail="Stock changed or insufficient at one of the requested locations",
		)

	return {
		"status": "confirmed",
		"picks": picks,
	}

@app.post("/locations", response_model=StorageLocation, status_code=201)
def create_location(location: StorageLocation):
	try:
		add_location(location.location_code)
	except sqlite3.IntegrityError:
		raise HTTPException(status_code=409, detail="Location already exists")
	return location

@app.post("/products", response_model=Product, status_code=201)
def create_product(product: Product):
	product_data = product.model_dump()
	try:
		add_product(product_data)
	except sqlite3.IntegrityError:
		raise HTTPException(status_code=409, detail="SKU already exists")
	return product_data

@app.post("/orders", status_code=201)
def create_order_endpoint(request: OrderCreateRequest):
	try:
		order_id = create_order(
			[item.model_dump() for item in request.items]
		)
	except sqlite3.IntegrityError:
		raise HTTPException(
			status_code=404,
			detail="One or more products were not found",
		)

	return {
		"order_id": order_id,
		"status": "created",
	}

@app.get("/orders/{order_id}")
def get_order_endpoint(order_id: int):
	order = get_order(order_id)
	if order is None:
		raise HTTPException(
			status_code=404,
			detail=f"Order '{order_id}' not found",
		)
	return order

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

@app.post("/orders/{order_id}/plan")
def plan_saved_order(order_id: int):
	order = get_order(order_id)
	if order is None:
		raise HTTPException(
			status_code=404,
			detail=f"Order '{order_id}' not found",
		)

	if order["status"] != "created":
		raise HTTPException(
			status_code=409,
			detail="Only created orders can be planned",
		)

	request = PackingRequest(
		items=[
			PackingItem(**item)
			for item in order["items"]
		]
	)
	packing_products = prepare_packing_products(request)

	try:
		pick_plan = build_pick_plan(
			[(item.sku, item.quantity) for item in request.items],
			get_inventory_balances(),
		)
	except ValueError as error:
		raise HTTPException(status_code=409, detail=str(error))

	box_types = get_box_types()
	packing_plan = build_packing_plan(packing_products, box_types)
	pallet_plan = build_pallet_plan(packing_plan["boxes"], box_types)
	truck_plan = build_truck_plan(pallet_plan["pallets"])

	if not update_order_status(order_id, "created", "planned"):
		raise HTTPException(
			status_code=409,
			detail="Order status changed while planning",
		)

	return {
		"order_id": order_id,
		"status": "planned",
		"picking": pick_plan,
		"packing": packing_plan,
		"palletization": pallet_plan,
		"trucking": truck_plan,
	}

@app.post("/orders/{order_id}/confirm-pick")
def confirm_order_pick_endpoint(
	order_id: int,
	request: PickConfirmationRequest,
):
	order = get_order(order_id)
	if order is None:
		raise HTTPException(
			status_code=404,
			detail=f"Order '{order_id}' not found",
		)

	if order["status"] != "planned":
		raise HTTPException(
			status_code=409,
			detail="Only planned orders can be picked",
		)

	picks = [pick.model_dump() for pick in request.picks]

	if not confirm_order_picks(order_id, picks):
		raise HTTPException(
			status_code=409,
			detail="Pick quantities or available stock do not match the order",
		)

	return {
		"order_id": order_id,
		"status": "picked",
		"picks": picks,
	}

@app.post("/orders/{order_id}/ship")
def ship_order_endpoint(order_id: int):
	order = get_order(order_id)
	if order is None:
		raise HTTPException(
			status_code=404,
			detail=f"Order '{order_id}' not found",
		)

	if order["status"] != "picked":
		raise HTTPException(
			status_code=409,
			detail="Only picked orders can be shipped",
		)

	if not update_order_status(order_id, "picked", "shipped"):
		raise HTTPException(
			status_code=409,
			detail="Order status changed while shipping",
		)

	return {
		"order_id": order_id,
		"status": "shipped",
	}

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
	try:
		pick_plan = build_pick_plan(
			[(item.sku, item.quantity) for item in request.items],
			get_inventory_balances(),
		)
	except ValueError as error:
		raise HTTPException(status_code=409, detail=str(error))

	box_types = get_box_types()

	packing_plan = build_packing_plan(packing_products, box_types)
	pallet_plan = build_pallet_plan(packing_plan["boxes"], box_types)
	truck_plan = build_truck_plan(pallet_plan["pallets"])
	return {
		"packing": packing_plan,
		"palletization": pallet_plan,
		"trucking": truck_plan,
		"picking": pick_plan
	}