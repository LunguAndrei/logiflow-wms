from app.palletizing import PALLET_LENGTH_CM, PALLET_WIDTH_CM

TRUCK_LENGTH_CM = 600
TRUCK_WIDTH_CM = 240
TRUCK_HEIGHT_CM = 240
TRUCK_MAX_PAYLOAD_KG = 5000


def pallet_fits_in_truck_at(pallet, x_cm, y_cm):
	return (
		x_cm >= 0
		and y_cm >= 0
		and x_cm + PALLET_LENGTH_CM <= TRUCK_WIDTH_CM
		and y_cm + PALLET_WIDTH_CM <= TRUCK_LENGTH_CM
		and pallet["loaded_height_cm"] <= TRUCK_HEIGHT_CM
	)

def pallets_overlap(first, second):
	return (
		first["x_cm"] < second["x_cm"] + PALLET_LENGTH_CM
		and first["x_cm"] + PALLET_LENGTH_CM > second["x_cm"]
		and first["y_cm"] < second["y_cm"] + PALLET_WIDTH_CM
		and first["y_cm"] + PALLET_WIDTH_CM > second["y_cm"]
	)

def find_pallet_position(pallet, placed_pallets):
	x_positions = {0.0}
	y_positions = {0.0}

	for item in placed_pallets:
		x_positions.add(item["x_cm"] + PALLET_LENGTH_CM)
		y_positions.add(item["y_cm"] + PALLET_WIDTH_CM)

	candidate_positions = sorted(
		(
			(x_cm, y_cm)
			for y_cm in y_positions
			for x_cm in x_positions
		),
		key=lambda position: (position[1], position[0]),
	)

	for x_cm, y_cm in candidate_positions:
		if not pallet_fits_in_truck_at(pallet, x_cm, y_cm):
			continue

		candidate = {
			**pallet,
			"x_cm": x_cm,
			"y_cm": y_cm,
		}

		if all(
			not pallets_overlap(candidate, item)
			for item in placed_pallets
		):
			return candidate

	return None

def build_truck_plan(pallets):
	remaining_pallets = list(pallets)
	trucks = []

	while remaining_pallets:
		placed_pallets = []
		not_placed = []
		loaded_weight = 0

		for pallet in remaining_pallets:
			if loaded_weight + pallet["total_weight_kg"] > TRUCK_MAX_PAYLOAD_KG:
				not_placed.append(pallet)
				continue

			placement = find_pallet_position(pallet, placed_pallets)
			if placement is None:
				not_placed.append(pallet)
				continue

			placed_pallets.append(placement)
			loaded_weight += pallet["total_weight_kg"]

		if not placed_pallets:
			raise ValueError("A pallet cannot fit in an empty truck")

		trucks.append({
			"truck_number": len(trucks) + 1,
			"pallet_count": len(placed_pallets),
			"loaded_weight_kg": round(loaded_weight, 2),
			"payload_limit_kg": TRUCK_MAX_PAYLOAD_KG,
			"pallets": [
				{
					"pallet_number": pallet["pallet_number"],
					"x_cm": pallet["x_cm"],
					"y_cm": pallet["y_cm"],
					"loaded_height_cm": pallet["loaded_height_cm"],
					"total_weight_kg": pallet["total_weight_kg"],
				}
				for pallet in placed_pallets
			],
		})

		remaining_pallets = not_placed

	return {"trucks": trucks}