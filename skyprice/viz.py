import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from skyprice.engine import simulate
from skyprice.data import load_config, build_risk_modules, distance_nm

_RISK_LABELS = dict(FuelRisk="Fuel variance", WeatherRisk="Weather delays",
    FBOEventRisk="FBO/ground handling", DeadheadRisk="Deadhead repositioning")

def narrate(trip, res):
    "Return plain-English pricing narrative for a charter quote"
    cfg = load_config()
    margin = cfg["pricing"]["target_margin"]
    flight_hrs = trip.distance_nm / trip.aircraft.cruise_ktas
    parts = [f"Base flight: {flight_hrs:.1f} hrs at ${trip.aircraft.hourly_rate:,}/hr block rate = ${res.base_cost:,.0f}."]
    for name, mean in res.risk_premiums.items():
        parts.append(f"{_RISK_LABELS.get(name, name)} adds ~${mean:,.0f} on average.")
    parts.append(f"90th-percentile total cost: ${res.p90:,.0f}.")
    parts.append(f"Final quote (p90 + {margin:.0%} margin): ${res.quote:,.0f}.")
    return '\n'.join(parts)

def plot_fuel_sensitivity(trip, price_points=(2.50, 3.50, 4.50), n=10000, seed=42):
    "Bar chart of p90 quote vs jet-A spot price"
    base_cfg = load_config()
    def _quote(spot):
        cfg = {**base_cfg, "fuel": {**base_cfg["fuel"], "spot_price_fallback": spot}}
        return simulate(trip, build_risk_modules(cfg), n=n, seed=seed).quote
    quotes = [_quote(s) for s in price_points]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar([f"${p:.2f}/gal" for p in price_points], quotes, color=["#4CAF50","#FF9800","#F44336"], width=0.5, edgecolor="white")
    for bar, q in zip(bars, quotes): ax.text(bar.get_x() + bar.get_width()/2, q + 50, f"${q:,.0f}", ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_ylabel("Final Quote ($)", fontsize=11)
    ax.set_title(f"Quote Sensitivity to Jet-A Price  |  {trip.origin}→{trip.destination}", fontsize=13, fontweight="bold")
    ax.set_ylim(min(quotes) * 0.97, max(quotes) * 1.03)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f"${x:,.0f}"))
    ax.spines[["top","right"]].set_visible(False)
    fig.tight_layout()
    return fig

def plot_fleet_comparison(origin="KBOS", dest="KMIA", travel_date=None, pax=4, cargo=200, n=10000, seed=42):
    "Side-by-side p50/p90/quote comparison across all aircraft in AC_LOOKUP"
    from skyprice.backtest import AC_LOOKUP
    from skyprice.core import Trip
    from datetime import date
    if travel_date is None: travel_date = date(2025, 1, 15)
    nm = distance_nm(origin, dest)
    labels, p50s, p90s, quotes = [], [], [], []
    for name, ac in AC_LOOKUP.items():
        try:
            trip = Trip(origin, dest, travel_date, ac, pax, cargo, nm)
            res = simulate(trip, build_risk_modules(), n=n, seed=seed)
            labels.append(name); p50s.append(res.percentiles["p50"]); p90s.append(res.p90); quotes.append(res.quote)
        except ValueError: pass
    x, w = np.arange(len(labels)), 0.25
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, (vals, color, label) in enumerate(zip([p50s, p90s, quotes], ["#4CAF50","#FF9800","#2196F3"], ["p50","p90","Quote (p90+margin)"])):
        bars = ax.bar(x + i*w, vals, w, color=color, edgecolor="white", alpha=0.9, label=label)
        for bar, v in zip(bars, vals): ax.text(bar.get_x()+bar.get_width()/2, v+200, f"${v/1000:.1f}k", ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax.set_xticks(x + w); ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("Cost ($)", fontsize=11)
    ax.set_title(f"Fleet Cost Comparison  |  {origin}→{dest}", fontsize=13, fontweight="bold")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f"${x:,.0f}"))
    ax.legend(fontsize=10, frameon=False); ax.spines[["top","right"]].set_visible(False)
    fig.tight_layout()
    return fig

def plot_waterfall(result, title=None):
    "Waterfall chart with per-module p10-p90 uncertainty ranges"
    modules = list(result.risk_distributions.keys())
    labels = ["Base Cost"] + [m.replace("Risk","") for m in modules] + ["Total Quote"]
    means = [result.base_cost] + [result.risk_distributions[m]["mean"] for m in modules]
    p10s  = [None] + [result.risk_distributions[m]["p10"] for m in modules]
    p90s  = [None] + [result.risk_distributions[m]["p90"] for m in modules]
    cumulative = [sum(means[:i+1]) for i in range(len(means))]
    bottoms = [0] + cumulative[:-1]
    colors = ["#2196F3"] + ["#FF7043","#FF9800","#AB47BC","#26A69A"][:len(modules)]
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, (b, m, lo, hi, c, l) in enumerate(zip(bottoms, means, p10s, p90s, colors, labels[:-1])):
        ax.bar(i, max(m, 200), bottom=b, color=c, edgecolor="white", width=0.6, alpha=0.9)
        if lo is not None:
            ax.errorbar(i, b + m, yerr=[[m - lo], [hi - m]], fmt="none", color="black", capsize=6, linewidth=1.5)
        ypos = b + m/2 if m > 1000 else b + m + 800
        ax.text(i, ypos, f"${m:,.0f}", ha="center", va="center", fontsize=9, fontweight="bold", color="white" if m > 1000 else "black")
    ax.bar(len(means), result.total, color="#2E7D32", edgecolor="white", width=0.6, alpha=0.9)
    ax.text(len(means), result.total/2, f"${result.total:,.0f}", ha="center", va="center", fontsize=10, fontweight="bold", color="white")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=11)
    ax.set_ylabel("Cost ($)", fontsize=11); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f"${x:,.0f}"))
    ax.set_title(title or f"Risk-Adjusted Pricing Waterfall  |  Quote: ${result.total:,.0f}", fontsize=13, fontweight="bold")
    ax.spines[["top","right"]].set_visible(False)
    ax.legend(handles=[mpatches.Patch(color="none", label="Error bars = p10–p90 range")], fontsize=9, frameon=False)
    fig.tight_layout()
    return fig

def plot_calibration(bt_df):
    "Backtest calibration: actual coverage vs target at each percentile"
    pcts = ["p50","p75","p90","p95","p99"]
    targets = [0.50, 0.75, 0.90, 0.95, 0.99]
    actual = [(bt_df.actual <= bt_df[p]).mean() for p in pcts]
    x = np.arange(len(pcts))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x, actual, width=0.5, color=["#4CAF50" if a >= t else "#F44336" for a,t in zip(actual,targets)], alpha=0.85, edgecolor="white")
    ax.plot(x, targets, "o--", color="#1565C0", linewidth=2, markersize=7, label="Target coverage", zorder=5)
    for i, (a, t) in enumerate(zip(actual, targets)): ax.text(i, a + 0.01, f"{a:.0%}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(pcts, fontsize=11)
    ax.set_ylabel("Fraction of actuals ≤ percentile quote", fontsize=11)
    ax.set_ylim(0, 1.12); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f"{x:.0%}"))
    ax.set_title("Backtest Calibration: Does the Model Price Accurately?", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10, frameon=False); ax.spines[["top","right"]].set_visible(False)
    fig.tight_layout()
    return fig

def plot_distribution(result, title="Charter Cost Distribution"):
    "Plot cost distribution clipped at p99, with percentile lines and quote marker"
    clip = result.percentiles["p99"]
    data = [x for x in result.distribution if x <= clip]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(data, bins=60, alpha=0.7, color="#2196F3", edgecolor="white")
    colors = dict(p50="#4CAF50", p75="#FF9800", p90="#F44336", p95="#880E4F", p99="#4A148C")
    for k, v in result.percentiles.items():
        if v <= clip: ax.axvline(v, color=colors[k], linestyle="--", linewidth=1.5, label=f"{k}: ${v:,.0f}")
    ax.axvline(result.total, color="black", linewidth=2.5, label=f"Quote: ${result.total:,.0f}")
    ax.set_xlabel("Total Trip Cost ($)", fontsize=11); ax.set_ylabel("Frequency", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f"${x:,.0f}"))
    ax.spines[["top","right"]].set_visible(False)
    ax.legend(fontsize=9); fig.tight_layout()
    return fig
