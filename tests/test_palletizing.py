from app.palletizing import footprint_is_supported, box_fits_pallet_at


def test_box_fits_on_pallet():
    box = {
        "outer_length_cm": 50,
        "outer_width_cm": 40,
        "outer_height_cm": 35,
    }

    assert box_fits_pallet_at(box, x_cm=0, y_cm=0, z_cm=0) is True


def test_box_does_not_fit_when_past_pallet_edge():
    box = {
        "outer_length_cm": 50,
        "outer_width_cm": 40,
        "outer_height_cm": 35,
    }

    assert box_fits_pallet_at(box, x_cm=56, y_cm=0, z_cm=0) is False

def test_box_must_stay_within_loaded_height_limit():
    box = {
        "outer_length_cm": 50,
        "outer_width_cm": 40,
        "outer_height_cm": 35,
    }

    assert box_fits_pallet_at(box, x_cm=0, y_cm=0, z_cm=110) is True
    assert box_fits_pallet_at(box, x_cm=0, y_cm=0, z_cm=111) is False

def test_box_above_another_box_is_supported():
    lower_box = {
        "x_cm": 0, "y_cm": 0, "z_cm": 0,
        "outer_length_cm": 20,
        "outer_width_cm": 20,
        "outer_height_cm": 10,
    }
    upper_box = {
        "outer_length_cm": 20,
        "outer_width_cm": 20,
        "outer_height_cm": 10,
    }

    assert footprint_is_supported(
        upper_box, x_cm=0, y_cm=0, z_cm=10, placed_boxes=[lower_box]
    ) is True


def test_box_without_support_below_is_rejected():
    lower_box = {
        "x_cm": 0, "y_cm": 0, "z_cm": 0,
        "outer_length_cm": 20,
        "outer_width_cm": 20,
        "outer_height_cm": 10,
    }
    upper_box = {
        "outer_length_cm": 20,
        "outer_width_cm": 20,
        "outer_height_cm": 10,
    }

    assert footprint_is_supported(
        upper_box, x_cm=30, y_cm=0, z_cm=10, placed_boxes=[lower_box]
    ) is False