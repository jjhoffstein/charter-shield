import numpy as np
from skyprice.risks.base import RiskModule

class FuelRisk(RiskModule):
    "Models fuel price volatility and destination markup risk"
    def __init__(self, base_price=6.50, volatility=0.15, flowage_range=(0.10, 0.30), into_plane_range=(1.25, 1.50)):
        self.base_price, self.volatility = base_price, volatility
        self.flowage_range, self.into_plane_range = flowage_range, into_plane_range

    def sample(self, trip, rng) -> float:
        "Sample fuel cost variance for a trip"
        flight_hours = trip.distance_nm / 450
        gallons = flight_hours * trip.aircraft.fuel_burn_gph
        spot_price = rng.lognormal(np.log(self.base_price), self.volatility)
        flowage = rng.uniform(*self.flowage_range)
        into_plane = rng.uniform(*self.into_plane_range)
        actual_per_gal = spot_price + flowage + into_plane
        quoted_per_gal = self.base_price + np.mean(self.flowage_range) + np.mean(self.into_plane_range)
        return (actual_per_gal - quoted_per_gal) * gallons

    def describe(self) -> dict:
        return dict(base_price=self.base_price, volatility=self.volatility,
                    flowage_range=self.flowage_range, into_plane_range=self.into_plane_range)
