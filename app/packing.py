from itertools import permutations, product as cartesian_product


def product_fits_box(product, box):
	product_dimensions = (
		product["length_cm"],
		product["width_cm"],
		product["height_cm"],
	)
	inner_dimensions = (
		box["inner_length_cm"],
		box["inner_width_cm"],
		box["inner_height_cm"],
	)

	if any(dimension is None for dimension in product_dimensions):
		return False

	if product["weight_kg"] is None:
		return False

	if product["weight_kg"] > box["max_payload_kg"]:
		return False

	for orientation in set(permutations(product_dimensions)):
		if all(
			product_side <= box_side
			for product_side, box_side in zip(orientation, inner_dimensions)
		):
			return True

	return False


def placements_overlap(first, second):
	return (
		first["x_cm"] < second["x_cm"] + second["length_cm"]
		and first["x_cm"] + first["length_cm"] > second["x_cm"]
		and first["y_cm"] < second["y_cm"] + second["width_cm"]
		and first["y_cm"] + first["width_cm"] > second["y_cm"]
		and first["z_cm"] < second["z_cm"] + second["height_cm"]
		and first["z_cm"] + first["height_cm"] > second["z_cm"]
	)


def find_placement(product, box, placements):
	if not product_fits_box(product, box):
		return None

	current_weight = sum(item["weight_kg"] for item in placements)
	if current_weight + product["weight_kg"] > box["max_payload_kg"]:
		return None

	x_positions = {0.0}
	y_positions = {0.0}
	z_positions = {0.0}

	for item in placements:
		x_positions.add(item["x_cm"] + item["length_cm"])
		y_positions.add(item["y_cm"] + item["width_cm"])
		z_positions.add(item["z_cm"] + item["height_cm"])

	candidate_positions = sorted(
		cartesian_product(x_positions, y_positions, z_positions),
		key=lambda position: (position[2], position[1], position[0]),
	)

	product_dimensions = (
		product["length_cm"],
		product["width_cm"],
		product["height_cm"],
	)

	for orientation in set(permutations(product_dimensions)):
		length_cm, width_cm, height_cm = orientation

		for x_cm, y_cm, z_cm in candidate_positions:
			if x_cm + length_cm > box["inner_length_cm"]:
				continue
			if y_cm + width_cm > box["inner_width_cm"]:
				continue
			if z_cm + height_cm > box["inner_height_cm"]:
				continue

			candidate = {
				"sku": product["sku"],
				"x_cm": x_cm,
				"y_cm": y_cm,
				"z_cm": z_cm,
				"length_cm": length_cm,
				"width_cm": width_cm,
				"height_cm": height_cm,
				"weight_kg": product["weight_kg"],
			}

			if all(
				not placements_overlap(candidate, item)
				for item in placements
			):
				return candidate

	return None

def calculate_order_totals(products):
	total_volume_liters = sum(
		product["length_cm"]
		* product["width_cm"]
		* product["height_cm"]
		/ 1000
		for product in products
	)
	total_weight_kg = sum(
		product["weight_kg"]
		for product in products
	)

	return {
		"volume_liters": round(total_volume_liters, 3),
		"product_weight_kg": round(total_weight_kg, 2),
	}

def choose_candidate_box(products, box_types):
	totals = calculate_order_totals(products)
	ordered_boxes = sorted(
		box_types,
		key=lambda box: box["capacity_liters"],
	)

	for box in ordered_boxes:
		if (
			totals["volume_liters"] <= box["capacity_liters"]
			and totals["product_weight_kg"] <= box["max_payload_kg"]
		):
			return box

	return ordered_boxes[-1]

def fill_box(products, box_type):
	placements = []
	remaining_products = []

	for product in products:
		placement = find_placement(product, box_type, placements)

		if placement is None:
			remaining_products.append(product)
		else:
			placements.append(placement)

	return placements, remaining_products

def shrink_packed_boxes(packed_boxes, box_types):
	ordered_boxes = sorted(
		box_types,
		key=lambda box: box["capacity_liters"],
	)

	for packed_box in packed_boxes:
		original_box = packed_box["box_type"]
		original_placements = packed_box["placements"]
		product_units = [
			{
				"sku": placement["sku"],
				"length_cm": placement["length_cm"],
				"width_cm": placement["width_cm"],
				"height_cm": placement["height_cm"],
				"weight_kg": placement["weight_kg"],
			}
			for placement in original_placements
		]

		best_box = original_box
		best_placements = original_placements
		current_index = ordered_boxes.index(original_box)

		for candidate_box in reversed(ordered_boxes[:current_index]):
			new_placements, not_placed = fill_box(
				product_units,
				candidate_box,
			)

			if not not_placed:
				best_box = candidate_box
				best_placements = new_placements

		packed_box["box_type"] = best_box
		packed_box["placements"] = best_placements

	return packed_boxes

def build_packing_plan(products, box_types):
	remaining_products = list(products)
	ordered_boxes = sorted(
		box_types,
		key=lambda box: box["capacity_liters"],
	)
	packed_boxes = []
	special_counts = {}

	while remaining_products:
		candidate_box = choose_candidate_box(
			remaining_products,
			ordered_boxes,
		)
		start_index = ordered_boxes.index(candidate_box)
		selected_box = None
		selected_placements = None
		selected_remaining = None

		for box_index in range(start_index, len(ordered_boxes)):
			box_type = ordered_boxes[box_index]
			placements, not_placed = fill_box(
				remaining_products,
				box_type,
			)

			if not not_placed:
				selected_box = box_type
				selected_placements = placements
				selected_remaining = []
				break

			is_largest_box = box_index == len(ordered_boxes) - 1
			if is_largest_box and placements:
				selected_box = box_type
				selected_placements = placements
				selected_remaining = not_placed
				break

		if selected_box is None:
			for product in remaining_products:
				sku = product["sku"]
				special_counts[sku] = special_counts.get(sku, 0) + 1
			remaining_products = []
			break

		packed_boxes.append({
			"box_type": selected_box,
			"placements": selected_placements,
		})
		remaining_products = selected_remaining

	packed_boxes = shrink_packed_boxes(packed_boxes, ordered_boxes)

	result_boxes = []
	for packed_box in packed_boxes:
		box_type = packed_box["box_type"]
		product_weight = sum(
			placement["weight_kg"]
			for placement in packed_box["placements"]
		)
		result_boxes.append({
			"box_code": box_type["code"],
			"capacity_liters": box_type["capacity_liters"],
			"product_weight_kg": round(product_weight, 2),
			"empty_box_weight_kg": box_type["empty_weight_kg"],
			"gross_weight_kg": round(
				product_weight + box_type["empty_weight_kg"], 2
			),
			"placements": packed_box["placements"],
		})

	return {
		"boxes": result_boxes,
		"special_handling": [
			{
				"sku": sku,
				"quantity": quantity,
				"reason": "No available box type can fit this product",
			}
			for sku, quantity in special_counts.items()
		],
	}