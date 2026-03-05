from abc import ABC, abstractmethod

class RiskModule(ABC):
    "Base class for all risk modules"
    @abstractmethod
    def sample(self, trip, rng) -> float: "Return a single stochastic cost sample for the given trip"
    @abstractmethod
    def describe(self) -> dict: "Return parameter summary for audit trail"
