"""加载已经训练并导出的模型。"""

import os
from pathlib import Path

import joblib

from app.features import FEATURE_COLUMNS


def load_model():
    """读取模型，并确认输入列与接口一致。"""
    default_path = Path(__file__).resolve().parent / "model" / "linear_regression.pkl"
    model_path = Path(os.getenv("MODEL_PATH", str(default_path)))

    if not model_path.is_file():
        raise FileNotFoundError(f"模型文件不存在：{model_path}")

    model = joblib.load(model_path)

    actual_columns = list(getattr(model, "feature_names_in_", []))
    if actual_columns != FEATURE_COLUMNS:
        raise ValueError(f"模型输入列不匹配：期望 {FEATURE_COLUMNS}，实际 {actual_columns}")

    return model
