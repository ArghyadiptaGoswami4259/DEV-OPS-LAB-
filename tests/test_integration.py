from app import app


def test_homepage():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["application"] == "DevOps Lab 4"
    assert data["author"] == "Arghyadipta Goswami"
    assert data["roll"] == "2301010192"
    assert data["section"] == "C"
    assert data["subject"] == "DEV OPS AUTOMATION"
    assert data["year"] == "2023-2027"


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_version():
    client = app.test_client()
    response = client.get("/")
    assert response.get_json()["version"] == "v1"
