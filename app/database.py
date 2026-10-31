import sqlite3
import os
from pathlib import Path

LOCAL_DATABASE_PATH = Path(__file__).resolve().parent.parent / "logiflow.db"
DATABASE_PATH = Path(
	os.environ.get("DATABASE_PATH", str(LOCAL_DATABASE_PATH))
)

seed_products = [
	("BRG-001", "Industrial bearing", "Components", "piece", 120, 30),
	("CAB-002", "Electrical cable", "Electrical", "meter", 500, 100),
	("GLV-003", "Safety gloves", "PPE", "pair", 200, 40),
]

def initialize_database():
	connection = sqlite3.connect(DATABASE_PATH)
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
		connection.executemany(
			"""
			INSERT OR IGNORE INTO products
				(sku, name, category, unit, quantity_on_hand, reorder_point)
			VALUES (?, ?, ?, ?, ?, ?)
			""",
			seed_products,
		)	
		connection.commit()
	finally:
		connection.close()

def get_products():
	connection = sqlite3.connect(DATABASE_PATH)
	connection.row_factory = sqlite3.Row
	try:
		rows = connection.execute(
			"""
			SELECT sku, name, category, unit, quantity_on_hand, reorder_point
			FROM products
			ORDER BY sku
			"""
		).fetchall()
		return [dict(row) for row in rows]
	finally:
		connection.close()

def add_product(product_data):
	connection = sqlite3.connect(DATABASE_PATH)
	try:
		connection.execute(
			"""
			INSERT INTO products
				(sku, name, category, unit, quantity_on_hand, reorder_point)
			VALUES (?, ?, ?, ?, ?, ?)
			""",
			(
				product_data["sku"],
				product_data["name"],
				product_data["category"],
				product_data["unit"],
				product_data["quantity_on_hand"],
				product_data["reorder_point"],
			),
		)
		connection.commit()
	finally:
		connection.close()

