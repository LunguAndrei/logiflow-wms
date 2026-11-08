import app.main as main
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError


def test_outbound_rejects_zero_quantity(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)

	with TestClient(main.app) as client:
		response = client.post(
			"/outbound/plan",
			json={"items": [{"sku": "CAB-050", "quantity": 0}]},
		)

	assert response.status_code == 422

def test_outbound_plan_returns_all_three_stages(monkeypatch):
	products = [{"sku": "TEST-001"}]
	box_types = [{"code": "BOX-TEST"}]

	packing_result = {"boxes": [{"box_code": "BOX-TEST"}]}
	pallet_result = {"pallets": [{"pallet_number": 1}]}
	truck_result = {"trucks": [{"truck_number": 1}]}
	pick_result = [
	{
		"sku": "TEST-001",
		"location_code": "A-01-01-01",
		"quantity": 1,
	}
	]

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(
		main, "prepare_packing_products", lambda request: products
	)
	monkeypatch.setattr(main, "get_box_types", lambda: box_types)
	monkeypatch.setattr(main, "get_inventory_balances", lambda: [])
	monkeypatch.setattr(
	main, "build_pick_plan", lambda requested_items, balances: pick_result,
	)
	monkeypatch.setattr(
		main, "build_packing_plan", lambda products, boxes: packing_result
	)
	monkeypatch.setattr(
		main, "build_pallet_plan", lambda boxes, box_types: pallet_result
	)
	monkeypatch.setattr(
		main, "build_truck_plan", lambda pallets: truck_result
	)

	with TestClient(main.app) as client:
		response = client.post(
			"/outbound/plan",
			json={"items": [{"sku": "TEST-001", "quantity": 1}]},
		)

	assert response.status_code == 200
	assert response.json() == {
		"packing": packing_result,
		"palletization": pallet_result,
		"trucking": truck_result,
		"picking": pick_result,
	}

@pytest.mark.parametrize(
	"location_code",
	[
		"A-21-01-01",
		"A-03-07-01",
		"A-03-02-11",
	],
)
def test_storage_location_rejects_numbers_over_limits(location_code):
	with pytest.raises(ValidationError):
		main.StorageLocation(location_code=location_code)

def test_create_location_returns_201(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "add_location", lambda location_code: None)

	with TestClient(main.app) as client:
		response = client.post(
			"/locations",
			json={"location_code": "B-01-01-01"},
		)

	assert response.status_code == 201
	assert response.json() == {"location_code": "B-01-01-01"}


def test_duplicate_location_returns_409(monkeypatch):
	def raise_duplicate_error(location_code):
		raise main.sqlite3.IntegrityError("duplicate location")

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "add_location", raise_duplicate_error)

	with TestClient(main.app) as client:
		response = client.post(
			"/locations",
			json={"location_code": "B-01-01-01"},
		)

	assert response.status_code == 409
	assert response.json()["detail"] == "Location already exists"

def test_inventory_pick_returns_success(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(
		main,
		"pick_inventory",
		lambda sku, location_code, quantity: True,
	)

	with TestClient(main.app) as client:
		response = client.post(
			"/inventory/pick",
			json={
				"sku": "ADH-001",
				"location_code": "A-01-01-01",
				"quantity": 2,
			},
		)

	assert response.status_code == 200
	assert response.json() == {
		"sku": "ADH-001",
		"location_code": "A-01-01-01",
		"quantity_picked": 2,
		"status": "picked",
	}


def test_inventory_pick_returns_409_when_stock_is_insufficient(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(
		main,
		"pick_inventory",
		lambda sku, location_code, quantity: False,
	)

	with TestClient(main.app) as client:
		response = client.post(
			"/inventory/pick",
			json={
				"sku": "ADH-001",
				"location_code": "A-01-01-01",
				"quantity": 14,
			},
		)

	assert response.status_code == 409
	assert response.json()["detail"] == (
		"No matching balance or insufficient stock at this location"
	)

def test_inventory_receive_returns_success(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(
		main,
		"receive_inventory",
		lambda sku, location_code, quantity: True,
	)

	with TestClient(main.app) as client:
		response = client.post(
			"/inventory/receive",
			json={
				"sku": "ADH-001",
				"location_code": "A-01-01-01",
				"quantity": 2,
			},
		)

	assert response.status_code == 200
	assert response.json() == {
		"sku": "ADH-001",
		"location_code": "A-01-01-01",
		"quantity_received": 2,
		"status": "received",
	}


def test_inventory_receive_returns_404_when_reference_is_missing(monkeypatch):
	def raise_integrity_error(sku, location_code, quantity):
		raise main.sqlite3.IntegrityError("foreign key constraint failed")

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "receive_inventory", raise_integrity_error)

	with TestClient(main.app) as client:
		response = client.post(
			"/inventory/receive",
			json={
				"sku": "MISSING",
				"location_code": "A-01-01-01",
				"quantity": 2,
			},
		)

	assert response.status_code == 404
	assert response.json()["detail"] == "Product or location not found"

def test_outbound_pick_confirmation_returns_success(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "confirm_inventory_picks", lambda picks: True)

	with TestClient(main.app) as client:
		response = client.post(
			"/outbound/pick/confirm",
			json={
				"picks": [
					{
						"sku": "ADH-001",
						"location_code": "A-01-01-01",
						"quantity": 2,
					},
					{
						"sku": "ANCHOR-01",
						"location_code": "A-01-01-02",
						"quantity": 1,
					},
				],
			},
		)

	assert response.status_code == 200
	assert response.json()["status"] == "confirmed"
	assert len(response.json()["picks"]) == 2


def test_outbound_pick_confirmation_returns_409_when_stock_changed(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "confirm_inventory_picks", lambda picks: False)

	with TestClient(main.app) as client:
		response = client.post(
			"/outbound/pick/confirm",
			json={
				"picks": [
					{
						"sku": "ADH-001",
						"location_code": "A-01-01-01",
						"quantity": 2,
					},
				],
			},
		)

	assert response.status_code == 409
	assert response.json()["detail"] == (
		"Stock changed or insufficient at one of the requested locations"
	)

def test_create_order_returns_201(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "create_order", lambda items: 123)

	with TestClient(main.app) as client:
		response = client.post(
			"/orders",
			json={
				"items": [
					{"sku": "ADH-001", "quantity": 2},
				],
			},
		)

	assert response.status_code == 201
	assert response.json() == {
		"order_id": 123,
		"status": "created",
	}


def test_create_order_returns_404_for_unknown_sku(monkeypatch):
	def raise_integrity_error(items):
		raise main.sqlite3.IntegrityError("foreign key constraint failed")

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "create_order", raise_integrity_error)

	with TestClient(main.app) as client:
		response = client.post(
			"/orders",
			json={
				"items": [
					{"sku": "MISSING-SKU", "quantity": 1},
				],
			},
		)

	assert response.status_code == 404
	assert response.json()["detail"] == "One or more products were not found"

def test_get_order_returns_order(monkeypatch):
	order = {
		"order_id": 123,
		"status": "created",
		"created_at": "2026-11-08 12:00:00",
		"items": [{"sku": "ADH-001", "quantity": 2}],
	}

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "get_order", lambda order_id: order)

	with TestClient(main.app) as client:
		response = client.get("/orders/123")

	assert response.status_code == 200
	assert response.json() == order


def test_get_order_returns_404_when_order_does_not_exist(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "get_order", lambda order_id: None)

	with TestClient(main.app) as client:
		response = client.get("/orders/999")

	assert response.status_code == 404
	assert response.json()["detail"] == "Order '999' not found"

def test_plan_saved_order_returns_plan(monkeypatch):
	order = {
		"order_id": 123,
		"status": "created",
		"items": [{"sku": "ADH-001", "quantity": 1}],
	}
	pick_result = [
		{
			"sku": "ADH-001",
			"location_code": "A-01-01-01",
			"quantity": 1,
		}
	]

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "get_order", lambda order_id: order)
	monkeypatch.setattr(main, "prepare_packing_products", lambda request: [])
	monkeypatch.setattr(main, "get_inventory_balances", lambda: [])
	monkeypatch.setattr(
		main,
		"build_pick_plan",
		lambda requested_items, balances: pick_result,
	)
	monkeypatch.setattr(main, "get_box_types", lambda: [])
	monkeypatch.setattr(
		main, "build_packing_plan", lambda products, boxes: {"boxes": []}
	)
	monkeypatch.setattr(
		main, "build_pallet_plan", lambda boxes, box_types: {"pallets": []}
	)
	monkeypatch.setattr(
		main, "build_truck_plan", lambda pallets: {"trucks": []}
	)
	monkeypatch.setattr(
		main, "update_order_status", lambda order_id, old, new: True
	)

	with TestClient(main.app) as client:
		response = client.post("/orders/123/plan")

	assert response.status_code == 200
	assert response.json()["status"] == "planned"
	assert response.json()["picking"] == pick_result


def test_plan_saved_order_rejects_already_planned_order(monkeypatch):
	order = {
		"order_id": 123,
		"status": "planned",
		"items": [{"sku": "ADH-001", "quantity": 1}],
	}

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "get_order", lambda order_id: order)

	with TestClient(main.app) as client:
		response = client.post("/orders/123/plan")

	assert response.status_code == 409
	assert response.json()["detail"] == "Only created orders can be planned"

def test_confirm_order_pick_returns_picked_status(monkeypatch):
	order = {"order_id": 123, "status": "planned"}
	picks = [
		{
			"sku": "ADH-001",
			"location_code": "A-01-01-01",
			"quantity": 2,
		},
	]

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "get_order", lambda order_id: order)
	monkeypatch.setattr(
		main,
		"confirm_order_picks",
		lambda order_id, picks: True,
	)

	with TestClient(main.app) as client:
		response = client.post(
			"/orders/123/confirm-pick",
			json={"picks": picks},
		)

	assert response.status_code == 200
	assert response.json() == {
		"order_id": 123,
		"status": "picked",
		"picks": picks,
	}


def test_confirm_order_pick_returns_409_when_pick_fails(monkeypatch):
	order = {"order_id": 123, "status": "planned"}

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "get_order", lambda order_id: order)
	monkeypatch.setattr(
		main,
		"confirm_order_picks",
		lambda order_id, picks: False,
	)

	with TestClient(main.app) as client:
		response = client.post(
			"/orders/123/confirm-pick",
			json={
				"picks": [
					{
						"sku": "ADH-001",
						"location_code": "A-01-01-01",
						"quantity": 2,
					},
				],
			},
		)

	assert response.status_code == 409
	assert response.json()["detail"] == (
		"Pick quantities or available stock do not match the order"
	)

def test_ship_order_changes_status_to_shipped(monkeypatch):
	order = {"order_id": 123, "status": "picked"}

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "get_order", lambda order_id: order)
	monkeypatch.setattr(
		main,
		"update_order_status",
		lambda order_id, expected_status, new_status: True,
	)

	with TestClient(main.app) as client:
		response = client.post("/orders/123/ship")

	assert response.status_code == 200
	assert response.json() == {
		"order_id": 123,
		"status": "shipped",
	}


def test_ship_order_rejects_order_not_yet_picked(monkeypatch):
	order = {"order_id": 123, "status": "planned"}

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(main, "get_order", lambda order_id: order)

	with TestClient(main.app) as client:
		response = client.post("/orders/123/ship")

	assert response.status_code == 409
	assert response.json()["detail"] == "Only picked orders can be shipped"

def test_inventory_transfer_returns_success(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(
		main,
		"transfer_inventory",
		lambda sku, source_location_code, destination_location_code, quantity: True,
	)

	with TestClient(main.app) as client:
		response = client.post(
			"/inventory/transfer",
			json={
				"sku": "ADH-001",
				"source_location_code": "A-01-01-01",
				"destination_location_code": "A-01-01-02",
				"quantity": 2,
			},
		)

	assert response.status_code == 200
	assert response.json() == {
		"sku": "ADH-001",
		"source_location_code": "A-01-01-01",
		"destination_location_code": "A-01-01-02",
		"quantity_transferred": 2,
		"status": "transferred",
	}

def test_inventory_transfer_returns_409_when_transfer_cannot_be_done(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(
		main,
		"transfer_inventory",
		lambda sku, source_location_code, destination_location_code, quantity: False,
	)

	with TestClient(main.app) as client:
		response = client.post(
			"/inventory/transfer",
			json={
				"sku": "ADH-001",
				"source_location_code": "A-01-01-01",
				"destination_location_code": "A-01-01-02",
				"quantity": 2,
			},
		)

	assert response.status_code == 409
	assert response.json()["detail"] == (
		"Transfer blocked: insufficient source stock, same location, or destination occupied by another SKU"
	)

def test_inventory_transfer_returns_404_when_reference_is_missing(monkeypatch):
	def raise_integrity_error(
		sku,
		source_location_code,
		destination_location_code,
		quantity,
	):
		raise main.sqlite3.IntegrityError("foreign key constraint failed")

	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(
		main,
		"transfer_inventory",
		raise_integrity_error,
	)

	with TestClient(main.app) as client:
		response = client.post(
			"/inventory/transfer",
			json={
				"sku": "ADH-001",
				"source_location_code": "A-01-01-01",
				"destination_location_code": "MISSING",
				"quantity": 2,
			},
		)

	assert response.status_code == 404
	assert response.json()["detail"] == "Product or location not found"

def test_inventory_transfer_rejects_zero_quantity(monkeypatch):
	monkeypatch.setattr(main, "initialize_database", lambda: None)

	with TestClient(main.app) as client:
		response = client.post(
			"/inventory/transfer",
			json={
				"sku": "ADH-001",
				"source_location_code": "A-01-01-01",
				"destination_location_code": "A-01-01-02",
				"quantity": 0,
			},
		)

	assert response.status_code == 422

def test_inventory_receive_returns_409_when_location_has_another_sku(
	monkeypatch,
):
	monkeypatch.setattr(main, "initialize_database", lambda: None)
	monkeypatch.setattr(
		main,
		"receive_inventory",
		lambda sku, location_code, quantity: False,
	)

	with TestClient(main.app) as client:
		response = client.post(
			"/inventory/receive",
			json={
				"sku": "ADH-001",
				"location_code": "A-01-01-02",
				"quantity": 1,
			},
		)

	assert response.status_code == 409
	assert response.json()["detail"] == (
		"Location already contains a different SKU"
	)