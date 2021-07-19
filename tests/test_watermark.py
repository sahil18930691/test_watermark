import os

from fastapi.testclient import TestClient

from .context import main


client = TestClient(main.app)


def test_addWatermark():
    params = {"URL": "https://propsamc-data-staging.s3.amazonaws.com/Online_Projects/PRMB0B2531_145604572553.jpg"}
    response = client.get("/addWatermark", params=params)
    assert response.status_code == 200

    params = {"URL": "https://propsamc-data-staging.s3.amazonaws.com/Online_Prdsdojects/PRMB0B2531_145604572553.jpg"}
    response = client.get("/addWatermark", params=params)
    assert response.status_code == 500

    params = {"URL": "https://google.com"}
    response = client.get("/addWatermark", params=params)
    assert response.status_code == 400
