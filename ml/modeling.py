"""构建 improved 特征和训练流水线。"""

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
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


def build_improved_model() -> Pipeline:
    """将中位数填补、标准化、线性回归封装为一个模型。"""
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("regressor", LinearRegression()),
        ]
    )
