import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

class RidgeDemandModel:
    """
    Linear / Ridge Regression model with L2 regularization.
    Fast, highly interpretable baseline ML model.
    """
    def __init__(self, alpha=1.0, random_state=42):
        self.alpha = alpha
        self.random_state = random_state
        self.name = f"Ridge Regression (alpha={alpha})"
        self.model = Ridge(alpha=alpha, random_state=random_state)

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        raw_preds = self.model.predict(X)
        # Retail sales cannot be negative
        return np.maximum(0.0, raw_preds)

    @property
    def feature_importances_(self):
        return np.abs(self.model.coef_)


class RandomForestDemandModel:
    """
    Random Forest Regressor.
    Captures non-linear feature interactions and weekly seasonal patterns.
    """
    def __init__(self, n_estimators=50, max_depth=6, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.name = f"Random Forest (trees={n_estimators}, depth={max_depth})"
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        raw_preds = self.model.predict(X)
        # Retail sales cannot be negative
        return np.maximum(0.0, raw_preds)

    @property
    def feature_importances_(self):
        return self.model.feature_importances_


class GradientBoostingDemandModel:
    """
    Gradient Boosting Regressor.
    Sequential tree ensemble that minimizes residual errors.
    """
    def __init__(self, n_estimators=50, max_depth=4, learning_rate=0.1, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.name = f"Gradient Boosting (trees={n_estimators}, depth={max_depth})"
        self.model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state
        )

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        raw_preds = self.model.predict(X)
        return np.maximum(0.0, raw_preds)

    @property
    def feature_importances_(self):
        return self.model.feature_importances_

