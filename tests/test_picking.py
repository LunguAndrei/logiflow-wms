import pytest

from app.picking import build_pick_plan


def test_build_pick_plan_splits_quantity_across_locations():
	requested_items = [
		("ADH-001", 10),
		("ADH-001", 8),
	]
	inventory_balances = [
		{
			"sku": "ADH-001",
			"location_code": "A-01-01-02",
			"quantity": 6,
		},
		{
			"sku": "ADH-001",
			"location_code": "A-01-01-01",
			"quantity": 15,
		},
	]

	result = build_pick_plan(requested_items, inventory_balances)

	assert result == [
		{
			"sku": "ADH-001",
			"location_code": "A-01-01-01",
			"quantity": 15,
		},
		{
			"sku": "ADH-001",
			"location_code": "A-01-01-02",
			"quantity": 3,
		},
	]


def test_build_pick_plan_rejects_insufficient_stock():
	requested_items = [("ADH-001", 7)]
	inventory_balances = [
		{
			"sku": "ADH-001",
			"location_code": "A-01-01-01",
			"quantity": 6,
		},
	]

	with pytest.raises(ValueError, match="Insufficient stock"):
		build_pick_plan(requested_items, inventory_balances)