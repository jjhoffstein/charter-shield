import numpy as np
from skyprice.core import PricingResult
from skyprice.risks.fuel import FuelRisk

def base_cost(trip, quoted_per_gal=8.075):
    "Compute deterministic base cost: flight time + all-in quoted fuel cost"
    ac = trip.aircraft
    flight_hrs = trip.distance_nm / ac.cruise_ktas
    return flight_hrs * ac.hourly_rate + flight_hrs * ac.fuel_burn_gph * quoted_per_gal

def simulate(trip, risk_modules, n=10_000, seed=42, margin=0.12):
    "Run Monte Carlo simulation across all risk modules"
    rng = np.random.default_rng(seed)
    fuel = next((m for m in risk_modules if isinstance(m, FuelRisk)), None)
    qpg = (fuel.base_price + np.mean(fuel.flowage_range) + np.mean(fuel.into_plane_range)) if fuel else 8.075
    bc = base_cost(trip, qpg)
    risk_samples = {type(m).__name__: np.array([m.sample(trip, rng) for _ in range(n)]) for m in risk_modules}
    total_risk = sum(risk_samples.values())
    total_cost = bc + total_risk
    pcts = [0.50, 0.75, 0.90, 0.95, 0.99]
    percentiles = {f"p{int(p*100)}": np.percentile(total_cost, p*100) for p in pcts}
    premiums = {k: float(np.mean(v)) for k, v in risk_samples.items()}
    risk_dists = {k: dict(mean=float(np.mean(v)), p10=float(np.percentile(v,10)), p90=float(np.percentile(v,90))) for k, v in risk_samples.items()}
    return PricingResult(base_cost=bc, risk_premiums=premiums,
        total=float(percentiles["p90"] * (1 + margin)),
        percentiles={k: float(v) for k, v in percentiles.items()},
        distribution=total_cost.tolist(), risk_distributions=risk_dists)
