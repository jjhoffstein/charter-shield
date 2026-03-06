import numpy as np
from datetime import date
from skyprice.risks.base import RiskModule

EVENT_WINDOWS = [
    ((1,  1), (1,  2),  1.00, "New Year's Day"),
    ((1, 31), (2,  3),  0.85, "Super Bowl"),
    ((2, 15), (2, 23),  0.70, "Daytona 500"),
    ((2, 14), (2, 16),  0.45, "Valentine's Day"),
    ((3, 13), (4,  7),  0.90, "March Madness"),
    ((4, 18), (4, 20),  0.50, "Easter"),
    ((5, 23), (5, 26),  0.55, "Memorial Day"),
    ((7,  3), (7,  5),  0.55, "July 4th"),
    ((8, 28), (9,  1),  0.60, "Labor Day"),
    ((11, 27),(11, 30), 0.60, "Thanksgiving"),
    ((12, 20),(12, 31), 0.65, "Holiday Season"),
    ((12, 26),(1,   1), 0.70, "New Year's Eve"),
]

def _event_prob(d, base_prob):
    "Return elevated event_prob if date falls in a known high-traffic window, else base_prob"
    for start, end, prob, *_ in EVENT_WINDOWS:
        s = date(d.year, *start)
        e = date(d.year, *end) if end[0] >= start[0] else date(d.year + 1, *end)
        if s <= d <= e: return max(prob, base_prob)
    return base_prob

class FBOEventRisk(RiskModule):
    "Models risk of FBO special event surcharges, with date-aware event probability"
    def __init__(self, event_prob=0.25, fee_ranges=None):
        self.event_prob = event_prob
        self.fee_ranges = fee_ranges or dict(mega=(10000, 30000, 0.05), major=(5000, 15000, 0.15), local=(1000, 5000, 0.40), standard=(60, 500, 0.40))

    def sample(self, trip, rng) -> float:
        "Sample FBO event fee, scaled by date-aware event probability"
        prob = _event_prob(trip.date, self.event_prob)
        if rng.random() > prob: return 0.0
        r, cum = rng.random(), 0.0
        for cat, (lo, hi, p) in self.fee_ranges.items():
            cum += p
            if r <= cum: return rng.uniform(lo, hi)
        lo, hi, _ = list(self.fee_ranges.values())[-1]
        return rng.uniform(lo, hi)

    def describe(self) -> dict:
        return dict(event_prob=self.event_prob, fee_ranges=self.fee_ranges)
