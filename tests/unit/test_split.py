"""检查数据划分是否隔离、完整且可重复。"""

import pandas as pd

from ml.split import split_records


def sample_records():
    """构造小数据，避免单元测试依赖 Azure 或本地 CSV。"""
    return pd.DataFrame(
        {
            "horsepower": [str(70 + i) for i in range(20)] + ["?", "?"],
            "mpg": [float(20 + i) for i in range(22)],
        }
    )


def test_split_keeps_missing_horsepower_in_training():
    source = sample_records()

    train, test = split_records(source)

    assert len(train) == 18
    assert len(test) == 4
    assert train["horsepower"].isna().sum() == 2
    assert test["horsepower"].notna().all()


def test_split_has_no_overlap_and_preserves_all_records():
    source = sample_records()
    original = source.copy(deep=True)

    train, test = split_records(source)

    assert set(train.index).isdisjoint(test.index)
    assert set(train.index) | set(test.index) == set(source.index)
    pd.testing.assert_frame_equal(source, original)


def test_split_is_reproducible():
    source = sample_records()

    train_first, test_first = split_records(source, random_state=42)
    train_second, test_second = split_records(source, random_state=42)

    pd.testing.assert_frame_equal(train_first, train_second)
    pd.testing.assert_frame_equal(test_first, test_second)
