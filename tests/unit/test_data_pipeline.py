"""Auto MPG 数据流水线的单元测试。"""

import pandas as pd
import pytest

from ml.data_pipeline import RAW_COLUMNS, make_v1, read_raw


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