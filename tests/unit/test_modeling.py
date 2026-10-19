"""验证 improved 特征和训练预处理的行为。"""

import numpy as np
import pandas as pd

from ml.data_pipeline import V2_FEATURE_COLUMNS
from ml.modeling import build_improved_model, prepare_improved_features


def test_features_preserve_missing_values_and_fixed_columns():
    source = pd.DataFrame(
        {
            "mpg": [20.0, 30.0],
            "cylinders": [4, 6],
            "displacement": [100.0, 150.0],
            "horsepower": ["?", "100"],
            "weight": [2000.0, 2500.0],
            "acceleration": [15.0, 16.0],
            "model_year": [75, 80],
            "origin": [1, 3],
            "car_name": ["car A", "car B"],
        }
    )
    original = source.copy(deep=True)

    features = prepare_improved_features(source)

    assert list(features.columns) == V2_FEATURE_COLUMNS
    assert len(features) == len(source)
    assert features["horsepower"].isna().sum() == 1
    assert features["origin_1"].tolist() == [1, 0]
    assert features["origin_2"].tolist() == [0, 0]
    assert features["origin_3"].tolist() == [0, 1]
    pd.testing.assert_frame_equal(source, original)


def test_prediction_reuses_training_median():
    X_train = pd.DataFrame({"horsepower": [10.0, 20.0, np.nan, 30.0]})
    y_train = pd.Series([1.0, 2.0, 2.0, 3.0])
    X_test = pd.DataFrame({"horsepower": [1000.0, np.nan]})

    model = build_improved_model()
    model.fit(X_train, y_train)

    imputer = model.named_steps["imputer"]
    assert imputer.statistics_[0] == 20.0

    predictions = model.predict(X_test)
    filled_test = imputer.transform(X_test)

    assert filled_test[1, 0] == 20.0
    assert imputer.statistics_[0] == 20.0
    assert np.isfinite(predictions).all()
