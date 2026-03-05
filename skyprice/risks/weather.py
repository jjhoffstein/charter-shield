import numpy as np
from skyprice.risks.base import RiskModule

class WeatherRisk(RiskModule):
    "Models cost of weather-induced delays"
    def __init__(self, delay_prob=0.15, mean_delay_hrs=1.0, delay_std=0.8):
        self.delay_prob, self.mean_delay_hrs, self.delay_std = delay_prob, mean_delay_hrs, delay_std

    def sample(self, trip, rng) -> float:
        "Sample weather delay cost"
        if rng.random() > self.delay_prob: return 0.0
        delay_hrs = rng.lognormal(np.log(self.mean_delay_hrs), self.delay_std)
        return delay_hrs * trip.aircraft.hourly_rate

    def describe(self) -> dict:
        return dict(delay_prob=self.delay_prob, mean_delay_hrs=self.mean_delay_hrs, delay_std=self.delay_std)
