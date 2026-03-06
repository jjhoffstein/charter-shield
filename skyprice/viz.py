import matplotlib.pyplot as plt

def plot_distribution(result, title="Charter Cost Distribution"):
    "Plot cost distribution with percentile lines"
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(result.distribution, bins=80, alpha=0.7, color="steelblue", edgecolor="white")
    colors = dict(p50="green", p75="orange", p90="red", p95="darkred", p99="purple")
    for k, v in result.percentiles.items():
        ax.axvline(v, color=colors[k], linestyle="--", linewidth=1.5, label=f"{k}: ${v:,.0f}")
    ax.axvline(result.total, color="black", linewidth=2.5, label=f"Quote: ${result.total:,.0f}")
    ax.set_xlabel("Total Trip Cost ($)"); ax.set_ylabel("Frequency"); ax.set_title(title)
    ax.legend(); fig.tight_layout()
    return fig

def plot_waterfall(result):
    "Risk factor waterfall chart"
    fig, ax = plt.subplots(figsize=(10, 5))
    labels = ["Base Cost"] + list(result.risk_premiums.keys()) + ["Total Quote"]
    vals = [result.base_cost] + list(result.risk_premiums.values())
    cumulative = [sum(vals[:i+1]) for i in range(len(vals))]
    bottoms = [0] + cumulative[:-1]
    colors = ["steelblue"] + ["coral"] * len(result.risk_premiums)
    for i, (b, v, c, l) in enumerate(zip(bottoms, vals, colors, labels[:-1])):
        ax.bar(i, v, bottom=b, color=c, edgecolor="white", width=0.6)
        ax.text(i, b + v/2, f"${v:,.0f}", ha="center", va="center", fontweight="bold", fontsize=9)
    ax.bar(len(vals), result.total, color="darkgreen", edgecolor="white", width=0.6)
    ax.text(len(vals), result.total/2, f"${result.total:,.0f}", ha="center", va="center", fontweight="bold", fontsize=9, color="white")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("Cost ($)"); ax.set_title("Risk-Adjusted Pricing Waterfall")
    fig.tight_layout()
    return fig
