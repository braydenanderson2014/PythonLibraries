"""Baseline training script for stock return prediction.

Uses scikit-learn GradientBoostingRegressor for a single-horizon future
log return prediction (default 5-day). This is intentionally minimal.
"""
from __future__ import annotations

from typing import Tuple, List

try:
    from .stock_data import StockDataManager
    from .dataset_builder import build_symbol_dataset
except Exception:  # pragma: no cover
    from stock_data import StockDataManager  # type: ignore
    from dataset_builder import build_symbol_dataset  # type: ignore

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import math

TARGET_H = 5


def _split(dataset, train_ratio=0.7, val_ratio=0.15) -> Tuple[List[dict], List[dict], List[dict]]:
    n = len(dataset)
    t_end = int(n * train_ratio)
    v_end = int(n * (train_ratio + val_ratio))
    return dataset[:t_end], dataset[t_end:v_end], dataset[v_end:]


def train_baseline(store: StockDataManager, symbol: str):
    data = build_symbol_dataset(store, symbol)
    if not data:
        raise RuntimeError("Not enough data to build dataset")
    train, val, test = _split(data)
    feat_keys = [k for k in data[0].keys() if k not in ('index', f'fut_ret_{TARGET_H}') and not k.startswith('fut_ret_')]
    def to_xy(rows):
        X = [[r[k] if r[k] is not None else 0.0 for k in feat_keys] for r in rows]
        y = [r[f'fut_ret_{TARGET_H}'] for r in rows]
        return X, y
    Xtr, ytr = to_xy(train)
    Xv, yv = to_xy(val)
    Xt, yt = to_xy(test)
    model = GradientBoostingRegressor()
    model.fit(Xtr, ytr)
    pred_val = model.predict(Xv)
    pred_test = model.predict(Xt)
    val_mae = mean_absolute_error(yv, pred_val) if yv else math.nan
    test_mae = mean_absolute_error(yt, pred_test) if yt else math.nan
    val_r2 = r2_score(yv, pred_val) if len(yv) > 1 else math.nan
    test_r2 = r2_score(yt, pred_test) if len(yt) > 1 else math.nan
    return {
        'features': feat_keys,
        'val_mae': val_mae,
        'test_mae': test_mae,
        'val_r2': val_r2,
        'test_r2': test_r2,
        'model': model,
        'counts': {'train': len(train), 'val': len(val), 'test': len(test)},
    }

__all__ = ["train_baseline"]
