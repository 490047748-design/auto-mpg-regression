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


def read_raw(raw_path: Path) -> pd.DataFrame:
    """读取无表头、以空白分隔的 Auto MPG 原始数据。"""
    return pd.read_csv(
        raw_path,
        sep=r"\s+",
        header=None,
        names=RAW_COLUMNS,
    )


def make_v1(raw_path: Path, out_path: Path) -> None:
    """把原始数据转换成带表头的 v1 CSV，不进行清洗。"""
    df = read_raw(raw_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    missing_horsepower = int((df["horsepower"] == "?").sum())

    print(f"[v1] 读取 {raw_path} -> 写出 {out_path}")
    print(f"[v1] 行数={len(df)}，列={list(df.columns)}")
    print(f"[v1] horsepower 含 '?' 的行数: {missing_horsepower}")


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

    args = parser.parse_args()

    if args.stage == "v1":
        make_v1(args.raw, args.out)


if __name__ == "__main__":
    main()