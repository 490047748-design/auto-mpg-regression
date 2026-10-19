"""训练 baseline，并用本地 MLflow 保存实验记录。"""

from sklearn.model_selection import KFold, cross_val_score
from ml.modeling import build_improved_model, prepare_improved_features

import argparse
import hashlib
from pathlib import Path
import subprocess

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)

from ml.split import split_records


FEATURES = [
    "cylinders",
    "displacement",
    "horsepower",
    "weight",
    "acceleration",
    "model_year",
    "origin",
]


def git_output(*args: str) -> str:
    """读取 Git 信息；命令失败时立即报错。"""
    return subprocess.check_output(
        ["git", *args],
        text=True,
        encoding="utf-8",
    ).strip()


def data_fingerprint(data_path: Path) -> str:
    """读取 DVC 指纹，并确认实际 CSV 与指针一致。"""
    pointer_path = Path(str(data_path) + ".dvc")
    pointer = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
    expected = pointer["outs"][0]["md5"]
    actual = hashlib.md5(data_path.read_bytes()).hexdigest()

    if actual != expected:
        raise ValueError("CSV 内容与 DVC 指针不一致，请先检查数据版本")

    return expected


def train_model(
    data_path: Path,
    run_name: str,
    stage: str,
    model_type: str = "linear",
    alpha: float = 1.0,
) -> None:
    """训练并记录 baseline 或 improved 实验。"""
    if git_output("status", "--porcelain"):
        raise RuntimeError("请先提交代码并保持工作区干净，再正式记录实验")

    code_version = git_output("rev-parse", "HEAD")
    data_version = data_fingerprint(data_path)

    data = pd.read_csv(data_path)
    train, test = split_records(data, test_size=0.2, random_state=42)

    if stage == "baseline":
        train = train.dropna(subset=["horsepower"])
        X_train = train[FEATURES]
        X_test = test[FEATURES]
        model = LinearRegression()
    else:
        X_train = prepare_improved_features(train)
        X_test = prepare_improved_features(test)
        model = build_improved_model(model_type=model_type, alpha=alpha)

    y_train = train["mpg"]
    y_test = test["mpg"]

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("AutoMPG_Regression")

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags(
            {
                "code_version": code_version,
                "data_version": data_version,
                "stage": stage,
            }
        )

        mlflow.log_params(
            {
                "model_type": model_type,
                "scale": stage == "improved",
                "test_size": 0.2,
                "random_state": 42,
                "n_train": len(train),
                "n_test": len(test),
                "n_features": X_train.shape[1],
                "data_path": str(data_path),
            }
        )
        if model_type == "ridge":
            mlflow.log_param("alpha", alpha)

        if stage == "improved":
            cv = KFold(n_splits=5, shuffle=True, random_state=42)
            scores = cross_val_score(
                model,
                X_train,
                y_train,
                cv=cv,
                scoring="neg_root_mean_squared_error",
            )
            cv_rmse = float(-scores.mean())

            mlflow.log_param("cv_folds", 5)
            mlflow.log_metric("cv_rmse", cv_rmse)
            print(f"CV RMSE: {cv_rmse:.4f}")

        model.fit(X_train, y_train)
        predictions = model.predict(X_test)

        if stage == "improved":
            horsepower_position = X_train.columns.get_loc("horsepower")
            median = float(model.named_steps["imputer"].statistics_[horsepower_position])
            mlflow.log_param("train_horsepower_median", median)
            print(f"Training horsepower median: {median:.1f}")

        metrics = {
            "rmse": float(root_mean_squared_error(y_test, predictions)),
            "mae": float(mean_absolute_error(y_test, predictions)),
            "r2": float(r2_score(y_test, predictions)),
        }
        mlflow.log_metrics(metrics)

        mlflow.log_dict(
            {
                "train_indices": train.index.tolist(),
                "test_indices": test.index.tolist(),
                "feature_columns": X_train.columns.tolist(),
            },
            "split_and_features.json",
        )

        fig, ax = plt.subplots()
        ax.scatter(predictions, y_test.to_numpy() - predictions, alpha=0.7)
        ax.axhline(0, color="red", linestyle="--")
        ax.set_xlabel("Predicted MPG")
        ax.set_ylabel("Residual (actual - predicted)")
        ax.set_title(f"{stage.capitalize()} residuals")
        fig.tight_layout()
        mlflow.log_figure(fig, "residual_plot.png")
        plt.close(fig)

        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            input_example=X_train.head(3),
            registered_model_name="AutoMPG_LinearRegression",
            skops_trusted_types=["numpy.dtype"],
        )

        print("run_id:", run.info.run_id)
        print("code_version:", code_version)
        print("data_version:", data_version)
        print(f"n_train={len(train)}, n_test={len(test)}")
        for name, value in metrics.items():
            print(f"{name}: {value:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto MPG baseline 训练")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/auto_mpg_v1.csv"),
    )
    parser.add_argument("--run-name", default="baseline-v1")
    parser.add_argument(
        "--stage",
        choices=["baseline", "improved"],
        default="baseline",
    )
    parser.add_argument(
        "--model-type",
        choices=["linear", "ridge"],
        default="linear",
    )
    parser.add_argument("--alpha", type=float, default=1.0)
    args = parser.parse_args()

    if args.stage == "baseline" and args.model_type != "linear":
        parser.error("本课程 baseline 固定使用 linear；Ridge 请搭配 --stage improved")

    if args.model_type == "ridge" and not 0 < args.alpha < float("inf"):
        parser.error("--alpha 必须是有限正数")

    train_model(
        args.data,
        args.run_name,
        args.stage,
        args.model_type,
        args.alpha,
    )


if __name__ == "__main__":
    main()
