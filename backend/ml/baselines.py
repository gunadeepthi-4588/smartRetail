import numpy as np
import pandas as pd

class NaiveBaseline:
    """
    Naive Forecast Benchmark:
    Predicts tomorrow's demand will be equal to yesterday's demand (lag_1).
    """
    def __init__(self):
        self.name = "Naive (Lag-1)"

    def fit(self, X, y=None):
        return self

    def predict(self, X):
        """
        If 'lag_1' column exists in X DataFrame, uses lag_1.
        Otherwise predicts the mean or zero.
        """
        if isinstance(X, pd.DataFrame) and "lag_1" in X.columns:
            return np.maximum(0, X["lag_1"].values)
        return np.zeros(len(X))


class MovingAverageBaseline:
    """
    Moving Average Benchmark:
    Predicts tomorrow's demand will be equal to the average of the last `window` days.
    """
    def __init__(self, window=7):
        self.window = window
        self.name = f"Moving Average ({window}-Day)"

    def fit(self, X, y=None):
        return self

    def predict(self, X):
        """
        If f'rolling_mean_{self.window}' exists in X DataFrame, uses that column.
        Otherwise falls back to lag_1 or 0.
        """
        col = f"rolling_mean_{self.window}"
        if isinstance(X, pd.DataFrame) and col in X.columns:
            return np.maximum(0, X[col].values)
        elif isinstance(X, pd.DataFrame) and "lag_1" in X.columns:
            return np.maximum(0, X["lag_1"].values)
        return np.zeros(len(X))
