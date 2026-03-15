"""Unified model training and prediction suite (enhanced + advanced extensions).

Adds / Extends:
    - Rolling window training (window_size)
    - Hyperparameter search (hyperparam_search)
    - Time-series cross-validation (cv_folds)
    - Walk-forward evaluation (walk_forward_folds)
    - Feature importance + SHAP attributions (compute_shap, shap_max_samples)
    - Streaming SGDRegressor (include_sgd)
    - Early stopping for boosting models (early_stopping_rounds)
    - Model registry with versioning & retention (max_versions_per_model)
    - Automatic model selection + optional ensemble building
    - Multi-horizon convenience wrapper (train_all_multi)
    - Prediction helpers & extended metrics logging
"""
from __future__ import annotations

import math, os, pickle, csv, datetime, sys, pathlib, json, itertools
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

try:
    import lightgbm as lgb  # type: ignore
except Exception:  # pragma: no cover
    lgb = None  # type: ignore

try:
    import xgboost as xgb  # type: ignore
except Exception:  # pragma: no cover
    xgb = None  # type: ignore

import torch
import torch.nn as nn
import torch.optim as optim

_BASE_DIR = pathlib.Path(__file__).resolve().parent
_SRC_DIR = _BASE_DIR / 'Financial Manager' / 'src'
if _SRC_DIR.exists() and str(_SRC_DIR) not in sys.path:
    sys.path.append(str(_SRC_DIR))

from stock_data import StockDataManager  # type: ignore
from dataset_builder import build_symbol_dataset  # type: ignore

TARGET_HORIZON = 5
DEFAULT_HORIZONS = (1,5,20,50,100)
METRICS_FILE = 'model_metrics.csv'
REGISTRY_FILE = 'model_registry.json'

def chronological_split(rows: List[dict], train_ratio=0.7, val_ratio=0.15):
    n = len(rows); t_end = int(n * train_ratio); v_end = int(n * (train_ratio + val_ratio))
    return rows[:t_end], rows[t_end:v_end], rows[v_end:]

def dataset_to_matrix(rows: List[dict], horizon: int) -> Tuple[List[List[float]], List[float], List[str]]:
    if not rows: return [], [], []
    exclude = {f'fut_ret_{h}' for h in (1,5,20,50,100)} | {'index'}
    feat_keys = [k for k in rows[0].keys() if k not in exclude]
    X = [[(r.get(k, 0.0) if r.get(k) is not None else 0.0) for k in feat_keys] for r in rows]
    y = [r.get(f'fut_ret_{horizon}', 0.0) for r in rows]
    return X, y, feat_keys

class MLPRegressor(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, 1)
        )
    def forward(self, x): return self.net(x)

@dataclass
class ModelResult:
    name: str
    val_mae: float
    test_mae: float
    val_r2: float
    test_r2: float
    val_directional_acc: float
    test_directional_acc: float
    counts: Dict[str, int]
    feature_names: List[str]
    hyperparams: Dict[str, Any] = field(default_factory=dict)
    feature_importances: Optional[List[Tuple[str, float]]] = None
    shap_importances: Optional[List[Tuple[str, float]]] = None
    cv_mae: Optional[float] = None
    cv_r2: Optional[float] = None
    wf_mae_mean: Optional[float] = None
    wf_mae_std: Optional[float] = None
    wf_r2_mean: Optional[float] = None
    wf_r2_std: Optional[float] = None
    best_iteration: Optional[int] = None
    path: Optional[str] = None
    cv_mae_folds: Optional[List[float]] = None
    cv_r2_folds: Optional[List[float]] = None
    wf_details: Optional[List[Dict[str, Any]]] = None

def directional_accuracy(y_true, y_pred):
    if not y_true: return math.nan
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if (yt >= 0 and yp >= 0) or (yt < 0 and yp < 0))
    return correct / len(y_true)

def train_all(
    store: StockDataManager,
    symbol: str,
    *,
    horizon: int = TARGET_HORIZON,
    save_dir: str = './model_artifacts',
    log_metrics: bool = True,
    window_size: Optional[int] = None,
    hyperparam_search: bool = False,
    cv_folds: int = 0,
    compute_shap: bool = False,
    include_sgd: bool = False,
    max_versions_per_model: int = 10,
    walk_forward_folds: int = 0,
    early_stopping_rounds: int = 0,
    shap_max_samples: int = 200,
    auto_select: bool = False,
    ensemble_top_n: int = 0,
    ensemble_weighting: str = 'inverse_mae',  # inverse_mae | equal | softmax
) -> Dict[str, ModelResult]:
    rows = build_symbol_dataset(store, symbol, horizons=(1,5,20,50,100))  # TODO: respect multi-horizon pipeline outside single run
    if len(rows) < 200: raise RuntimeError('Not enough data for robust training.')
    if window_size and len(rows) > window_size: rows = rows[-window_size:]
    train, val, test = chronological_split(rows)
    Xtr, ytr, feat_keys = dataset_to_matrix(train, horizon)
    Xv, yv, _ = dataset_to_matrix(val, horizon)
    Xt, yt, _ = dataset_to_matrix(test, horizon)
    os.makedirs(save_dir, exist_ok=True)
    results: Dict[str, ModelResult] = {}

    # Gradient Boosting
    gbr_params = {'n_estimators': 400, 'learning_rate': 0.1, 'max_depth': 3}
    if hyperparam_search:
        grid = {'n_estimators': [200, 400], 'learning_rate': [0.05, 0.1], 'max_depth': [2,3]}
        best = (float('inf'), gbr_params)
        for combo in itertools.product(*grid.values()):
            params = dict(zip(grid.keys(), combo))
            model = GradientBoostingRegressor(**params)
            model.fit(Xtr, ytr)
            mae = mean_absolute_error(yv, model.predict(Xv))
            if mae < best[0]: best = (mae, params)
        gbr_params = best[1]
    gbr = GradientBoostingRegressor(**gbr_params).fit(Xtr, ytr)
    pv, pt = gbr.predict(Xv), gbr.predict(Xt)
    res = _build_result('sklearn_gbr', pv, pt, yv, yt, train, val, test, feat_keys, gbr_params)
    if cv_folds > 1:
        cv_mae, cv_r2, cv_mae_folds, cv_r2_folds = _time_series_cv_detailed(Xtr, ytr, lambda: GradientBoostingRegressor(**gbr_params), cv_folds)
        res.cv_mae, res.cv_r2 = cv_mae, cv_r2; res.cv_mae_folds, res.cv_r2_folds = cv_mae_folds, cv_r2_folds
    if walk_forward_folds > 1:
        wf = _walk_forward_eval(Xtr, ytr, lambda: GradientBoostingRegressor(**gbr_params), walk_forward_folds)
        _attach_walk_forward(res, wf); res.wf_details = wf
    if hasattr(gbr, 'feature_importances_'):
        res.feature_importances = _compute_feature_importances(list(gbr.feature_importances_), feat_keys)
    if compute_shap:
        res.shap_importances = _compute_shap_importance(gbr, Xv, feat_keys, max_samples=shap_max_samples)
    _save_pickle(gbr, os.path.join(save_dir, f'{symbol}_gbr.pkl')); res.path = os.path.join(save_dir, f'{symbol}_gbr.pkl'); results[res.name] = res

    # LightGBM
    if lgb is not None:
        lgb_params = {'n_estimators': 400, 'learning_rate': 0.05, 'num_leaves': 31}
        if hyperparam_search:
            grid = {'n_estimators': [300,600], 'learning_rate': [0.05,0.1], 'num_leaves':[31,63]}
            best = (float('inf'), lgb_params)
            for combo in itertools.product(*grid.values()):
                params = dict(zip(grid.keys(), combo))
                model = lgb.LGBMRegressor(**params).fit(Xtr, ytr)
                mae = mean_absolute_error(yv, model.predict(Xv))
                if mae < best[0]: best = (mae, params)
            lgb_params = best[1]
        lgb_fit_kwargs = {'eval_set': [(Xv, yv)], 'verbose': False}
        if early_stopping_rounds > 0:
            lgb_fit_kwargs['callbacks'] = [lgb.early_stopping(early_stopping_rounds)]
        lgbm = lgb.LGBMRegressor(**lgb_params).fit(Xtr, ytr, **lgb_fit_kwargs)
        best_iter = getattr(lgbm, 'best_iteration_', None)
        if best_iter is not None and best_iter > 0:
            pv = lgbm.predict(Xv, num_iteration=best_iter)
            pt = lgbm.predict(Xt, num_iteration=best_iter)
        else:
            pv, pt = lgbm.predict(Xv), lgbm.predict(Xt)
        lr = _build_result('lightgbm', pv, pt, yv, yt, train, val, test, feat_keys, lgb_params)
        lr.best_iteration = best_iter
        if cv_folds > 1:
            cv_mae, cv_r2, cv_mae_folds, cv_r2_folds = _time_series_cv_detailed(Xtr, ytr, lambda: lgb.LGBMRegressor(**lgb_params), cv_folds)
            lr.cv_mae, lr.cv_r2 = cv_mae, cv_r2; lr.cv_mae_folds, lr.cv_r2_folds = cv_mae_folds, cv_r2_folds
        if walk_forward_folds > 1:
            wf = _walk_forward_eval(Xtr, ytr, lambda: lgb.LGBMRegressor(**lgb_params), walk_forward_folds)
            _attach_walk_forward(lr, wf); lr.wf_details = wf
        if hasattr(lgbm, 'feature_importances_'):
            lr.feature_importances = _compute_feature_importances(list(lgbm.feature_importances_), feat_keys)
        if compute_shap:
            lr.shap_importances = _compute_shap_importance(lgbm, Xv, feat_keys, max_samples=shap_max_samples)
        _save_pickle(lgbm, os.path.join(save_dir, f'{symbol}_lgbm.pkl')); lr.path = os.path.join(save_dir, f'{symbol}_lgbm.pkl'); results[lr.name] = lr

    # XGBoost
    if xgb is not None:
        xgb_params = {'n_estimators': 400, 'max_depth': 5, 'learning_rate': 0.05, 'objective': 'reg:squarederror', 'tree_method': 'hist'}
        if hyperparam_search:
            grid = {'n_estimators': [300,600], 'max_depth': [4,6], 'learning_rate': [0.05,0.1]}
            best = (float('inf'), xgb_params)
            for combo in itertools.product(*grid.values()):
                params = dict(zip(grid.keys(), combo))
                model = xgb.XGBRegressor(**params, objective='reg:squarederror', tree_method='hist').fit(Xtr, ytr, verbose=False)
                mae = mean_absolute_error(yv, model.predict(Xv))
                if mae < best[0]: best = (mae, params)
            xgb_params.update(best[1])
        xgb_fit_kwargs = {'eval_set': [(Xv, yv)], 'verbose': False}
        if early_stopping_rounds > 0:
            xgb_fit_kwargs['early_stopping_rounds'] = early_stopping_rounds
        xgbr = xgb.XGBRegressor(**xgb_params).fit(Xtr, ytr, **xgb_fit_kwargs)
        best_iter = getattr(xgbr, 'best_iteration', None)
        if best_iter is not None and best_iter > 0:
            pv = xgbr.predict(Xv, iteration_range=(0, best_iter+1))
            pt = xgbr.predict(Xt, iteration_range=(0, best_iter+1))
        else:
            pv, pt = xgbr.predict(Xv), xgbr.predict(Xt)
        xr = _build_result('xgboost', pv, pt, yv, yt, train, val, test, feat_keys, xgb_params)
        xr.best_iteration = best_iter
        if cv_folds > 1:
            cv_mae, cv_r2, cv_mae_folds, cv_r2_folds = _time_series_cv_detailed(Xtr, ytr, lambda: xgb.XGBRegressor(**xgb_params), cv_folds)
            xr.cv_mae, xr.cv_r2 = cv_mae, cv_r2; xr.cv_mae_folds, xr.cv_r2_folds = cv_mae_folds, cv_r2_folds
        if walk_forward_folds > 1:
            wf = _walk_forward_eval(Xtr, ytr, lambda: xgb.XGBRegressor(**xgb_params), walk_forward_folds)
            _attach_walk_forward(xr, wf); xr.wf_details = wf
        if hasattr(xgbr, 'feature_importances_'):
            xr.feature_importances = _compute_feature_importances(list(xgbr.feature_importances_), feat_keys)
        if compute_shap:
            xr.shap_importances = _compute_shap_importance(xgbr, Xv, feat_keys, max_samples=shap_max_samples)
        _save_pickle(xgbr, os.path.join(save_dir, f'{symbol}_xgboost.pkl')); xr.path = os.path.join(save_dir, f'{symbol}_xgboost.pkl'); results[xr.name] = xr

    # PyTorch MLP
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    import numpy as np
    Xtr_t = torch.tensor(np.array(Xtr), dtype=torch.float32).to(device)
    ytr_t = torch.tensor(np.array(ytr), dtype=torch.float32).view(-1,1).to(device)
    Xv_t = torch.tensor(np.array(Xv), dtype=torch.float32).to(device)
    yv_t = torch.tensor(np.array(yv), dtype=torch.float32).view(-1,1).to(device)
    Xt_t = torch.tensor(np.array(Xt), dtype=torch.float32).to(device)
    yt_t = torch.tensor(np.array(yt), dtype=torch.float32).view(-1,1).to(device)
    mlp_params = {'hidden': 64, 'lr': 1e-3}
    if hyperparam_search:
        grid = {'hidden': [64,128], 'lr':[1e-3,5e-4]}; best=(float('inf'), mlp_params)
        for combo in itertools.product(*grid.values()):
            params = dict(zip(grid.keys(), combo))
            mtmp = MLPRegressor(len(feat_keys), hidden=params['hidden']).to(device)
            opt_tmp = optim.Adam(mtmp.parameters(), lr=params['lr']); lf = nn.MSELoss()
            for _ in range(50):
                mtmp.train(); opt_tmp.zero_grad(); pr = mtmp(Xtr_t); ls = lf(pr, ytr_t); ls.backward(); opt_tmp.step()
            mtmp.eval();
            with torch.no_grad(): mae = mean_absolute_error(yv, mtmp(Xv_t).cpu().numpy().ravel())
            if mae < best[0]: best = (mae, params)
        mlp_params = best[1]
    model = MLPRegressor(len(feat_keys), hidden=mlp_params['hidden']).to(device)
    opt = optim.Adam(model.parameters(), lr=mlp_params['lr'])
    loss_fn = nn.MSELoss(); best_val=float('inf'); patience=10; no_improve=0
    for epoch in range(200):
        model.train(); opt.zero_grad(); pred=model(Xtr_t); loss=loss_fn(pred,ytr_t); loss.backward(); opt.step()
        model.eval();
        with torch.no_grad(): vloss = loss_fn(model(Xv_t), yv_t).item()
        if vloss < best_val - 1e-5:
            best_val = vloss; no_improve=0
            torch.save({'model_state': model.state_dict(), 'feat_keys': feat_keys}, os.path.join(save_dir, f'{symbol}_mlp.pt'))
        else:
            no_improve += 1
            if no_improve >= patience: break
    ckpt_path = os.path.join(save_dir, f'{symbol}_mlp.pt')
    if os.path.exists(ckpt_path):
        ckpt = torch.load(ckpt_path, map_location=device); model.load_state_dict(ckpt['model_state'])
    model.eval();
    with torch.no_grad(): pv = model(Xv_t).cpu().numpy().ravel(); pt = model(Xt_t).cpu().numpy().ravel()
    mr = _build_result('pytorch_mlp', pv, pt, yv, yt, train, val, test, feat_keys, mlp_params); mr.path = ckpt_path; results[mr.name] = mr
    # (Optional) SHAP for MLP could be added, but omitted for runtime cost.

    # SGDRegressor streaming model
    if include_sgd:
        import random
        scaler = StandardScaler()
        Xtr_s = scaler.fit_transform(Xtr)
        sgd_params = {'alpha': 0.0001, 'learning_rate': 'optimal'}
        sgd = SGDRegressor(**sgd_params)
        for epoch in range(5):
            order = list(range(len(Xtr_s)))
            random.shuffle(order)
            for idx in order:
                sgd.partial_fit([Xtr_s[idx]], [ytr[idx]])
        Xv_s = scaler.transform(Xv); Xt_s = scaler.transform(Xt)
        pv_s = sgd.predict(Xv_s); pt_s = sgd.predict(Xt_s)
        sgr = _build_result('sgd_reg', pv_s, pt_s, yv, yt, train, val, test, feat_keys, sgd_params)
        if cv_folds > 1:
            cv_mae, cv_r2, cv_mae_folds, cv_r2_folds = _time_series_cv_detailed(Xtr, ytr, lambda: _new_sgd_with_scaler(sgd_params), cv_folds, scale=True)
            sgr.cv_mae, sgr.cv_r2 = cv_mae, cv_r2; sgr.cv_mae_folds, sgr.cv_r2_folds = cv_mae_folds, cv_r2_folds
        _save_pickle({'model': sgd, 'scaler': scaler, 'feat_keys': feat_keys}, os.path.join(save_dir, f'{symbol}_sgd.pkl'))
        sgr.path = os.path.join(save_dir, f'{symbol}_sgd.pkl')
        results[sgr.name] = sgr

    if log_metrics:
        _append_metrics_csv(symbol, horizon, results); _update_registry(symbol, horizon, results, max_versions_per_model=max_versions_per_model)

    # Automatic selection & ensemble (optional)
    if auto_select:
        selection = select_best_model(results)
        _write_active_selection(save_dir, symbol, horizon, selection)
    if ensemble_top_n and ensemble_top_n > 1:
        ens = build_ensemble(results, top_n=ensemble_top_n, weighting=ensemble_weighting)
        _write_ensemble(save_dir, symbol, horizon, ens)
    return results

def load_pickle(path: str):
    with open(path, 'rb') as f: return pickle.load(f)

def predict_with(model_obj, X: List[List[float]]): return model_obj.predict(X)

def _build_result(name: str, pv, pt, yv, yt, train, val, test, feat_keys, hyperparams: Optional[Dict[str, Any]] = None):
    val_mae = mean_absolute_error(yv, pv) if yv else math.nan
    test_mae = mean_absolute_error(yt, pt) if yt else math.nan
    val_r2 = r2_score(yv, pv) if len(yv) > 1 else math.nan
    test_r2 = r2_score(yt, pt) if len(yt) > 1 else math.nan
    vdir = directional_accuracy(yv, pv); tdir = directional_accuracy(yt, pt)
    return ModelResult(name=name, val_mae=val_mae, test_mae=test_mae, val_r2=val_r2, test_r2=test_r2, val_directional_acc=vdir, test_directional_acc=tdir, counts={'train': len(train), 'val': len(val), 'test': len(test)}, feature_names=feat_keys, hyperparams=hyperparams or {})

def _save_pickle(obj, path: str):
    with open(path, 'wb') as f: pickle.dump(obj, f)

def _append_metrics_csv(symbol: str, horizon: int, results: Dict[str, ModelResult]):
    new_file = not os.path.exists(METRICS_FILE)
    with open(METRICS_FILE, 'a', newline='') as f:
        w = csv.writer(f)
        if new_file: w.writerow(['timestamp','symbol','horizon','model','val_mae','test_mae','val_r2','test_r2','val_dir_acc','test_dir_acc','train_count','val_count','test_count'])
        ts = datetime.datetime.utcnow().isoformat()
        for r in results.values():
            w.writerow([ts,symbol,horizon,r.name,r.val_mae,r.test_mae,r.val_r2,r.test_r2,r.val_directional_acc,r.test_directional_acc,r.counts['train'],r.counts['val'],r.counts['test']])

def _compute_feature_importances(importances: List[float], feat_names: List[str]) -> List[Tuple[str, float]]:
    pairs = list(zip(feat_names, importances)); pairs.sort(key=lambda x: x[1], reverse=True); return pairs

def _load_registry() -> List[dict]:
    if not os.path.exists(REGISTRY_FILE): return []
    try:
        with open(REGISTRY_FILE,'r') as f: return json.load(f)
    except Exception: return []

def _save_registry(entries: List[dict]):
    with open(REGISTRY_FILE,'w') as f: json.dump(entries, f, indent=2)

def _update_registry(symbol: str, horizon: int, results: Dict[str, ModelResult], *, max_versions_per_model: int = 10):
    entries = _load_registry()
    for name, res in results.items():
        prev_versions = [e for e in entries if e['symbol']==symbol and e['horizon']==horizon and e['model']==name]
        version = 1 + max((e.get('version',0) for e in prev_versions), default=0)
        entries.append({
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'symbol': symbol,
            'horizon': horizon,
            'model': name,
            'version': version,
            'metrics': {
                'val_mae': res.val_mae,
                'test_mae': res.test_mae,
                'val_r2': res.val_r2,
                'test_r2': res.test_r2,
                'val_dir_acc': res.val_directional_acc,
                'test_dir_acc': res.test_directional_acc,
                'cv_mae': res.cv_mae,
                'cv_r2': res.cv_r2,
                'cv_mae_folds': res.cv_mae_folds,
                'cv_r2_folds': res.cv_r2_folds,
                'wf_mae_mean': res.wf_mae_mean,
                'wf_mae_std': res.wf_mae_std,
                'wf_r2_mean': res.wf_r2_mean,
                'wf_r2_std': res.wf_r2_std,
                'wf_details': res.wf_details,
            },
            'hyperparams': res.hyperparams,
            'path': res.path,
            'feature_count': len(res.feature_names),
            'top_features': res.feature_importances[:15] if res.feature_importances else None
        })
    # Retention policy per (symbol,horizon,model)
    if max_versions_per_model > 0:
        grouped: Dict[Tuple[str,int,str], List[dict]] = {}
        for e in entries:
            key = (e['symbol'], e['horizon'], e['model'])
            grouped.setdefault(key, []).append(e)
        pruned: List[dict] = []
        for key, items in grouped.items():
            items.sort(key=lambda x: x.get('version',0), reverse=True)
            pruned.extend(items[:max_versions_per_model])
        entries = pruned
    _save_registry(entries)

def incremental_retrain(store: StockDataManager, symbol: str, model_paths: Dict[str, str], *, horizon: int = TARGET_HORIZON, log_metrics: bool = True, window_size: Optional[int] = None, max_versions_per_model: int = 10) -> Dict[str, Any]:
    rows = build_symbol_dataset(store, symbol, horizons=(1,5,20,50,100))
    if len(rows) < 200: raise RuntimeError('Not enough data for retraining.')
    if window_size and len(rows) > window_size: rows = rows[-window_size:]
    train, val, test = chronological_split(rows)
    Xtr, ytr, feat_keys = dataset_to_matrix(train, horizon)
    Xv, yv, _ = dataset_to_matrix(val, horizon)
    Xt, yt, _ = dataset_to_matrix(test, horizon)
    updated = {}
    if 'sklearn_gbr' in model_paths:
        model = load_pickle(model_paths['sklearn_gbr']); model.fit(Xtr, ytr); _save_pickle(model, model_paths['sklearn_gbr']); updated['sklearn_gbr']='retrained'
    if 'lightgbm' in model_paths and lgb is not None:
        model = load_pickle(model_paths['lightgbm']); model.fit(Xtr, ytr); _save_pickle(model, model_paths['lightgbm']); updated['lightgbm']='retrained'
    if 'xgboost' in model_paths and xgb is not None:
        model = load_pickle(model_paths['xgboost']); model.fit(Xtr, ytr); _save_pickle(model, model_paths['xgboost']); updated['xgboost']='retrained'
    if 'pytorch_mlp' in model_paths:
        import numpy as np
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        Xtr_t = torch.tensor(np.array(Xtr), dtype=torch.float32).to(device)
        ytr_t = torch.tensor(np.array(ytr), dtype=torch.float32).view(-1,1).to(device)
        state = torch.load(model_paths['pytorch_mlp'], map_location=device)
        model = MLPRegressor(len(feat_keys)); model.load_state_dict(state['model_state']); model.to(device)
        opt = optim.Adam(model.parameters(), lr=5e-4); loss_fn = nn.MSELoss(); model.train()
        for _ in range(50):
            opt.zero_grad(); pred = model(Xtr_t); loss = loss_fn(pred, ytr_t); loss.backward(); opt.step()
        torch.save({'model_state': model.state_dict(), 'feat_keys': feat_keys}, model_paths['pytorch_mlp']); updated['pytorch_mlp']='retrained'
    metrics_results: Dict[str, ModelResult] = {}
    # SGD streaming update
    if 'sgd_reg' in model_paths:
        art = load_pickle(model_paths['sgd_reg'])
        sgd = art['model']; scaler = art['scaler']; feat_keys_art = art.get('feat_keys', feat_keys)
        Xtr_s = scaler.fit_transform(Xtr)
        # single pass partial updates
        for i in range(len(Xtr_s)):
            sgd.partial_fit([Xtr_s[i]], [ytr[i]])
        _save_pickle({'model': sgd, 'scaler': scaler, 'feat_keys': feat_keys_art}, model_paths['sgd_reg'])
        updated['sgd_reg'] = 'partial_fit'

    for name, path in model_paths.items():
        if name == 'pytorch_mlp':
            import numpy as np
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            Xv_t = torch.tensor(np.array(Xv), dtype=torch.float32).to(device)
            Xt_t = torch.tensor(np.array(Xt), dtype=torch.float32).to(device)
            state = torch.load(path, map_location=device)
            model = MLPRegressor(len(feat_keys)); model.load_state_dict(state['model_state']); model.to(device); model.eval()
            with torch.no_grad(): pv = model(Xv_t).cpu().numpy().ravel(); pt = model(Xt_t).cpu().numpy().ravel()
            metrics_results[name] = _build_result(name, pv, pt, yv, yt, train, val, test, feat_keys)
            metrics_results[name].path = path
        elif name == 'sgd_reg':
            art = load_pickle(path)
            sgd = art['model']; scaler = art['scaler']
            Xv_s = scaler.transform(Xv); Xt_s = scaler.transform(Xt)
            pv = sgd.predict(Xv_s); pt = sgd.predict(Xt_s)
            metrics_results[name] = _build_result(name, pv, pt, yv, yt, train, val, test, feat_keys)
            metrics_results[name].path = path
        else:
            model = load_pickle(path); pv = model.predict(Xv); pt = model.predict(Xt)
            metrics_results[name] = _build_result(name, pv, pt, yv, yt, train, val, test, feat_keys); metrics_results[name].path = path
    if log_metrics: _append_metrics_csv(symbol, horizon, metrics_results); _update_registry(symbol, horizon, metrics_results, max_versions_per_model=max_versions_per_model)
    return updated

def latest_feature_vector(store: StockDataManager, symbol: str, horizon: int = TARGET_HORIZON) -> Tuple[List[float], List[str]]:
    rows = build_symbol_dataset(store, symbol, horizons=(1,5,20,50,100))
    if not rows: raise RuntimeError('No data available.')
    row = rows[-1]; exclude = {f'fut_ret_{h}' for h in (1,5,20,50,100)} | {'index'}
    feat_keys = [k for k in row.keys() if k not in exclude]
    vec = [(row.get(k, 0.0) if row.get(k) is not None else 0.0) for k in feat_keys]
    return vec, feat_keys

def predict_latest(store: StockDataManager, symbol: str, model_name: str, model_path: str, horizon: int = TARGET_HORIZON):
    X, feat_names = latest_feature_vector(store, symbol, horizon)
    if model_name == 'pytorch_mlp':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        state = torch.load(model_path, map_location=device)
        model = MLPRegressor(len(feat_names)); model.load_state_dict(state['model_state']); model.to(device); model.eval()
        with torch.no_grad():
            arr = torch.tensor([X], dtype=torch.float32).to(device); pred = model(arr).cpu().numpy().ravel()[0]
        return float(pred)
    else:
        model = load_pickle(model_path); return float(model.predict([X])[0])

def _time_series_cv(X: List[List[float]], y: List[float], model_ctor, folds: int, scale: bool=False) -> Tuple[float, float]:
    if folds < 2 or len(X) < folds + 5: return math.nan, math.nan
    import numpy as np
    X_arr = np.array(X); y_arr = np.array(y)
    fold_mae: List[float] = []; fold_r2: List[float] = []
    for f in range(1, folds+1):
        split = int(len(X_arr) * f/(folds+1))
        X_train, y_train = X_arr[:split], y_arr[:split]
        X_valid, y_valid = X_arr[split:split+int(len(X_arr)/(folds+1))], y_arr[split:split+int(len(X_arr)/(folds+1))]
        if len(X_valid) < 5: break
        if scale:
            scaler = StandardScaler(); X_train = scaler.fit_transform(X_train); X_valid = scaler.transform(X_valid)
        model = model_ctor()
        model.fit(X_train, y_train)
        pred = model.predict(X_valid)
        fold_mae.append(mean_absolute_error(y_valid, pred))
        if len(y_valid) > 1:
            try: fold_r2.append(r2_score(y_valid, pred))
            except Exception: pass
    return (sum(fold_mae)/len(fold_mae) if fold_mae else math.nan,
            sum(fold_r2)/len(fold_r2) if fold_r2 else math.nan)

def _time_series_cv_detailed(X: List[List[float]], y: List[float], model_ctor, folds: int, scale: bool=False) -> Tuple[float, float, List[float], List[float]]:
    if folds < 2 or len(X) < folds + 5: return math.nan, math.nan, [], []
    import numpy as np
    X_arr = np.array(X); y_arr = np.array(y)
    fold_mae: List[float] = []; fold_r2: List[float] = []
    for f in range(1, folds+1):
        split = int(len(X_arr) * f/(folds+1))
        X_train, y_train = X_arr[:split], y_arr[:split]
        X_valid, y_valid = X_arr[split:split+int(len(X_arr)/(folds+1))], y_arr[split:split+int(len(X_arr)/(folds+1))]
        if len(X_valid) < 5: break
        if scale:
            scaler = StandardScaler(); X_train = scaler.fit_transform(X_train); X_valid = scaler.transform(X_valid)
        model = model_ctor(); model.fit(X_train, y_train)
        pred = model.predict(X_valid)
        fold_mae.append(mean_absolute_error(y_valid, pred))
        if len(y_valid) > 1:
            try: fold_r2.append(r2_score(y_valid, pred))
            except Exception: pass
    avg_mae = (sum(fold_mae)/len(fold_mae)) if fold_mae else math.nan
    avg_r2 = (sum(fold_r2)/len(fold_r2)) if fold_r2 else math.nan
    return avg_mae, avg_r2, fold_mae, fold_r2

def _compute_shap_importance(model, X_sample: List[List[float]], feat_keys: List[str], max_samples: int = 200) -> Optional[List[Tuple[str, float]]]:
    try:
        import numpy as np, shap
        if not X_sample: return None
        X_arr = np.array(X_sample)
        if len(X_arr) > max_samples: X_arr = X_arr[:max_samples]
        explainer = shap.Explainer(model, X_arr)
        shap_vals = explainer(X_arr)
        vals = getattr(shap_vals, 'values', shap_vals)
        if isinstance(vals, list): vals = vals[0]
        imp = list(zip(feat_keys, np.mean(np.abs(vals), axis=0).tolist()))
        imp.sort(key=lambda x: x[1], reverse=True)
        return imp
    except Exception:
        return None

def _new_sgd_with_scaler(params: Dict[str, Any]):
    """Factory returning an object with fit/predict for CV using SGD + scaling."""
    class Wrapper:
        def __init__(self):
            from sklearn.linear_model import SGDRegressor
            from sklearn.preprocessing import StandardScaler
            import random
            self.scaler = StandardScaler()
            self.model = SGDRegressor(**params)
            self.params = params
        def fit(self, X, y):
            import numpy as np, random
            Xs = self.scaler.fit_transform(X)
            order = list(range(len(Xs)))
            for epoch in range(3):
                random.shuffle(order)
                for idx in order:
                    self.model.partial_fit([Xs[idx]], [y[idx]])
            return self
        def predict(self, X):
            Xs = self.scaler.transform(X)
            return self.model.predict(Xs)
    return Wrapper()

def train_all_multi(store: StockDataManager, symbol: str, horizons: Tuple[int,...] = DEFAULT_HORIZONS, **kwargs) -> Dict[int, Dict[str, ModelResult]]:
    out: Dict[int, Dict[str, ModelResult]] = {}
    for h in horizons:
        out[h] = train_all(store, symbol, horizon=h, **kwargs)
    return out

# ---------------- Walk-Forward Evaluation ---------------------------------

def _walk_forward_eval(X: List[List[float]], y: List[float], model_ctor, folds: int, min_train_fraction: float = 0.2):
    import numpy as np
    if folds < 2 or len(X) < 50:
        return []
    X_arr = np.array(X); y_arr = np.array(y)
    segment = int(len(X_arr)/(folds+1))
    results = []
    for i in range(1, folds+1):
        train_end = segment * i
        if train_end < max(int(len(X_arr)*min_train_fraction), 10):
            continue
        test_end = min(train_end + segment, len(X_arr))
        if test_end - train_end < 5:
            break
        X_tr, y_tr = X_arr[:train_end], y_arr[:train_end]
        X_te, y_te = X_arr[train_end:test_end], y_arr[train_end:test_end]
        model = model_ctor(); model.fit(X_tr, y_tr)
        pred = model.predict(X_te)
        mae = mean_absolute_error(y_te, pred)
        r2v = r2_score(y_te, pred) if len(y_te) > 1 else math.nan
        results.append({'mae': mae, 'r2': r2v, 'n': len(y_te)})
    return results

def _attach_walk_forward(res: ModelResult, wf_results: List[Dict[str, Any]]):
    if not wf_results:
        return
    maes = [r['mae'] for r in wf_results]
    r2s = [r['r2'] for r in wf_results if not math.isnan(r['r2'])]
    import statistics
    res.wf_mae_mean = statistics.mean(maes)
    res.wf_mae_std = statistics.pstdev(maes) if len(maes) > 1 else 0.0
    if r2s:
        res.wf_r2_mean = statistics.mean(r2s)
        res.wf_r2_std = statistics.pstdev(r2s) if len(r2s) > 1 else 0.0

# ---------------- Model Selection & Ensemble -------------------------------

def select_best_model(results: Dict[str, ModelResult], strategy: str = 'val') -> ModelResult:
    def score(r: ModelResult):
        if strategy == 'wf' and r.wf_mae_mean is not None:
            return r.wf_mae_mean
        if strategy == 'cv' and r.cv_mae is not None:
            return r.cv_mae
        return r.val_mae
    return min(results.values(), key=score)

def build_ensemble(results: Dict[str, ModelResult], top_n: int = 3, strategy: str = 'val', weighting: str = 'inverse_mae') -> Dict[str, Any]:
    scored = []
    for r in results.values():
        if strategy == 'wf' and r.wf_mae_mean is not None:
            metric = r.wf_mae_mean
        elif strategy == 'cv' and r.cv_mae is not None:
            metric = r.cv_mae
        else:
            metric = r.val_mae
        if metric is None or math.isnan(metric):
            continue
        scored.append((metric, r))
    scored.sort(key=lambda x: x[0])
    top = scored[:top_n]
    if not top:
        return {'members': [], 'weights': []}
    metrics = [m for m,_ in top]
    if weighting == 'equal':
        weights = [1/len(top)] * len(top)
    elif weighting == 'softmax':
        import math as _m
        # Softmax of negative MAE => lower MAE gets higher weight
        exps = [_m.exp(-m) for m in metrics]
        s = sum(exps); weights = [e/s for e in exps]
    else:  # inverse_mae default
        inv = [1/(m + 1e-9) for m in metrics]
        s = sum(inv)
        weights = [v/s for v in inv]
    return {'members': [r.name for _, r in top], 'weights': weights}

def _write_active_selection(save_dir: str, symbol: str, horizon: int, result: ModelResult):
    data = {
        'symbol': symbol,
        'horizon': horizon,
        'model': result.name,
        'path': result.path,
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'metrics': {
            'val_mae': result.val_mae,
            'test_mae': result.test_mae,
            'val_r2': result.val_r2,
            'test_r2': result.test_r2,
            'cv_mae': result.cv_mae,
            'cv_r2': result.cv_r2,
            'wf_mae_mean': result.wf_mae_mean,
            'wf_mae_std': result.wf_mae_std,
            'wf_r2_mean': result.wf_r2_mean,
            'wf_r2_std': result.wf_r2_std
        }
    }
    path = os.path.join(save_dir, f'{symbol}_h{horizon}_active.json')
    with open(path, 'w') as f: json.dump(data, f, indent=2)

def _write_ensemble(save_dir: str, symbol: str, horizon: int, ensemble: Dict[str, Any]):
    payload = {'symbol': symbol, 'horizon': horizon, 'ensemble': ensemble, 'timestamp': datetime.datetime.utcnow().isoformat()}
    path = os.path.join(save_dir, f'{symbol}_h{horizon}_ensemble.json')
    with open(path, 'w') as f: json.dump(payload, f, indent=2)

def predict_latest_ensemble(store: StockDataManager, symbol: str, artifact_path: str, horizon: int = TARGET_HORIZON):
    with open(artifact_path, 'r') as f:
        meta = json.load(f)
    members = meta['ensemble']['members']
    weights = meta['ensemble']['weights']
    vec, feat_names = latest_feature_vector(store, symbol, horizon)
    preds = []
    for m in members:
        model_file = _infer_model_path(meta['symbol'], m, horizon)
        if m == 'pytorch_mlp':
            preds.append(predict_latest(store, symbol, m, model_file, horizon))
        elif m == 'sgd_reg':
            art = load_pickle(model_file)
            scaler = art['scaler']; model = art['model']
            import numpy as np
            preds.append(float(model.predict(scaler.transform([vec]))[0]))
        else:
            model_obj = load_pickle(model_file)
            preds.append(float(model_obj.predict([vec])[0]))
    return sum(w*p for w,p in zip(weights, preds))

def predict_active(store: StockDataManager, symbol: str, artifact_path: str, horizon: int = TARGET_HORIZON):
    """Convenience: read active selection JSON and produce latest prediction."""
    with open(artifact_path, 'r') as f:
        meta = json.load(f)
    model_name = meta['model']; path = meta['path']
    return predict_latest(store, symbol, model_name, path, horizon)

def _infer_model_path(symbol: str, model_name: str, horizon: int) -> str:
    base = 'model_artifacts'
    suffix_map = {
        'sklearn_gbr': 'gbr.pkl',
        'lightgbm': 'lgbm.pkl',
        'xgboost': 'xgboost.pkl',
        'pytorch_mlp': 'mlp.pt',
        'sgd_reg': 'sgd.pkl'
    }
    return os.path.join(base, f'{symbol}_{suffix_map.get(model_name, model_name)}')

__all__ = [
    'train_all','train_all_multi','incremental_retrain','ModelResult',
    'predict_latest','latest_feature_vector','select_best_model','build_ensemble',
    'predict_latest_ensemble','predict_active'
]
