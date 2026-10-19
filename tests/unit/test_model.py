"""验证导出模型及训练端、服务端的特征契约。"""

from pathlib import Path

import pandas as pd
import pytest

from app.features import FEATURE_COLUMNS, payload_to_features, to_frame
from app.model import load_model
from ml.data_pipeline import V2_FEATURE_COLUMNS
from ml.modeling import prepare_improved_features


pytestmark = pytest.mark.unit

MODEL_PATH = Path(__file__).resolve().parents[2] / "app" / "model" / "linear_regression.pkl"

SAMPLE = {
    "cylinders": 4,
    "displacement": 120,
    "horsepower": 79,
    "weight": 2625,
    "acceleration": 18.6,
    "model_year": 1982,
    "origin": 1,
}


@pytest.fixture
def model(monkeypatch):
    """明确加载本项目导出的模型，避免环境变量干扰。"""
    monkeypatch.setenv("MODEL_PATH", str(MODEL_PATH))
    return load_model()


def predict_one(model, payload):
    frame = to_frame(payload_to_features(payload))
    return float(model.predict(frame)[0])


def test_feature_contract_matches_training_and_model(model):
    """服务列序必须同时匹配训练代码和已导出的模型。"""
    assert FEATURE_COLUMNS == V2_FEATURE_COLUMNS
    assert FEATURE_COLUMNS == list(model.feature_names_in_)
    assert model.n_features_in_ == 9


@pytest.mark.parametrize(
    ("origin", "expected"),
    [
        (1, [1.0, 0.0, 0.0]),
        (2, [0.0, 1.0, 0.0]),
        (3, [0.0, 0.0, 1.0]),
    ],
)
def test_origin_one_hot_expansion(origin, expected):
    payload = {**SAMPLE, "origin": origin}
    frame = to_frame(payload_to_features(payload))

    actual = frame.loc[0, ["origin_1", "origin_2", "origin_3"]].tolist()

    assert frame.shape == (1, 9)
    assert actual == expected


@pytest.mark.parametrize(
    ("year", "expected"),
    [(1970, 70.0), (1977, 77.0), (1982, 82.0)],
)
def test_year_conversion(year, expected):
    payload = {**SAMPLE, "model_year": year}
    frame = to_frame(payload_to_features(payload))

    assert frame.loc[0, "model_year"] == expected


@pytest.mark.parametrize("origin", [1, 2, 3])
def test_serving_features_match_training_features(origin):
    """同一辆车在两条转换路径中必须得到相同的特征。"""
    payload = {**SAMPLE, "origin": origin}

    serving_frame = to_frame(payload_to_features(payload))

    # 原始训练数据中的年份是两位数，horsepower 可以是字符串。
    raw_record = {
        **payload,
        "model_year": 82,
        "horsepower": "79",
    }
    training_frame = prepare_improved_features(pd.DataFrame([raw_record]))

    pd.testing.assert_frame_equal(
        serving_frame,
        training_frame,
        check_dtype=False,
    )


def test_fixed_sample_prediction(model):
    """守住当前导出模型的固定样本预测结果。"""
    prediction = predict_one(model, SAMPLE)

    assert prediction == pytest.approx(29.15996, abs=0.001)


@pytest.mark.parametrize("extra_weight", [100, 400, 800])
def test_heavier_car_predicted_lower_mpg(model, extra_weight):
    """检查当前模型在固定其他特征时的车重响应方向。"""
    heavier = {
        **SAMPLE,
        "weight": SAMPLE["weight"] + extra_weight,
    }

    assert predict_one(model, heavier) < predict_one(model, SAMPLE)


@pytest.mark.parametrize("older_year", [1970, 1977, 1981])
def test_newer_car_predicted_higher_mpg(model, older_year):
    """检查当前模型在训练年份范围内的年份响应方向。"""
    older = {**SAMPLE, "model_year": older_year}

    assert predict_one(model, SAMPLE) > predict_one(model, older)
