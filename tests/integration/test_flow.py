"""验证真实模型参与的应用调用流程。"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


pytestmark = pytest.mark.integration

MODEL_PATH = Path(__file__).resolve().parents[2] / "app" / "model" / "linear_regression.pkl"

VALID_PAYLOAD = {
    "cylinders": 4,
    "displacement": 120,
    "horsepower": 79,
    "weight": 2625,
    "acceleration": 18.6,
    "model_year": 1982,
    "origin": 1,
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("MODEL_PATH", str(MODEL_PATH))
    monkeypatch.setenv("MODEL_VERSION", "6")
    monkeypatch.setenv("APP_ENV", "test")

    with TestClient(app) as test_client:
        yield test_client


def test_complete_prediction_flow(client):
    """首页、健康检查、模型信息和预测在同一应用中正常工作。"""
    homepage = client.get("/")
    assert homepage.status_code == 200
    assert "text/html" in homepage.headers["content-type"]
    assert 'id="prediction-form"' in homepage.text

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    info_response = client.get("/model-info")
    assert info_response.status_code == 200
    info = info_response.json()

    assert len(info["feature_columns"]) == 9
    assert info["model_version"] == "6"
    assert info["app_env"] == "test"

    prediction_response = client.post("/predict", json=VALID_PAYLOAD)
    assert prediction_response.status_code == 200
    prediction = prediction_response.json()

    assert prediction["mpg"] == pytest.approx(29.15996, abs=0.001)
    assert prediction["model_version"] == info["model_version"]
    assert prediction["app_env"] == info["app_env"]
    assert prediction["unit"] == info["unit"] == "mpg"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("weight", -5),
        ("model_year", 2082),
        ("origin", 4),
    ],
)
def test_invalid_request_does_not_break_service(client, field, value):
    """非法请求被拒绝后，服务仍能正常处理下一次预测。"""
    before = client.post("/predict", json=VALID_PAYLOAD)
    assert before.status_code == 200

    invalid_payload = {**VALID_PAYLOAD, field: value}
    rejected = client.post("/predict", json=invalid_payload)

    assert rejected.status_code == 422
    assert any(error["loc"] == ["body", field] for error in rejected.json()["detail"])

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    after = client.post("/predict", json=VALID_PAYLOAD)
    assert after.status_code == 200
    assert after.json() == before.json()
