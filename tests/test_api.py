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