import numpy as np
from skyprice.core import PricingResult

def base_cost(trip, fuel_base_price=6.50):
    "Compute deterministic base cost: flight time + base fuel"
    ac = trip.aircraft
    flight_hrs = trip.distance_nm / 450
    return flight_hrs * ac.hourly_rate + flight_hrs * ac.fuel_burn_gph * fuel_base_price

def simulate(trip, risk_modules, n=10_000, seed=42, margin=0.12, fuel_base_price=6.50):
    "Run Monte Carlo simulation across all risk modules"
    rng = np.random.default_rng(seed)
    bc = base_cost(trip, fuel_base_price)
    risk_samples = {type(m).__name__: np.array([m.sample(trip, rng) for _ in range(n)]) for m in risk_modules}
    total_risk = sum(risk_samples.values())
    total_cost = bc + total_risk
    pcts = [0.50, 0.75, 0.90, 0.95, 0.99]
    percentiles = {f"p{int(p*100)}": np.percentile(total_cost, p*100) for p in pcts}
    premiums = {k: float(np.mean(v)) for k, v in risk_samples.items()}
    return PricingResult(
        base_cost=bc, risk_premiums=premiums,
        total=float(percentiles["p90"] * (1 + margin)),
        percentiles={k: float(v) for k, v in percentiles.items()},
        distribution=total_cost.tolist())
