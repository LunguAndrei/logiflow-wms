import pytest
import sqlite3
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

def test_initialize_database_migrates_old_movement_table(isolated_database):
	balance = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ADH-001"
	)
	assert database.receive_inventory(
		"ADH-001",
		balance["location_code"],
		1,
	) is True

	connection = database.connect_database()
	try:
		connection.execute(
			"ALTER TABLE inventory_movements RENAME TO movements_new_schema"
		)
		connection.execute(
			"""
			CREATE TABLE inventory_movements (
				movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
				sku TEXT NOT NULL,
				location_code TEXT NOT NULL,
				movement_type TEXT NOT NULL
					CHECK (movement_type IN ('receive', 'pick')),
				quantity INTEGER NOT NULL CHECK (quantity > 0),
				order_id INTEGER,
				created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)
		connection.execute(
			"""
			INSERT INTO inventory_movements (
				movement_id, sku, location_code, movement_type,
				quantity, order_id, created_at
			)
			SELECT
				movement_id, sku, location_code, movement_type,
				quantity, order_id, created_at
			FROM movements_new_schema
			"""
		)
		connection.execute("DROP TABLE movements_new_schema")
		connection.commit()
	finally:
		connection.close()

	database.initialize_database()

	movement = database.get_inventory_movements()[0]
	assert movement["sku"] == "ADH-001"
	assert movement["movement_type"] == "receive"
	assert movement["quantity"] == 1

	connection = database.connect_database()
	try:
		columns = {
			row[1]
			for row in connection.execute(
				"PRAGMA table_info(inventory_movements)"
			)
		}
	finally:
		connection.close()

	assert "destination_location_code" in columns

def test_transfer_inventory_moves_stock_and_records_movement(isolated_database):
	balances_before = database.get_inventory_balances()

	source_balance = next(
		item
		for item in balances_before
		if item["sku"] == "ADH-001"
	)
	source_location = source_balance["location_code"]

	destination_location = "Z-20-06-09"
	database.add_location(destination_location)

	occupied_locations = {
		item["location_code"]
		for item in balances_before
		if item["quantity"] > 0
	}
	destination_location = next(
		item["location_code"]
		for item in database.get_locations()
		if item["location_code"] not in occupied_locations
	)

	source_quantity_before = source_balance["quantity"]
	product_before = next(
		item
		for item in database.get_products()
		if item["sku"] == "ADH-001"
	)["quantity_on_hand"]

	assert database.transfer_inventory(
		"ADH-001",
		source_location,
		destination_location,
		2,
	) is True

	balances_after = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}
	product_after = next(
		item
		for item in database.get_products()
		if item["sku"] == "ADH-001"
	)["quantity_on_hand"]

	assert balances_after[("ADH-001", source_location)] == source_quantity_before - 2
	assert balances_after[("ADH-001", destination_location)] == 2
	assert product_after == product_before

	movement = database.get_inventory_movements()[0]
	assert movement["movement_type"] == "transfer"
	assert movement["location_code"] == source_location
	assert movement["destination_location_code"] == destination_location
	assert movement["quantity"] == 2

def test_transfer_inventory_rolls_back_when_source_stock_is_insufficient(
	isolated_database,
):
	balances_before = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}
	source_balance = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ADH-001"
	)

	destination_location = next(
		item["location_code"]
		for item in database.get_locations()
		if item["location_code"] != source_balance["location_code"]
	)

	assert database.transfer_inventory(
		"ADH-001",
		source_balance["location_code"],
		destination_location,
		source_balance["quantity"] + 1,
	) is False

	balances_after = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}

	assert balances_after == balances_before
	assert database.get_inventory_movements() == []

def test_transfer_inventory_rolls_back_when_destination_is_missing(
	isolated_database,
):
	source_balance = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ADH-001"
	)
	balances_before = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}

	with pytest.raises(sqlite3.IntegrityError):
		database.transfer_inventory(
			"ADH-001",
			source_balance["location_code"],
			"Z-99-99-99",
			1,
		)

	balances_after = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}

	assert balances_after == balances_before
	assert database.get_inventory_movements() == []

def test_transfer_inventory_rejects_same_location(isolated_database):
	source_balance = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ADH-001"
	)
	balances_before = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}

	assert database.transfer_inventory(
		"ADH-001",
		source_balance["location_code"],
		source_balance["location_code"],
		1,
	) is False

	balances_after = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}

	assert balances_after == balances_before
	assert database.get_inventory_movements() == []

def test_transfer_inventory_rejects_destination_with_another_sku(
	isolated_database,
):
	balances_before = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}
	source_balance = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ADH-001"
	)
	occupied_destination = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ANCHOR-01"
	)

	assert database.transfer_inventory(
		"ADH-001",
		source_balance["location_code"],
		occupied_destination["location_code"],
		1,
	) is False

	balances_after = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}

	assert balances_after == balances_before
	assert database.get_inventory_movements() == []

def test_receive_inventory_rejects_different_sku_at_occupied_location(
	isolated_database,
):
	anchor_balance = next(
		item
		for item in database.get_inventory_balances()
		if item["sku"] == "ANCHOR-01"
	)
	balances_before = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}

	assert database.receive_inventory(
		"ADH-001",
		anchor_balance["location_code"],
		1,
	) is False

	balances_after = {
		(item["sku"], item["location_code"]): item["quantity"]
		for item in database.get_inventory_balances()
	}

	assert balances_after == balances_before
	assert database.get_inventory_movements() == []