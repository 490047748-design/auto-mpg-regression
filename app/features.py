"""把经过校验的接口输入转换成训练时的特征格式。"""

import pandas as pd


FEATURE_COLUMNS = [
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


def payload_to_features(payload: dict) -> list[float]:
    """转换年份和产地，并按照固定顺序排列特征。"""
    return [
        float(payload["cylinders"]),
        float(payload["displacement"]),
        float(payload["horsepower"]),
        float(payload["weight"]),
        float(payload["acceleration"]),
        float(payload["model_year"] % 100),
        float(payload["origin"] == 1),
        float(payload["origin"] == 2),
        float(payload["origin"] == 3),
    ]


def to_frame(features: list[float]) -> pd.DataFrame:
    """生成模型要求的单行、带列名的 DataFrame。"""
    return pd.DataFrame([features], columns=FEATURE_COLUMNS)
