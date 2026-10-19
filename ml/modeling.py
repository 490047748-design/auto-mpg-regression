"""构建 improved 特征和训练流水线。"""

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.data_pipeline import (
    V2_FEATURE_COLUMNS,
    coerce_horsepower,
    encode_origin,
)


def prepare_improved_features(data: pd.DataFrame) -> pd.DataFrame:
    """转换马力和产地，保留缺失值供训练流水线处理。"""
    prepared = coerce_horsepower(data)
    prepared = encode_origin(prepared)

    return prepared[V2_FEATURE_COLUMNS].copy()


def build_improved_model(
    model_type: str = "linear",
    alpha: float = 1.0,
) -> Pipeline:
    """构建预处理流程，并选择线性回归或 Ridge。"""
    if model_type == "linear":
        regressor = LinearRegression()
    elif model_type == "ridge":
        if not 0 < alpha < float("inf"):
            raise ValueError("Ridge 的 alpha 必须是有限正数")
        regressor = Ridge(alpha=alpha)
    else:
        raise ValueError(f"不支持的模型类型: {model_type}")

    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("regressor", regressor),
        ]
    )
