import os

from fastapi.testclient import TestClient

from .context import main


client = TestClient(main.app)


def test_addWatermark():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = {"url_": "https://propsamc-data-staging.s3.amazonaws.com/Online_Projects/PRMB0B2531_145604572553.jpg"}
    response = client.post("/addWatermark", headers=headers, json=data)
    assert response.status_code == 200

    data = {"url_": "https://propsamc-data-staging.s3.amazonaws.com/Online_Prdsdojects/PRMB0B2531_145604572553.jpg"}
    response = client.post("/addWatermark", headers=headers, json=data)
    assert response.status_code == 500

    data = {"url_": "https://google.com"}
    response = client.post("/addWatermark", headers=headers, json=data)
    assert response.status_code == 406

    data = {"url_": "https://propsamc-data-staging.s3.amazonaws.com/Online_Projects/PRMB0B2531_145604572553.jpg", "width_percentage": 1.1}
    response = client.post("/addWatermark", headers=headers, json=data)
    assert response.status_code == 406
