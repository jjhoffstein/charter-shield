import numpy as np, pandas as pd
from datetime import date
from skyprice.core import Aircraft, Trip, PricingResult
from skyprice.data import load_config, build_risk_modules
from skyprice.engine import simulate

AC_LOOKUP = {"Gulfstream G-IV": Aircraft("Gulfstream G-IV", 8500, 4370, 24000, 280),
             "Citation XLS+": Aircraft("Citation XLS+", 4200, 931, 12500, 190),
             "Phenom 300": Aircraft("Phenom 300", 3200, 581, 8500, 150)}

def backtest(hist_df, modules=None, cfg=None):
    "Run model against historical trips, return coverage stats"
    if cfg is None: cfg = load_config()
    if modules is None: modules = build_risk_modules(cfg)
    n, seed, margin = cfg["simulation"]["n_iterations"], cfg["simulation"]["seed"], cfg["pricing"]["target_margin"]
    rows = []
    for _, r in hist_df.iterrows():
        ac = AC_LOOKUP[r.aircraft]
        t = Trip(r.origin, r.destination, date.fromisoformat(r.date), ac, r.pax, r.cargo_lbs, r.distance_nm)
        res = simulate(t, modules, n=n, seed=seed, margin=margin)
        rows.append(dict(actual=r.actual_cost, quote=res.total, **res.percentiles))
    return pd.DataFrame(rows)

def coverage_stats(bt_df):
    "Compute coverage at each percentile"
    return {col: float((bt_df.actual <= bt_df[col]).mean()) for col in ["p50", "p75", "p90", "p95", "p99", "quote"]}
