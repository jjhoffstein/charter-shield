import numpy as np
from skyprice.risks.base import RiskModule

class WeatherRisk(RiskModule):
    "Models cost of weather-induced delays with seasonal/geographic adjustments"
    def __init__(self, delay_prob=0.15, mean_delay_hrs=1.0, delay_std=0.8, seasonal_multipliers=None, airport_zones=None):
        self.delay_prob, self.mean_delay_hrs, self.delay_std = delay_prob, mean_delay_hrs, delay_std
        self.seasonal_multipliers = seasonal_multipliers or {}
        self.airport_zones = airport_zones or {}

    def _get_multiplier(self, icao, month):
        "Look up seasonal delay multiplier for an airport and month"
        zone = self.airport_zones.get(icao)
        if zone is None or zone not in self.seasonal_multipliers: return 1.0
        return self.seasonal_multipliers[zone][month - 1]

    def _effective_delay_prob(self, trip):
        "Use the worse of origin/destination delay probability"
        m = trip.date.month
        mult = max(self._get_multiplier(trip.origin, m), self._get_multiplier(trip.destination, m))
        return min(self.delay_prob * mult, 0.95)

    def sample(self, trip, rng) -> float:
        "Sample weather delay cost"
        if rng.random() > self._effective_delay_prob(trip): return 0.0
        delay_hrs = rng.lognormal(np.log(self.mean_delay_hrs), self.delay_std)
        return delay_hrs * trip.aircraft.hourly_rate

    def describe(self) -> dict:
        return dict(delay_prob=self.delay_prob, mean_delay_hrs=self.mean_delay_hrs, delay_std=self.delay_std,
                    seasonal_multipliers=self.seasonal_multipliers, airport_zones=self.airport_zones)
