"""使用真实导出模型验证预测接口。"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


pytestmark = pytest.mark.api

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
    """固定测试配置，并执行应用的启动和关闭流程。"""
    monkeypatch.setenv("MODEL_PATH", str(MODEL_PATH))
    monkeypatch.setenv("MODEL_VERSION", "6")
    monkeypatch.setenv("APP_ENV", "test")

    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_info(client):
    response = client.get("/model-info")

    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "6"
    assert data["app_env"] == "test"
    assert data["unit"] == "mpg"
    assert data["feature_columns"] == [
        "cylinders",
        "displacement",
        "horsepower",
        "weight",
        "acceleration",
        "model_year",
        "origin_1",
        "origin_2",
        "origin_3",
    ]


def test_homepage(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="prediction-form"' in response.text


def test_predict_valid_input(client):
    response = client.post("/predict", json=VALID_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["mpg"] == pytest.approx(29.15996, abs=0.001)
    assert data["unit"] == "mpg"
    assert data["model_version"] == "6"
    assert data["app_env"] == "test"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("weight", -5),
        ("weight", 0),
        ("weight", 6001),
        ("cylinders", 2),
        ("cylinders", 13),
        ("displacement", 0),
        ("displacement", 1001),
        ("horsepower", -1),
        ("horsepower", 0),
        ("horsepower", 601),
        ("acceleration", -1),
        ("acceleration", 0),
        ("acceleration", 41),
        ("origin", 0),
        ("origin", 4),
        ("model_year", 1969),
        ("model_year", 1983),
        ("model_year", 2000),
        ("model_year", 2050),
        ("model_year", 2082),
        ("model_year", 2101),
    ],
)
def test_predict_rejects_invalid_values(client, field, value):
    payload = {**VALID_PAYLOAD, field: value}
    response = client.post("/predict", json=payload)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"] == ["body", field] for error in errors)


def test_predict_rejects_missing_field(client):
    payload = VALID_PAYLOAD.copy()
    del payload["horsepower"]

    response = client.post("/predict", json=payload)

    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "horsepower"] and error["type"] == "missing"
        for error in response.json()["detail"]
    )


def test_predict_rejects_extra_field(client):
    payload = {**VALID_PAYLOAD, "unexpected": 123}
    response = client.post("/predict", json=payload)

    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "unexpected"] and error["type"] == "extra_forbidden"
        for error in response.json()["detail"]
    )


def test_startup_fails_without_model(monkeypatch, tmp_path):
    missing_path = tmp_path / "missing_model.pkl"
    monkeypatch.setenv("MODEL_PATH", str(missing_path))

    with pytest.raises(FileNotFoundError, match="模型文件不存在"):
        with TestClient(app):
            pass


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("weight", "not-a-number"),
        ("horsepower", None),
        ("cylinders", 4.5),
        ("origin", [1]),
        ("model_year", "unknown"),
    ],
)
def test_predict_rejects_invalid_types(client, field, value):
    """错误类型应返回 422，并指出具体字段。"""
    payload = {**VALID_PAYLOAD, field: value}
    response = client.post("/predict", json=payload)

    assert response.status_code == 422
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])


@pytest.mark.parametrize("year", [1970, 1982])
def test_predict_accepts_year_boundaries(client, year):
    """合法年份的两个端点都应被接受。"""
    payload = {**VALID_PAYLOAD, "model_year": year}
    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert isinstance(response.json()["mpg"], (int, float))


def test_predict_rejects_malformed_json(client):
    """JSON 缺少逗号时，应返回解析错误，而不是服务器错误。"""
    response = client.post(
        "/predict",
        content='{"weight": -5 "origin": 1}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert any(error["type"] == "json_invalid" for error in response.json()["detail"])
