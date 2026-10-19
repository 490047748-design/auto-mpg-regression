"""Auto MPG 数据流水线的单元测试。"""

import pandas as pd
import pytest

from ml.data_pipeline import (
    RAW_COLUMNS,
    V2_FEATURE_COLUMNS,
    apply_iqr,
    coerce_horsepower,
    encode_origin,
    impute_horsepower,
    iqr_bounds,
    make_v1,
    make_v2,
    read_raw,
)


SAMPLE_RAW = """\
18.0 8 307.0 130.0 3504. 12.0 70 1 "chevrolet chevelle malibu"
25.0 4 97.0 ? 2046. 19.0 71 3 "toyota corolla"
"""


@pytest.mark.unit
def test_read_raw_assigns_columns_and_preserves_rows(tmp_path):
    """读取原始文件时，应补全列名并保留全部记录。"""
    raw_path = tmp_path / "auto-mpg.data"
    raw_path.write_text(SAMPLE_RAW, encoding="utf-8")

    result = read_raw(raw_path)

    assert list(result.columns) == RAW_COLUMNS
    assert len(result) == 2
    assert result.loc[0, "car_name"] == "chevrolet chevelle malibu"


@pytest.mark.unit
def test_make_v1_preserves_missing_horsepower_marker(tmp_path):
    """v1 只做格式转换，不应提前清洗 horsepower 的问号。"""
    raw_path = tmp_path / "auto-mpg.data"
    output_path = tmp_path / "auto_mpg_v1.csv"
    raw_path.write_text(SAMPLE_RAW, encoding="utf-8")

    make_v1(raw_path, output_path)
    result = pd.read_csv(output_path, dtype={"horsepower": "string"})

    assert output_path.exists()
    assert len(result) == 2
    assert result.loc[1, "horsepower"] == "?"


@pytest.mark.unit
def test_coerce_horsepower_converts_question_mark_to_nan():
    """问号应转为 NaN，正常数字字符串应转为浮点数。"""
    source = pd.DataFrame(
        {
            "horsepower": ["130.0", "?", "95.0"],
        }
    )

    result = coerce_horsepower(source)

    assert result.loc[0, "horsepower"] == 130.0
    assert pd.isna(result.loc[1, "horsepower"])
    assert result.loc[2, "horsepower"] == 95.0
    assert source.loc[1, "horsepower"] == "?"


@pytest.mark.unit
def test_impute_horsepower_uses_median_without_changing_source():
    """缺失马力应使用中位数填补，输入数据保持不变。"""
    source = pd.DataFrame(
        {
            "horsepower": [100.0, float("nan"), 200.0],
        }
    )

    result, used_median = impute_horsepower(source)

    assert used_median == 150.0
    assert result["horsepower"].tolist() == [100.0, 150.0, 200.0]
    assert pd.isna(source.loc[1, "horsepower"])


@pytest.mark.unit
def test_encode_origin_creates_stable_one_hot_columns():
    """即使样本缺少某个产地，也必须保持三个固定的 origin 特征。"""
    source = pd.DataFrame(
        {
            "mpg": [18.0, 25.0],
            "origin": [1, 3],
        }
    )

    result = encode_origin(source)

    assert "origin" not in result.columns
    assert result["origin_1"].tolist() == [1, 0]
    assert result["origin_2"].tolist() == [0, 0]
    assert result["origin_3"].tolist() == [0, 1]


@pytest.mark.unit
def test_iqr_bounds_and_filter_remove_extreme_mpg():
    """IQR 应保留正常记录并删除明显的高端异常值。"""
    source = pd.DataFrame(
        {
            "mpg": [10.0, 11.0, 12.0, 13.0, 100.0],
        }
    )

    lower, upper = iqr_bounds(source)
    result = apply_iqr(source, lower, upper)

    assert lower == 8.0
    assert upper == 16.0
    assert result["mpg"].tolist() == [10.0, 11.0, 12.0, 13.0]
    assert len(source) == 5


@pytest.mark.unit
def test_make_v2_creates_clean_model_ready_csv(tmp_path):
    """v2 应完成缺失值、类别、异常值处理并输出固定模型特征。"""
    v1_path = tmp_path / "auto_mpg_v1.csv"
    output_path = tmp_path / "auto_mpg_v2.csv"
    source = pd.DataFrame(
        {
            "mpg": [10.0, 11.0, 12.0, 13.0, 100.0],
            "cylinders": [4, 4, 6, 6, 8],
            "displacement": [100.0, 110.0, 120.0, 130.0, 140.0],
            "horsepower": ["100.0", "?", "120.0", "130.0", "140.0"],
            "weight": [2000.0, 2100.0, 2200.0, 2300.0, 2400.0],
            "acceleration": [15.0, 16.0, 17.0, 18.0, 19.0],
            "model_year": [70, 71, 72, 73, 74],
            "origin": [1, 2, 3, 1, 3],
            "car_name": ["a", "b", "c", "d", "e"],
        }
    )
    source.to_csv(v1_path, index=False)

    make_v2(v1_path, output_path)
    result = pd.read_csv(output_path)

    assert list(result.columns) == ["mpg"] + V2_FEATURE_COLUMNS
    assert len(result) == 4
    assert result["horsepower"].isna().sum() == 0
    assert result.loc[result["mpg"] == 11.0, "horsepower"].iloc[0] == 125.0
    assert 100.0 not in result["mpg"].tolist()
