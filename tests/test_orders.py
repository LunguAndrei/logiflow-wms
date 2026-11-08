import sqlite3

import pytest

import app.database as database


@pytest.fixture
def fresh_database(tmp_path, monkeypatch):
	monkeypatch.setattr(
		database,
		"DATABASE_PATH",
		tmp_path / "orders-test.db",
	)
	database.initialize_database()


def test_create_order_saves_header_and_aggregates_skus(fresh_database):
	order_id = database.create_order([
		{"sku": "ADH-001", "quantity": 2},
		{"sku": "ADH-001", "quantity": 3},
		{"sku": "ANCHOR-01", "quantity": 1},
	])

	connection = database.connect_database()
	try:
		order = connection.execute(
			"SELECT status FROM orders WHERE order_id = ?",
			(order_id,),
		).fetchone()
		items = connection.execute(
			"""
			SELECT sku, quantity
			FROM order_items
			WHERE order_id = ?
			ORDER BY sku
			""",
			(order_id,),
		).fetchall()
	finally:
		connection.close()

	assert order[0] == "created"
	assert dict(items) == {
		"ADH-001": 5,
		"ANCHOR-01": 1,
	}
	saved_order = database.get_order(order_id)

	assert saved_order["order_id"] == order_id
	assert saved_order["status"] == "created"
	assert saved_order["items"] == [
		{"sku": "ADH-001", "quantity": 5},
		{"sku": "ANCHOR-01", "quantity": 1},
	]


def test_create_order_rolls_back_if_product_does_not_exist(fresh_database):
	with pytest.raises(sqlite3.IntegrityError):
		database.create_order([
			{"sku": "MISSING-SKU", "quantity": 1},
		])

	connection = database.connect_database()
	try:
		order_count = connection.execute(
			"SELECT COUNT(*) FROM orders"
		).fetchone()[0]
	finally:
		connection.close()

	assert order_count == 0

def test_order_status_changes_only_from_expected_state(fresh_database):
	order_id = database.create_order([
		{"sku": "ADH-001", "quantity": 1},
	])

	assert database.update_order_status(
		order_id,
		"created",
		"planned",
	) is True
	assert database.get_order(order_id)["status"] == "planned"

	assert database.update_order_status(
		order_id,
		"created",
		"picked",
	) is False
	assert database.get_order(order_id)["status"] == "planned"

def test_confirm_order_picks_updates_stock_and_status(fresh_database):
	order_id = database.create_order([
		{"sku": "ADH-001", "quantity": 2},
		{"sku": "ANCHOR-01", "quantity": 1},
	])
	assert database.update_order_status(
		order_id,
		"created",
		"planned",
	)

	balances = database.get_inventory_balances()
	adh_balance = next(item for item in balances if item["sku"] == "ADH-001")
	anchor_balance = next(item for item in balances if item["sku"] == "ANCHOR-01")
	products = {
		item["sku"]: item["quantity_on_hand"]
		for item in database.get_products()
	}

	picks = [
		{
			"sku": "ADH-001",
			"location_code": adh_balance["location_code"],
			"quantity": 2,
		},
		{
			"sku": "ANCHOR-01",
			"location_code": anchor_balance["location_code"],
			"quantity": 1,
		},
	]

	assert database.confirm_order_picks(order_id, picks) is True
	assert database.get_order(order_id)["status"] == "picked"

	updated_balances = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}
	updated_products = {
		item["sku"]: item["quantity_on_hand"]
		for item in database.get_products()
	}

	assert updated_balances[("ADH-001", adh_balance["location_code"])] == adh_balance["quantity"] - 2
	assert updated_balances[("ANCHOR-01", anchor_balance["location_code"])] == anchor_balance["quantity"] - 1
	assert updated_products["ADH-001"] == products["ADH-001"] - 2
	assert updated_products["ANCHOR-01"] == products["ANCHOR-01"] - 1
	movements = database.get_inventory_movements()

	assert len(movements) == 2
	assert all(movement["movement_type"] == "pick" for movement in movements)
	assert all(movement["order_id"] == order_id for movement in movements)

def test_confirm_order_picks_rolls_back_when_a_location_fails(fresh_database):
	order_id = database.create_order([
		{"sku": "ADH-001", "quantity": 2},
	])
	assert database.update_order_status(
		order_id,
		"created",
		"planned",
	)

	balance = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ADH-001"
	)
	product = next(
		item
		for item in database.get_products()
		if item["sku"] == "ADH-001"
	)

	picks = [
		{
			"sku": "ADH-001",
			"location_code": balance["location_code"],
			"quantity": 1,
		},
		{
			"sku": "ADH-001",
			"location_code": "Z-99-99-99",
			"quantity": 1,
		},
	]

	assert database.confirm_order_picks(order_id, picks) is False
	assert database.get_order(order_id)["status"] == "planned"

	updated_balance = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ADH-001"
	)
	updated_product = next(
		item
		for item in database.get_products()
		if item["sku"] == "ADH-001"
	)

	assert updated_balance["quantity"] == balance["quantity"]
	assert updated_product["quantity_on_hand"] == product["quantity_on_hand"]