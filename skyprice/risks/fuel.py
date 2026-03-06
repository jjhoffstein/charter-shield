import numpy as np
from skyprice.risks.base import RiskModule

class FuelRisk(RiskModule):
    "Models fuel price volatility, destination markup risk, and burn quantity variance"
    def __init__(self, base_price=6.25, volatility=0.15, flowage_range=(0.10, 0.30), into_plane_range=(1.25, 1.50),
                 burn_volatility=0.04, airport_zones=None, seasonal_multipliers=None):
        self.base_price, self.volatility = base_price, volatility
        self.flowage_range, self.into_plane_range = flowage_range, into_plane_range
        self.burn_volatility = burn_volatility
        self.airport_zones = airport_zones or {}
        self.seasonal_multipliers = seasonal_multipliers or {}

    def _get_multiplier(self, icao, month):
        zone = self.airport_zones.get(icao)
        if zone is None or zone not in self.seasonal_multipliers: return 1.0
        return self.seasonal_multipliers[zone][month - 1]

    def _burn_sigma(self, trip):
        m = trip.date.month
        mult = max(self._get_multiplier(trip.origin, m), self._get_multiplier(trip.destination, m))
        return self.burn_volatility * mult

    def sample(self, trip, rng) -> float:
        "Sample fuel cost variance for a trip"
        flight_hours = trip.distance_nm / trip.aircraft.cruise_ktas
        base_gallons = flight_hours * trip.aircraft.fuel_burn_gph
        actual_gallons = base_gallons * rng.lognormal(0, self._burn_sigma(trip))
        spot_price = rng.lognormal(np.log(self.base_price), self.volatility)
        flowage = rng.uniform(*self.flowage_range)
        into_plane = rng.uniform(*self.into_plane_range)
        actual_cost = actual_gallons * (spot_price + flowage + into_plane)
        quoted_cost = base_gallons * (self.base_price + np.mean(self.flowage_range) + np.mean(self.into_plane_range))
        return actual_cost - quoted_cost

    def describe(self) -> dict:
        return dict(base_price=self.base_price, volatility=self.volatility, burn_volatility=self.burn_volatility,
                    flowage_range=self.flowage_range, into_plane_range=self.into_plane_range)
