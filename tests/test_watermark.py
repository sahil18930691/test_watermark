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
    assert response.status_code == 400

    data = {"url_": "https://google.com"}
    response = client.post("/addWatermark", headers=headers, json=data)
    assert response.status_code == 406

    data = {"url_": "https://propsamc-data-staging.s3.amazonaws.com/Online_Projects/PRMB0B2531_145604572553.jpg", "width_percentage": 1.1}
    response = client.post("/addWatermark", headers=headers, json=data)
    assert response.status_code == 406


def test_extract_filename():
    filename = main.extract_filename("https://images.unsplash.com/photo-1626080308314-d7868286cce2?ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&ixlib=rb-1.2.1&auto=format&fit=crop&w=334&q=80")
    assert filename == "photo-1626080308314-d7868286cce2"

    filename = main.extract_filename("https://propsamc-data-staging.s3.amazonaws.com/Online_Projects/PRMBH9HETA_151115995347.jpg")
    assert filename == "PRMBH9HETA_151115995347.jpg"
