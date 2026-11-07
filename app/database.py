import sqlite3
import os
from pathlib import Path

LOCAL_DATABASE_PATH = Path(__file__).resolve().parent.parent / "logiflow.db"
DATABASE_PATH = Path(
	os.environ.get("DATABASE_PATH", str(LOCAL_DATABASE_PATH))
)

def connect_database():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

seed_products = [
	("BRG-001", "Industrial bearing", "Components", "piece", 120, 30, 8, 8, 5, 0.70),
	("CAB-003", "3 m cable roll", "Electrical", "roll", 5, 2, 15, 15, 4, 0.35),
	("CAB-005", "5 m cable roll", "Electrical", "roll", 5, 2, 16, 16, 5, 0.55),
	("CAB-010", "10 m cable roll", "Electrical", "roll", 11, 3, 18, 18, 6, 1.00),
	("CAB-025", "25 m cable roll", "Electrical", "roll", 4, 2, 22, 22, 8, 2.40),
	("CAB-050", "50 m cable roll", "Electrical", "roll", 5, 2, 28, 28, 10, 4.60),
	("GLV-003", "Safety gloves", "PPE", "pair", 200, 40, 24, 12, 3, 0.15),
	("BOLT-M08", "M8 bolts, pack of 100", "Fasteners", "pack", 20, 5, 12, 9, 6, 1.20),
	("NUT-M08", "M8 nuts, pack of 100", "Fasteners", "pack", 20, 5, 10, 8, 5, 0.80),
	("WASH-M08", "M8 washers, pack of 100", "Fasteners", "pack", 30, 8, 10, 8, 4, 0.40),
	("SCREW-050", "Wood screws, pack", "Fasteners", "pack", 15, 4, 18, 12, 5, 0.90),
	("TAPE-001", "Industrial adhesive tape roll", "Supplies", "roll", 25, 5, 12, 12, 5, 0.25),
	("SEAL-010", "Gaskets, set of 10", "Components", "set", 12, 3, 15, 10, 4, 0.30),
	("BEAR-002", "Compact bearing", "Components", "piece", 40, 10, 10, 10, 6, 0.95),
	("BEAR-003", "Heavy-duty bearing", "Components", "piece", 10, 3, 14, 14, 8, 2.20),
	("MASK-010", "Protective masks, pack of 10", "PPE", "pack", 20, 5, 20, 15, 8, 0.35),
	("GOGGLE-01", "Safety goggles", "PPE", "piece", 15, 4, 18, 8, 7, 0.18),
	("GLV-004", "Cut-resistant gloves", "PPE", "pair", 20, 5, 25, 13, 4, 0.22),
	("VEST-001", "High-visibility vest", "PPE", "piece", 12, 3, 28, 22, 4, 0.30),
	("HELM-001", "Safety helmet", "PPE", "piece", 8, 2, 30, 24, 18, 0.65),
	("FILTER-01", "Small industrial filter", "Components", "piece", 10, 3, 12, 12, 15, 0.55),
	("FILTER-02", "Medium industrial filter", "Components", "piece", 8, 2, 20, 20, 25, 1.80),
	("VALVE-01", "Small metal valve", "Components", "piece", 12, 3, 12, 10, 8, 1.40),
	("VALVE-02", "Medium metal valve", "Components", "piece", 5, 1, 20, 15, 12, 4.80),
	("SENSOR-01", "Temperature sensor", "Electrical", "piece", 15, 4, 14, 10, 6, 0.35),
	("SENSOR-02", "Pressure sensor", "Electrical", "piece", 12, 3, 18, 12, 10, 0.80),
	("MOTOR-01", "Small electric motor", "Components", "piece", 4, 1, 28, 20, 18, 8.50),
	("PUMP-001", "Hand pump", "Tools", "piece", 5, 1, 35, 18, 15, 5.20),
	("TOOL-001", "Adjustable wrench", "Tools", "piece", 20, 5, 25, 8, 3, 0.75),
	("TOOL-002", "Screwdriver set", "Tools", "set", 12, 3, 30, 20, 5, 1.10),
	("TOOL-003", "Industrial pliers", "Tools", "piece", 15, 4, 22, 8, 3, 0.45),
	("DRILL-001", "Portable drill", "Tools", "piece", 8, 2, 32, 25, 10, 3.20),
	("BAT-018", "Power tool battery", "Electrical", "piece", 10, 3, 12, 8, 7, 0.65),
	("LAMP-001", "LED work light", "Electrical", "piece", 10, 3, 24, 18, 10, 1.30),
	("CONNECT-01", "Electrical connectors, set of 20", "Electrical", "set", 25, 5, 16, 12, 7, 0.50),
	("PIPE-050", "Metal pipe, 50 cm long", "Components", "piece", 10, 2, 50, 5, 5, 2.80),
	("PIPE-120", "Metal pipe, 120 cm long", "Components", "piece", 5, 1, 120, 5, 5, 6.20),
	("HOSE-050", "Coiled flexible hose", "Components", "piece", 8, 2, 30, 25, 12, 2.10),
	("CHAIN-001", "Metal chain, 2 m pack", "Components", "pack", 6, 2, 25, 20, 10, 7.50),
	("GEAR-001", "Small gear", "Components", "piece", 15, 3, 15, 15, 6, 1.60),
	("GEAR-002", "Large gear", "Components", "piece", 3, 1, 30, 30, 10, 9.80),
	("PANEL-001", "Small electrical panel", "Electrical", "piece", 5, 1, 35, 25, 15, 6.50),
	("BOX-TOOL", "Box of installation accessories", "Tools", "box", 6, 2, 35, 25, 20, 4.20),
	("CHEM-001", "1 L lubricant container", "Chemicals", "container", 10, 2, 12, 8, 24, 1.10),
	("CHEM-002", "5 L industrial cleaner container", "Chemicals", "container", 4, 1, 20, 15, 30, 5.50),
	("ADH-001", "Industrial adhesive cartridge", "Supplies", "cartridge", 15, 4, 30, 6, 6, 0.65),
	("ROLL-001", "Insulation material roll", "Components", "roll", 4, 1, 40, 20, 20, 3.60),
	("BRACKET-01", "Metal bracket", "Components", "piece", 10, 2, 25, 20, 12, 2.70),
	("ANCHOR-01", "Metal anchors, pack of 10", "Fasteners", "pack", 8, 2, 20, 12, 8, 3.80),
	("MOTOR-XL", "Large industrial motor", "Components", "piece", 1, 1, 55, 45, 40, 18.00),
]

seed_box_types = [
	("BOX-3.7L", 3.7, 20, 15, 12.33, 21, 16, 13.33, 0.10, 5),
	("BOX-5L", 5, 25, 20, 10, 26, 21, 11, 0.15, 5),
	("BOX-7L", 7, 28, 25, 10, 29, 26, 11, 0.20, 5),
	("BOX-10L", 10, 40, 25, 10, 41, 26, 11, 0.25, 5),
	("BOX-14L", 14, 35, 20, 20, 36, 21, 21, 0.35, 5),
	("BOX-34L", 34, 50, 34, 20, 51, 35, 21, 0.65, 15),
	("BOX-50L", 50, 50, 40, 25, 51, 41, 26, 0.85, 15),
	("BOX-70L", 70, 50, 40, 35, 51, 41, 36, 1.10, 15),
]

def initialize_database():
	connection = connect_database()
	try:
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS products (
				sku TEXT PRIMARY KEY,
				name TEXT NOT NULL,
				category TEXT NOT NULL,
				unit TEXT NOT NULL,
				quantity_on_hand INTEGER NOT NULL CHECK (quantity_on_hand >= 0),
				reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0)
			)
			"""
		)

		existing_columns = {
			row[1] for row in connection.execute("PRAGMA table_info(products)")
		}
		new_columns = {
			"length_cm": "REAL",
			"width_cm": "REAL",
			"height_cm": "REAL",
			"weight_kg": "REAL",
		}

		for column_name, column_type in new_columns.items():
			if column_name not in existing_columns:
				connection.execute(
					f"ALTER TABLE products ADD COLUMN {column_name} {column_type}"
				)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS box_types (
				code TEXT PRIMARY KEY,
				capacity_liters REAL NOT NULL CHECK (capacity_liters > 0),
				inner_length_cm REAL NOT NULL CHECK (inner_length_cm > 0),
				inner_width_cm REAL NOT NULL CHECK (inner_width_cm > 0),
				inner_height_cm REAL NOT NULL CHECK (inner_height_cm > 0),
				outer_length_cm REAL NOT NULL CHECK (outer_length_cm > 0),
				outer_width_cm REAL NOT NULL CHECK (outer_width_cm > 0),
				outer_height_cm REAL NOT NULL CHECK (outer_height_cm > 0),
				empty_weight_kg REAL NOT NULL CHECK (empty_weight_kg > 0),
				max_payload_kg REAL NOT NULL CHECK (max_payload_kg > 0)
			)
			"""
		)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS storage_locations (
				location_code TEXT PRIMARY KEY
			)
			"""
		)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS inventory_balances (
				sku TEXT NOT NULL,
				location_code TEXT NOT NULL,
				quantity INTEGER NOT NULL CHECK (quantity >= 0),
				PRIMARY KEY (sku, location_code),
				FOREIGN KEY (sku) REFERENCES products(sku),
				FOREIGN KEY (location_code) REFERENCES storage_locations(location_code)
			)
			"""
		)
		connection.executemany(
			"""
			INSERT OR IGNORE INTO products
				(sku, name, category, unit, quantity_on_hand, reorder_point, length_cm, width_cm, height_cm, weight_kg)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(sku) DO UPDATE SET
				name = excluded.name,
				category = excluded.category,
				unit = excluded.unit,
				reorder_point = excluded.reorder_point,
				length_cm = excluded.length_cm,
				width_cm = excluded.width_cm,
				height_cm = excluded.height_cm,
				weight_kg = excluded.weight_kg
			""",
			seed_products,
		)
		products_without_balances = connection.execute(
			"""
			SELECT p.sku, p.quantity_on_hand
			FROM products AS p
			LEFT JOIN inventory_balances AS ib ON ib.sku = p.sku
			WHERE ib.sku IS NULL
			ORDER BY p.sku
			"""
		).fetchall()

		used_locations = {
			row[0]
			for row in connection.execute(
				"SELECT location_code FROM storage_locations"
			)
		}

		location_index = 0

		for sku, quantity in products_without_balances:
			while True:
				rack_number = location_index // 60 + 1
				level_number = (location_index % 60) // 10 + 1
				position_number = location_index % 10 + 1

				if rack_number > 20:
					raise ValueError("No free locations remain in aisle A")

				location_code = (
					f"A-{rack_number:02d}-{level_number:02d}-{position_number:02d}"
				)
				location_index += 1

				if location_code not in used_locations:
					break

			connection.execute(
				"""
				INSERT OR IGNORE INTO storage_locations (location_code)
				VALUES (?)
				""",
				(location_code,),
			)
			connection.execute(
				"""
				INSERT INTO inventory_balances
					(sku, location_code, quantity)
				VALUES (?, ?, ?)
				""",
				(sku, location_code, quantity),
			)
			used_locations.add(location_code)
		connection.executemany(
			"""
			INSERT INTO box_types
				(code, capacity_liters,
				inner_length_cm, inner_width_cm, inner_height_cm,
				outer_length_cm, outer_width_cm, outer_height_cm,
				empty_weight_kg, max_payload_kg)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(code) DO UPDATE SET
				capacity_liters = excluded.capacity_liters,
				inner_length_cm = excluded.inner_length_cm,
				inner_width_cm = excluded.inner_width_cm,
				inner_height_cm = excluded.inner_height_cm,
				outer_length_cm = excluded.outer_length_cm,
				outer_width_cm = excluded.outer_width_cm,
				outer_height_cm = excluded.outer_height_cm,
				empty_weight_kg = excluded.empty_weight_kg,
				max_payload_kg = excluded.max_payload_kg
			""",
			seed_box_types,
		)
		connection.commit()
	finally:
		connection.close()

def get_products():
	connection = connect_database()
	connection.row_factory = sqlite3.Row
	try:
		rows = connection.execute(
			"""
			SELECT sku, name, category, unit, quantity_on_hand, reorder_point, length_cm, width_cm, height_cm, weight_kg
			FROM products
			ORDER BY sku
			"""
		).fetchall()
		return [dict(row) for row in rows]
	finally:
		connection.close()

def get_box_types():
	connection = connect_database()
	connection.row_factory = sqlite3.Row
	try:
		rows = connection.execute(
			"""
			SELECT code, capacity_liters,
				   inner_length_cm, inner_width_cm, inner_height_cm,
				   outer_length_cm, outer_width_cm, outer_height_cm,
				   empty_weight_kg, max_payload_kg
			FROM box_types
			ORDER BY capacity_liters
			"""
		).fetchall()
		return [dict(row) for row in rows]
	finally:
		connection.close()

def add_product(product_data):
	connection = connect_database()
	try:
		connection.execute(
			"""
			INSERT INTO products
				(sku, name, category, unit, quantity_on_hand, reorder_point, length_cm, width_cm, height_cm, weight_kg)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""",
			(
				product_data["sku"],
				product_data["name"],
				product_data["category"],
				product_data["unit"],
				product_data["quantity_on_hand"],
				product_data["reorder_point"],
				product_data["length_cm"],
				product_data["width_cm"],
				product_data["height_cm"],
				product_data["weight_kg"],
			),
		)
		connection.commit()
	finally:
		connection.close()

def get_locations():
	connection = connect_database()
	try:
		rows = connection.execute(
			"""
			SELECT location_code
			FROM storage_locations
			ORDER BY location_code
			"""
		).fetchall()
		return [{"location_code": row[0]} for row in rows]
	finally:
		connection.close()


def get_inventory_balances():
	connection = connect_database()
	connection.row_factory = sqlite3.Row
	try:
		rows = connection.execute(
			"""
			SELECT sku, location_code, quantity
			FROM inventory_balances
			ORDER BY location_code, sku
			"""
		).fetchall()
		return [dict(row) for row in rows]
	finally:
		connection.close()

def pick_inventory(sku, location_code, quantity):
	connection = connect_database()
	try:
		balance_update = connection.execute(
			"""
			UPDATE inventory_balances
			SET quantity = quantity - ?
			WHERE sku = ? AND location_code = ? AND quantity >= ?
			""",
			(quantity, sku, location_code, quantity),
		)

		if balance_update.rowcount == 0:
			connection.rollback()
			return False

		product_update = connection.execute(
			"""
			UPDATE products
			SET quantity_on_hand = quantity_on_hand - ?
			WHERE sku = ? AND quantity_on_hand >= ?
			""",
			(quantity, sku, quantity),
		)

		if product_update.rowcount == 0:
			connection.rollback()
			return False

		connection.commit()
		return True
	finally:
		connection.close()

def confirm_inventory_picks(picks):
	connection = connect_database()
	try:
		for pick in picks:
			quantity = pick["quantity"]

			balance_update = connection.execute(
				"""
				UPDATE inventory_balances
				SET quantity = quantity - ?
				WHERE sku = ?
					AND location_code = ?
					AND quantity >= ?
				""",
				(
					quantity,
					pick["sku"],
					pick["location_code"],
					quantity,
				),
			)

			if balance_update.rowcount == 0:
				connection.rollback()
				return False

			product_update = connection.execute(
				"""
				UPDATE products
				SET quantity_on_hand = quantity_on_hand - ?
				WHERE sku = ? AND quantity_on_hand >= ?
				""",
				(quantity, pick["sku"], quantity),
			)

			if product_update.rowcount == 0:
				connection.rollback()
				return False

		connection.commit()
		return True
	finally:
		connection.close()

def receive_inventory(sku, location_code, quantity):
	connection = connect_database()
	try:
		connection.execute(
			"""
			INSERT INTO inventory_balances (sku, location_code, quantity)
			VALUES (?, ?, ?)
			ON CONFLICT(sku, location_code) DO UPDATE SET
				quantity = quantity + excluded.quantity
			""",
			(sku, location_code, quantity),
		)

		connection.execute(
			"""
			UPDATE products
			SET quantity_on_hand = quantity_on_hand + ?
			WHERE sku = ?
			""",
			(quantity, sku),
		)

		connection.commit()
		return True
	finally:
		connection.close()

def add_location(location_code):
	connection = connect_database()
	try:
		connection.execute(
			"""
			INSERT INTO storage_locations (location_code)
			VALUES (?)
			""",
			(location_code,),
		)
		connection.commit()
	finally:
		connection.close()
