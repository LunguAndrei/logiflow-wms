PALLET_LENGTH_CM = 105
PALLET_WIDTH_CM = 85
PALLET_HEIGHT_CM = 15
PALLET_TARE_WEIGHT_KG = 25

MAX_CARGO_WEIGHT_KG = 300
MAX_LOADED_HEIGHT_CM = 160

def box_fits_pallet_at(box, x_cm, y_cm, z_cm):
	return (
		x_cm >= 0
		and y_cm >= 0
		and z_cm >= 0
		and x_cm + box["outer_length_cm"] <= PALLET_LENGTH_CM
		and y_cm + box["outer_width_cm"] <= PALLET_WIDTH_CM
		and PALLET_HEIGHT_CM + z_cm + box["outer_height_cm"]
		<= MAX_LOADED_HEIGHT_CM
	)

def boxes_overlap(first, second):
	return (
		first["x_cm"] < second["x_cm"] + second["outer_length_cm"]
		and first["x_cm"] + first["outer_length_cm"] > second["x_cm"]
		and first["y_cm"] < second["y_cm"] + second["outer_width_cm"]
		and first["y_cm"] + first["outer_width_cm"] > second["y_cm"]
		and first["z_cm"] < second["z_cm"] + second["outer_height_cm"]
		and first["z_cm"] + first["outer_height_cm"] > second["z_cm"]
	)

def footprint_is_supported(box, x_cm, y_cm, z_cm, placed_boxes):
	if z_cm == 0:
		return True

	box_left = x_cm
	box_right = x_cm + box["outer_length_cm"]
	box_front = y_cm
	box_back = y_cm + box["outer_width_cm"]

	support_boxes = [
		item
		for item in placed_boxes
		if item["z_cm"] + item["outer_height_cm"] == z_cm
	]

	if not support_boxes:
		return False

	x_edges = {box_left, box_right}
	y_edges = {box_front, box_back}

	for item in support_boxes:
		overlap_left = max(box_left, item["x_cm"])
		overlap_right = min(
			box_right,
			item["x_cm"] + item["outer_length_cm"],
		)
		overlap_front = max(box_front, item["y_cm"])
		overlap_back = min(
			box_back,
			item["y_cm"] + item["outer_width_cm"],
		)

		if overlap_left < overlap_right and overlap_front < overlap_back:
			x_edges.add(overlap_left)
			x_edges.add(overlap_right)
			y_edges.add(overlap_front)
			y_edges.add(overlap_back)

	sorted_x_edges = sorted(x_edges)
	sorted_y_edges = sorted(y_edges)

	for x_index in range(len(sorted_x_edges) - 1):
		for y_index in range(len(sorted_y_edges) - 1):
			cell_x = (
				sorted_x_edges[x_index] + sorted_x_edges[x_index + 1]
			) / 2
			cell_y = (
				sorted_y_edges[y_index] + sorted_y_edges[y_index + 1]
			) / 2

			cell_is_supported = any(
				item["x_cm"] <= cell_x
				< item["x_cm"] + item["outer_length_cm"]
				and item["y_cm"] <= cell_y
				< item["y_cm"] + item["outer_width_cm"]
				for item in support_boxes
			)

			if not cell_is_supported:
				return False

	return True

def find_box_placement(box, placed_boxes):
	x_positions = {0.0}
	y_positions = {0.0}
	z_positions = {0.0}

	for item in placed_boxes:
		x_positions.add(item["x_cm"] + item["outer_length_cm"])
		y_positions.add(item["y_cm"] + item["outer_width_cm"])
		z_positions.add(item["z_cm"] + item["outer_height_cm"])

	candidate_positions = sorted(
		(
			(x_cm, y_cm, z_cm)
			for z_cm in z_positions
			for y_cm in y_positions
			for x_cm in x_positions
		),
		key=lambda position: (position[2], position[1], position[0]),
	)

	for x_cm, y_cm, z_cm in candidate_positions:
		if not box_fits_pallet_at(box, x_cm, y_cm, z_cm):
			continue

		candidate = {
			**box,
			"x_cm": x_cm,
			"y_cm": y_cm,
			"z_cm": z_cm,
		}

		if any(boxes_overlap(candidate, item) for item in placed_boxes):
			continue

		if not footprint_is_supported(
			box,
			x_cm,
			y_cm,
			z_cm,
			placed_boxes,
		):
			continue

		return candidate

	return None

def fill_pallet(packed_boxes, box_types):
	box_types_by_code = {
		box_type["code"]: box_type
		for box_type in box_types
	}

	boxes_to_place = sorted(
		packed_boxes,
		key=lambda packed_box: (
			box_types_by_code[packed_box["box_code"]]["outer_length_cm"]
			* box_types_by_code[packed_box["box_code"]]["outer_width_cm"]
		),
		reverse=True,
	)

	placed_boxes = []
	remaining_boxes = []
	cargo_weight = 0

	for packed_box in boxes_to_place:
		box_type = box_types_by_code[packed_box["box_code"]]
		box = {
			**packed_box,
			"outer_length_cm": box_type["outer_length_cm"],
			"outer_width_cm": box_type["outer_width_cm"],
			"outer_height_cm": box_type["outer_height_cm"],
		}

		if cargo_weight + box["gross_weight_kg"] > MAX_CARGO_WEIGHT_KG:
			remaining_boxes.append(packed_box)
			continue

		placement = find_box_placement(box, placed_boxes)
		if placement is None:
			remaining_boxes.append(packed_box)
			continue

		placed_boxes.append(placement)
		cargo_weight += box["gross_weight_kg"]

	return placed_boxes, remaining_boxes

def build_pallet_plan(packed_boxes, box_types):
	remaining_boxes = list(packed_boxes)
	pallets = []

	while remaining_boxes:
		placed_boxes, not_placed = fill_pallet(
			remaining_boxes,
			box_types,
		)

		if not placed_boxes:
			raise ValueError("No boxes could be placed on an empty pallet")

		cargo_weight = sum(
			box["gross_weight_kg"]
			for box in placed_boxes
		)
		loaded_height = max(
			PALLET_HEIGHT_CM
			+ box["z_cm"]
			+ box["outer_height_cm"]
			for box in placed_boxes
		)

		pallets.append({
			"pallet_number": len(pallets) + 1,
			"box_count": len(placed_boxes),
			"cargo_weight_kg": round(cargo_weight, 2),
			"pallet_tare_weight_kg": PALLET_TARE_WEIGHT_KG,
			"total_weight_kg": round(
				cargo_weight + PALLET_TARE_WEIGHT_KG, 2
			),
			"loaded_height_cm": round(loaded_height, 2),
			"boxes": [
				{
					"box_code": box["box_code"],
					"x_cm": box["x_cm"],
					"y_cm": box["y_cm"],
					"z_cm": box["z_cm"],
					"gross_weight_kg": box["gross_weight_kg"],
					"placements": box["placements"],
				}
				for box in placed_boxes
			],
		})

		remaining_boxes = not_placed

	return {"pallets": pallets}