from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
import joblib

from indicators.base import BaseIndicator


class MLIndicator(BaseIndicator):
    """
    Wraps a trained sklearn-compatible model as a first-class indicator.

    Prevents look-ahead by shifting predictions forward by `shift` bars:
    prediction for bar[i] is based on features available at bar[i],
    but is only surfaced to the strategy at bar[i+shift].

    Usage:
        import joblib
        from indicators.ml import MLIndicator

        def my_features(df):
            import pandas_ta as ta
            rsi = ta.rsi(df["close"], length=14)
            return pd.DataFrame({"rsi": rsi, "ret": df["close"].pct_change()})

        ml_ind = MLIndicator(
            name="rf_signal",
            model_path="models/rf.pkl",
            feature_fn=my_features,
            output_type="probability",
        )
        library.register(ml_ind)

        # In strategy:
        prob = self.indicators.custom("rf_signal")
        signals[prob > 0.65] = Signal.BUY
    """

    def __init__(
        self,
        name: str,
        model_path: str,
        feature_fn: Callable[[pd.DataFrame], pd.DataFrame],
        output_type: str = "probability",  # "probability" | "class" | "regression"
        class_index: int = 1,
        shift: int = 1,
    ):
        self._name = name
        self._model = joblib.load(model_path)
        self._feature_fn = feature_fn
        self._output_type = output_type
        self._class_index = class_index
        self._shift = shift

    @property
    def name(self) -> str:
        return self._name

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        features: pd.DataFrame = self._feature_fn(df)
        valid_mask = features.notna().all(axis=1)
        X = features[valid_mask].values

        if self._output_type == "probability":
            preds = self._model.predict_proba(X)[:, self._class_index]
        elif self._output_type == "class":
            preds = self._model.predict(X).astype(float)
        else:
            preds = self._model.predict(X).astype(float)

        result = pd.Series(np.nan, index=df.index, name=self._name)
        result[valid_mask] = preds
        return result.shift(self._shift)
