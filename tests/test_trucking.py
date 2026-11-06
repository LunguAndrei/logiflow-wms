from app.trucking import build_truck_plan, pallet_fits_in_truck_at


def test_pallet_fits_in_truck():
    pallet = {"loaded_height_cm": 160}

    assert pallet_fits_in_truck_at(pallet, x_cm=0, y_cm=0) is True


def test_pallet_outside_truck_width_is_rejected():
    pallet = {"loaded_height_cm": 160}

    assert pallet_fits_in_truck_at(pallet, x_cm=140, y_cm=0) is False


def test_pallet_too_tall_for_truck_is_rejected():
    pallet = {"loaded_height_cm": 241}

    assert pallet_fits_in_truck_at(pallet, x_cm=0, y_cm=0) is False

def test_truck_plan_uses_second_truck_when_first_is_full():
    pallets = [
        {
            "pallet_number": number,
            "total_weight_kg": 50,
            "loaded_height_cm": 100,
        }
        for number in range(1, 16)
    ]

    plan = build_truck_plan(pallets)

    assert len(plan["trucks"]) == 2
    assert plan["trucks"][0]["pallet_count"] == 14
    assert plan["trucks"][1]["pallet_count"] == 1