import app.main as main
from fastapi.testclient import TestClient


def test_outbound_rejects_zero_quantity(monkeypatch):
    monkeypatch.setattr(main, "initialize_database", lambda: None)

    with TestClient(main.app) as client:
        response = client.post(
            "/outbound/plan",
            json={"items": [{"sku": "CAB-050", "quantity": 0}]},
        )

    assert response.status_code == 422

def test_outbound_plan_returns_all_three_stages(monkeypatch):
    products = [{"sku": "TEST-001"}]
    box_types = [{"code": "BOX-TEST"}]

    packing_result = {"boxes": [{"box_code": "BOX-TEST"}]}
    pallet_result = {"pallets": [{"pallet_number": 1}]}
    truck_result = {"trucks": [{"truck_number": 1}]}

    monkeypatch.setattr(main, "initialize_database", lambda: None)
    monkeypatch.setattr(
        main, "prepare_packing_products", lambda request: products
    )
    monkeypatch.setattr(main, "get_box_types", lambda: box_types)
    monkeypatch.setattr(
        main, "build_packing_plan", lambda products, boxes: packing_result
    )
    monkeypatch.setattr(
        main, "build_pallet_plan", lambda boxes, box_types: pallet_result
    )
    monkeypatch.setattr(
        main, "build_truck_plan", lambda pallets: truck_result
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/outbound/plan",
            json={"items": [{"sku": "TEST-001", "quantity": 1}]},
        )

    assert response.status_code == 200
    assert response.json() == {
        "packing": packing_result,
        "palletization": pallet_result,
        "trucking": truck_result,
    }