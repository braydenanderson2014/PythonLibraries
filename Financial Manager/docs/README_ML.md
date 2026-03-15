# ML Stack Overview

This document summarizes the chosen initial stack and future directions.

## Current Components
- Data storage: JSON via `StockDataManager` (can migrate to SQLite later)
- Providers: Composite multi-source with optional Polygon & Alpha Vantage
- Corporate Actions: Splits/Dividends (Polygon) with adjustment + raw preservation
- Fundamentals: Point-in-time retrieval with TTM + quarterly sequences
- Features: Pure Python technical set (SMA/EMA/Vol/Returns)
- Dataset Builder: Generates supervised rows with multi-horizon future returns
- Baseline Model: Scikit-Learn GradientBoostingRegressor

## Why Not Deep Learning Yet?
For short horizon return prediction with limited engineered features, tree models
often outperform naive deep models. Once richer cross-sectional + sequence
features exist (e.g., multi-symbol temporal context, embeddings of sectors,
macro factors), deep learning becomes more compelling.

## When We Add a Deep Model
Recommended framework: **PyTorch**
Reasons:
1. Ecosystem: rich time-series & tabular libraries (PyTorch Forecasting, PyTorch Lightning)
2. Debuggability: imperative execution easier to iterate
3. Community: abundant examples for financial modeling and custom losses
4. Deployment: ONNX export and TorchScript options

TensorFlow/Keras remain viable, but given Python-first tooling already present,
PyTorch is a smoother path.

## Planned Enhancements
- Add numpy/pandas vectorized feature calc (replace pure python loops)
- Extend feature set: RSI, MACD, Bollinger Bands, ATR, momentum ranks
- Add cross-sectional sector z-scores
- Add dataset caching to disk (Parquet) for faster experiments
- Introduce label variants (classification: direction, volatility breakout)
- Add experiment config runner (YAML) + results logging
- Integrate PyTorch seq2seq or Temporal Fusion Transformer for multi-horizon forecasting

## Suggested Library Adds (Future)
- `lightgbm` for stronger tree baselines
- `xgboost` for alternative gradient boosting
- `pytorch-lightning` or `lightning` for structured training loops
- `optuna` for hyperparameter tuning
- `ta` or `vectorbt` for indicator breadth (optional) 

## Data Integrity / Leakage Guard Rails
- Use `fundamentals_point_in_time` for historical feature reconstruction
- Never compute future-derived indicators (e.g., forward returns) inside training features
- Keep a strict time-ordered split (already in baseline)

## Next Step Suggestions
1. Persist raw_* values robustly (already serialized) and add retrieval toggle.
2. Add feature pipeline with pandas for speed & clarity.
3. Introduce multiple horizons multi-task model.
4. Implement walk-forward evaluation harness.

Feel free to request any of these and they can be implemented incrementally.
