import numpy as np
from skyprice.risks.base import RiskModule

class FBOEventRisk(RiskModule):
    "Models risk of FBO special event surcharges"
    def __init__(self, event_prob=0.20, fee_ranges=None):
        self.event_prob = event_prob
        self.fee_ranges = fee_ranges or dict(mega=(10000, 30000, 0.05), major=(5000, 15000, 0.15), local=(1000, 5000, 0.40), standard=(60, 500, 0.40))

    def sample(self, trip, rng) -> float:
        "Sample FBO event fee"
        if rng.random() > self.event_prob: return 0.0
        r = rng.random()
        cum = 0.0
        for cat, (lo, hi, prob) in self.fee_ranges.items():
            cum += prob
            if r <= cum: return rng.uniform(lo, hi)
        lo, hi, _ = list(self.fee_ranges.values())[-1]
        return rng.uniform(lo, hi)

    def describe(self) -> dict:
        return dict(event_prob=self.event_prob, fee_ranges=self.fee_ranges)
