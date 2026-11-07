def build_pick_plan(requested_items, inventory_balances):
	requested_quantities = {}

	for sku, quantity in requested_items:
		requested_quantities[sku] = (
			requested_quantities.get(sku, 0) + quantity
		)

	balances_by_sku = {}
	for balance in inventory_balances:
		balances_by_sku.setdefault(balance["sku"], []).append(balance)

	pick_lines = []

	for sku, requested_quantity in requested_quantities.items():
		remaining = requested_quantity
		locations = sorted(
			balances_by_sku.get(sku, []),
			key=lambda balance: balance["location_code"],
		)

		for balance in locations:
			pick_quantity = min(remaining, balance["quantity"])

			if pick_quantity > 0:
				pick_lines.append({
					"sku": sku,
					"location_code": balance["location_code"],
					"quantity": pick_quantity,
				})
				remaining -= pick_quantity

			if remaining == 0:
				break

		if remaining > 0:
			raise ValueError(f"Insufficient stock for '{sku}'")

	return pick_lines