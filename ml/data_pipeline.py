"""Auto MPG 数据流水线：从 UCI 原始文件生成版本化数据集。"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


RAW_COLUMNS = [
    "mpg",
    "cylinders",
    "displacement",
    "horsepower",
    "weight",
    "acceleration",
    "model_year",
    "origin",
    "car_name",
]

V2_FEATURE_COLUMNS = [
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


def read_raw(raw_path: Path) -> pd.DataFrame:
    """读取无表头、以空白分隔的 Auto MPG 原始数据。"""
    return pd.read_csv(
        raw_path,
        sep=r"\s+",
        header=None,
        names=RAW_COLUMNS,
    )


def coerce_horsepower(df: pd.DataFrame) -> pd.DataFrame:
    """把 horsepower 转成数值，无法转换的问号会变成 NaN。"""
    result = df.copy()
    result["horsepower"] = pd.to_numeric(
        result["horsepower"],
        errors="coerce",
    )
    return result


def impute_horsepower(
    df: pd.DataFrame,
    median: float | None = None,
) -> tuple[pd.DataFrame, float]:
    """使用中位数填补 horsepower 缺失值，并返回实际使用的中位数。"""
    result = df.copy()

    if median is None:
        median = float(result["horsepower"].median())

    result["horsepower"] = result["horsepower"].fillna(median)

    return result, float(median)


def encode_origin(df: pd.DataFrame) -> pd.DataFrame:
    """把 origin 类别展开成 origin_1、origin_2、origin_3 三个开关列。"""
    result = pd.get_dummies(
        df,
        columns=["origin"],
        prefix="origin",
        dtype=int,
    )

    for column in ("origin_1", "origin_2", "origin_3"):
        if column not in result.columns:
            result[column] = 0

    return result


def iqr_bounds(df: pd.DataFrame) -> tuple[float, float]:
    """计算 mpg 的 IQR 正常范围，并返回下界和上界。"""
    q1, q3 = df["mpg"].quantile([0.25, 0.75])
    iqr = q3 - q1

    lower = float(q1 - 1.5 * iqr)
    upper = float(q3 + 1.5 * iqr)

    return lower, upper


def apply_iqr(
    df: pd.DataFrame,
    lower: float,
    upper: float,
) -> pd.DataFrame:
    """只保留 mpg 位于 IQR 正常范围内的记录。"""
    mask = (df["mpg"] >= lower) & (df["mpg"] <= upper)
    return df.loc[mask].copy()


def make_v1(raw_path: Path, out_path: Path) -> None:
    """把原始数据转换成带表头的 v1 CSV，不进行清洗。"""
    df = read_raw(raw_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    missing_horsepower = int((df["horsepower"] == "?").sum())

    print(f"[v1] 读取 {raw_path} -> 写出 {out_path}")
    print(f"[v1] 行数={len(df)}，列={list(df.columns)}")
    print(f"[v1] horsepower 含 '?' 的行数: {missing_horsepower}")


def make_v2(v1_path: Path, out_path: Path) -> None:
    """从 v1 生成经过缺失值、类别和异常值处理的 v2。"""
    df = pd.read_csv(v1_path)
    original_rows = len(df)

    df = coerce_horsepower(df)
    missing_horsepower = int(df["horsepower"].isna().sum())
    df, median_horsepower = impute_horsepower(df)

    df = encode_origin(df)

    lower, upper = iqr_bounds(df)
    outlier_count = int(((df["mpg"] < lower) | (df["mpg"] > upper)).sum())
    df = apply_iqr(df, lower, upper)

    df = df[["mpg"] + V2_FEATURE_COLUMNS]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"[v2] 输入 {v1_path}（{original_rows} 行） -> 输出 {out_path}（{len(df)} 行）")
    print(
        f"[v2] 中位数填补 horsepower 缺失 {missing_horsepower} 处（中位数={median_horsepower:.1f}）"
    )
    print(f"[v2] IQR 剔除 mpg 异常行 {outlier_count} 行（区间 [{lower:.2f}, {upper:.2f}]）")
    print("[v2] origin 已 one-hot 编码为 origin_1/origin_2/origin_3")
    print(f"[v2] 最终列: {list(df.columns)}")


def main() -> None:
    """解析命令行参数并执行指定的数据版本任务。"""
    parser = argparse.ArgumentParser(description="Auto MPG 数据版本流水线")
    subparsers = parser.add_subparsers(dest="stage", required=True)

    parser_v1 = subparsers.add_parser(
        "v1",
        help="把 UCI 原始数据转换成 v1 CSV",
    )
    parser_v1.add_argument(
        "--raw",
        type=Path,
        required=True,
        help="UCI 原始 auto-mpg.data 文件",
    )
    parser_v1.add_argument(
        "--out",
        type=Path,
        required=True,
        help="生成的 v1 CSV 文件",
    )

    parser_v2 = subparsers.add_parser(
        "v2",
        help="把 v1 清洗并转换成 v2 CSV",
    )
    parser_v2.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        required=True,
        help="输入的 v1 CSV 文件",
    )
    parser_v2.add_argument(
        "--out",
        type=Path,
        required=True,
        help="生成的 v2 CSV 文件",
    )

    args = parser.parse_args()

    if args.stage == "v1":
        make_v1(args.raw, args.out)
    else:
        make_v2(args.in_path, args.out)


if __name__ == "__main__":
    main()
