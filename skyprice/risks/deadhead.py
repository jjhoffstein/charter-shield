import numpy as np
from skyprice.risks.base import RiskModule
from skyprice.data import distance_nm

class DeadheadRisk(RiskModule):
    "Models cost of empty repositioning legs using actual home-base distances"
    def __init__(self, sell_prob=0.30, fuel_price_per_gal=7.825):
        self.sell_prob, self.fuel_price_per_gal = sell_prob, fuel_price_per_gal

    def sample(self, trip, rng) -> float:
        "Sample deadhead cost — repo distance from home base, zero if empty leg sells"
        if rng.random() < self.sell_prob: return 0.0
        home = trip.aircraft.home_base
        repo_nm = distance_nm(home, trip.origin) + distance_nm(trip.destination, home)
        repo_hrs = repo_nm / trip.aircraft.cruise_ktas
        return repo_hrs * (trip.aircraft.hourly_rate + trip.aircraft.fuel_burn_gph * self.fuel_price_per_gal)

    def describe(self) -> dict: return dict(sell_prob=self.sell_prob, fuel_price_per_gal=self.fuel_price_per_gal)
