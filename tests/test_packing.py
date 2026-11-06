from app.packing import build_packing_plan, find_placement, placements_overlap, product_fits_box


def test_product_fits_box_when_rotated():
    product = {
        "length_cm": 8,
        "width_cm": 5,
        "height_cm": 8,
        "weight_kg": 1,
    }

    box = {
        "inner_length_cm": 5,
        "inner_width_cm": 8,
        "inner_height_cm": 8,
        "max_payload_kg": 5,
    }

    assert product_fits_box(product, box) is True

def test_product_does_not_fit_box_when_too_heavy():
    product = {
        "length_cm": 5,
        "width_cm": 5,
        "height_cm": 5,
        "weight_kg": 6,
    }

    box = {
        "inner_length_cm": 10,
        "inner_width_cm": 10,
        "inner_height_cm": 10,
        "max_payload_kg": 5,
    }

    assert product_fits_box(product, box) is False

def test_product_does_not_fit_box_when_too_large():
    product = {
        "length_cm": 12,
        "width_cm": 5,
        "height_cm": 5,
        "weight_kg": 1,
    }

    box = {
        "inner_length_cm": 10,
        "inner_width_cm": 10,
        "inner_height_cm": 10,
        "max_payload_kg": 5,
    }

    assert product_fits_box(product, box) is False

def test_placements_overlap_when_products_intersect():
    first = {
        "x_cm": 0, "y_cm": 0, "z_cm": 0,
        "length_cm": 10, "width_cm": 10, "height_cm": 10,
    }
    second = {
        "x_cm": 5, "y_cm": 5, "z_cm": 5,
        "length_cm": 10, "width_cm": 10, "height_cm": 10,
    }

    assert placements_overlap(first, second) is True


def test_placements_do_not_overlap_when_touching_at_edge():
    first = {
        "x_cm": 0, "y_cm": 0, "z_cm": 0,
        "length_cm": 10, "width_cm": 10, "height_cm": 10,
    }
    second = {
        "x_cm": 10, "y_cm": 0, "z_cm": 0,
        "length_cm": 10, "width_cm": 10, "height_cm": 10,
    }

    assert placements_overlap(first, second) is False

def test_find_placement_finds_free_space():
    product = {
        "sku": "TEST-001",
        "length_cm": 5,
        "width_cm": 5,
        "height_cm": 5,
        "weight_kg": 1,
    }

    box = {
        "inner_length_cm": 10,
        "inner_width_cm": 10,
        "inner_height_cm": 10,
        "max_payload_kg": 10,
    }

    existing_placement = {
        "sku": "TEST-000",
        "x_cm": 0, "y_cm": 0, "z_cm": 0,
        "length_cm": 5, "width_cm": 5, "height_cm": 5,
        "weight_kg": 1,
    }

    placement = find_placement(product, box, [existing_placement])

    assert placement is not None
    assert placements_overlap(placement, existing_placement) is False

def test_build_packing_plan_returns_box_for_fitting_product():
    product = {
        "sku": "TEST-001",
        "length_cm": 5,
        "width_cm": 5,
        "height_cm": 5,
        "weight_kg": 1,
    }

    box_type = {
        "code": "BOX-TEST",
        "capacity_liters": 1,
        "inner_length_cm": 10,
        "inner_width_cm": 10,
        "inner_height_cm": 10,
        "max_payload_kg": 5,
        "empty_weight_kg": 0.1,
    }

    plan = build_packing_plan([product], [box_type])

    assert len(plan["boxes"]) == 1
    assert plan["boxes"][0]["box_code"] == "BOX-TEST"
    assert len(plan["boxes"][0]["placements"]) == 1
    assert plan["special_handling"] == []

def test_build_packing_plan_marks_product_that_cannot_fit():
    product = {
        "sku": "TEST-LONG",
        "length_cm": 20,
        "width_cm": 3,
        "height_cm": 3,
        "weight_kg": 1,
    }

    box_type = {
        "code": "BOX-TEST",
        "capacity_liters": 1,
        "inner_length_cm": 10,
        "inner_width_cm": 10,
        "inner_height_cm": 10,
        "max_payload_kg": 5,
        "empty_weight_kg": 0.1,
    }

    plan = build_packing_plan([product], [box_type])

    assert plan["boxes"] == []
    assert plan["special_handling"] == [
        {
            "sku": "TEST-LONG",
            "quantity": 1,
            "reason": "No available box type can fit this product",
        }
    ]