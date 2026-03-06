import numpy as np
from skyprice.risks.base import RiskModule
from skyprice.data import distance_nm

class DeadheadRisk(RiskModule):
    "Models cost of empty repositioning legs using actual home-base distances"
    def __init__(self, sell_prob=0.30):
        self.sell_prob = sell_prob

    def sample(self, trip, rng) -> float:
        "Sample deadhead cost — repo distance from home base, zero if empty leg sells"
        if rng.random() < self.sell_prob: return 0.0
        home = trip.aircraft.home_base
        repo_nm = distance_nm(home, trip.origin) + distance_nm(trip.destination, home)
        return (repo_nm / trip.aircraft.cruise_ktas) * trip.aircraft.hourly_rate

    def describe(self) -> dict: return dict(sell_prob=self.sell_prob)
