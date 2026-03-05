import numpy as np
from skyprice.risks.base import RiskModule

class DeadheadRisk(RiskModule):
    "Models cost of empty repositioning legs"
    def __init__(self, sell_prob=0.35):
        self.sell_prob = sell_prob

    def sample(self, trip, rng) -> float:
        "Sample deadhead cost — full repositioning cost discounted by sell probability"
        flight_hours = trip.distance_nm / 450
        repo_cost = flight_hours * trip.aircraft.hourly_rate
        if rng.random() < self.sell_prob: return 0.0
        return repo_cost * rng.uniform(0.5, 1.0)

    def describe(self) -> dict: return dict(sell_prob=self.sell_prob)
