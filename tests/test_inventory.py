import pytest

import app.database as database


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
	monkeypatch.setattr(
		database,
		"DATABASE_PATH",
		tmp_path / "inventory-test.db",
	)
	database.initialize_database()


def test_confirm_inventory_picks_updates_all_lines(isolated_database):
	balances = {
		(balance["sku"], balance["location_code"]): balance["quantity"]
		for balance in database.get_inventory_balances()
	}
	products = {
		product["sku"]: product["quantity_on_hand"]
		for product in database.get_products()
	}

	adh_location = next(
		location
		for sku, location in balances
		if sku == "ADH-001"
	)
	anchor_location = next(
		location
		for sku, location in balances
		if sku == "ANCHOR-01"
	)

	picks = [
		{
			"sku": "ADH-001",
			"location_code": adh_location,
			"quantity": 1,
		},
		{
			"sku": "ANCHOR-01",
			"location_code": anchor_location,
			"quantity": 1,
		},
	]

	assert database.confirm_inventory_picks(picks) is True

	updated_balances = {
		(balance["sku"], balance["location_code"]): balance["quantity"]
		for balance in database.get_inventory_balances()
	}
	updated_products = {
		product["sku"]: product["quantity_on_hand"]
		for product in database.get_products()
	}

	assert updated_balances[("ADH-001", adh_location)] == balances[("ADH-001", adh_location)] - 1
	assert updated_balances[("ANCHOR-01", anchor_location)] == balances[("ANCHOR-01", anchor_location)] - 1
	assert updated_products["ADH-001"] == products["ADH-001"] - 1
	assert updated_products["ANCHOR-01"] == products["ANCHOR-01"] - 1
	movements = database.get_inventory_movements()

	assert len(movements) == len(picks)
	assert all(movement["movement_type"] == "pick" for movement in movements)


def test_confirm_inventory_picks_rolls_back_all_lines_when_one_fails(isolated_database):
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
			"quantity": 2,
		},
		{
			"sku": "ADH-001",
			"location_code": "Z-99-99-99",
			"quantity": 1,
		},
	]

	assert database.confirm_inventory_picks(picks) is False

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
	assert database.get_inventory_movements() == []

def test_receive_inventory_records_movement(isolated_database):
	balance = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ADH-001"
	)

	assert database.receive_inventory(
		"ADH-001",
		balance["location_code"],
		2,
	) is True

	movements = database.get_inventory_movements()

	assert len(movements) == 1
	assert movements[0]["sku"] == "ADH-001"
	assert movements[0]["location_code"] == balance["location_code"]
	assert movements[0]["movement_type"] == "receive"
	assert movements[0]["quantity"] == 2
	assert movements[0]["order_id"] is None

def test_pick_inventory_records_movement(isolated_database):
	balance = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ADH-001"
	)

	assert database.pick_inventory(
		"ADH-001",
		balance["location_code"],
		1,
	) is True

	movement = database.get_inventory_movements()[0]
	assert movement["sku"] == "ADH-001"
	assert movement["location_code"] == balance["location_code"]
	assert movement["movement_type"] == "pick"
	assert movement["quantity"] == 1
	assert movement["order_id"] is None