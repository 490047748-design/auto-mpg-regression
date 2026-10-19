"""为不同模型方案提供同一份训练集和测试集。"""

import pandas as pd
from sklearn.model_selection import train_test_split

from ml.data_pipeline import coerce_horsepower


def split_records(
    data: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """将马力缺失记录放入训练集，并固定完整记录的划分。"""
    if not data.index.is_unique:
        raise ValueError("每条记录必须具有唯一索引")

    prepared = coerce_horsepower(data)

    missing_mask = prepared["horsepower"].isna()
    complete = prepared.loc[~missing_mask]
    missing = prepared.loc[missing_mask]

    train_complete, test = train_test_split(
        complete,
        test_size=test_size,
        random_state=random_state,
    )

    train = pd.concat([train_complete, missing])

    return train.copy(), test.copy()
