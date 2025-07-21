"""Investor profile strategies using Strategy pattern."""

from abc import ABC, abstractmethod
from typing import Dict


class InvestorStrategy(ABC):
    """Abstract base class for investor strategies."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get strategy name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get strategy description."""
        pass
    
    @property
    @abstractmethod
    def weights(self) -> Dict[str, float]:
        """Get metric weights for this strategy."""
        pass
    
    @property
    @abstractmethod
    def thresholds(self) -> Dict[str, tuple]:
        """Get metric thresholds (low, target, high) for normalization."""
        pass
    
    def normalize_metric(self, value: float, metric_name: str) -> float:
        """Normalize a metric value to 0-100 scale."""
        if metric_name not in self.thresholds:
            return 50  # Default to middle if no threshold defined
        
        low, target, high = self.thresholds[metric_name]
        
        # Handle edge cases
        if value <= low:
            return 0
        elif value >= high:
            return 100
        elif value <= target:
            # Linear interpolation from low to target (0 to 50)
            return 50 * (value - low) / (target - low)
        else:
            # Linear interpolation from target to high (50 to 100)
            return 50 + 50 * (value - target) / (high - target)
    
    def calculate_score(self, metrics: Dict[str, float]) -> float:
        """Calculate weighted score based on metrics."""
        total_score = 0
        total_weight = 0
        
        for metric_name, weight in self.weights.items():
            if metric_name in metrics:
                normalized = self.normalize_metric(metrics[metric_name], metric_name)
                total_score += normalized * weight
                total_weight += weight
        
        # Normalize to 0-100 if weights don't sum to 1
        if total_weight > 0:
            return total_score / total_weight
        return 0


class CashFlowInvestor(InvestorStrategy):
    """Strategy for cash flow focused investors."""
    
    @property
    def name(self) -> str:
        return "cash_flow"
    
    @property
    def description(self) -> str:
        return "Prioritizes immediate cash flow and financial safety"
    
    @property
    def weights(self) -> Dict[str, float]:
        return {
            "coc_return": 0.40,
            "dscr": 0.30,
            "cap_rate": 0.10,
            "irr": 0.10,
            "equity_multiple": 0.10
        }
    
    @property
    def thresholds(self) -> Dict[str, tuple]:
        return {
            "coc_return": (0.02, 0.08, 0.15),
            "dscr": (1.2, 1.5, 2.0),
            "cap_rate": (0.03, 0.055, 0.08),
            "irr": (0.05, 0.12, 0.20),
            "equity_multiple": (1.2, 2.0, 3.0)
        }


class BalancedInvestor(InvestorStrategy):
    """Strategy for balanced growth investors."""
    
    @property
    def name(self) -> str:
        return "balanced"
    
    @property
    def description(self) -> str:
        return "Seeks balance between cash flow and appreciation"
    
    @property
    def weights(self) -> Dict[str, float]:
        return {
            "coc_return": 0.25,
            "dscr": 0.20,
            "cap_rate": 0.10,
            "irr": 0.25,
            "equity_multiple": 0.20
        }
    
    @property
    def thresholds(self) -> Dict[str, tuple]:
        return {
            "coc_return": (0.02, 0.08, 0.15),
            "dscr": (1.2, 1.5, 2.0),
            "cap_rate": (0.03, 0.055, 0.08),
            "irr": (0.05, 0.12, 0.20),
            "equity_multiple": (1.2, 2.0, 3.0)
        }


class AppreciationInvestor(InvestorStrategy):
    """Strategy for appreciation focused investors."""
    
    @property
    def name(self) -> str:
        return "appreciation"
    
    @property
    def description(self) -> str:
        return "Prioritizes long-term appreciation and total returns"
    
    @property
    def weights(self) -> Dict[str, float]:
        return {
            "coc_return": 0.10,
            "dscr": 0.10,
            "cap_rate": 0.10,
            "irr": 0.40,
            "equity_multiple": 0.30
        }
    
    @property
    def thresholds(self) -> Dict[str, tuple]:
        return {
            "coc_return": (0.02, 0.08, 0.15),
            "dscr": (1.2, 1.5, 2.0),
            "cap_rate": (0.03, 0.055, 0.08),
            "irr": (0.05, 0.12, 0.20),
            "equity_multiple": (1.2, 2.0, 3.0)
        }


def get_investor_strategy(profile: str) -> InvestorStrategy:
    """Factory function to get investor strategy by profile name."""
    strategies = {
        "cash_flow": CashFlowInvestor(),
        "balanced": BalancedInvestor(),
        "appreciation": AppreciationInvestor(),
    }
    
    if profile not in strategies:
        raise ValueError(
            f"Unknown investor profile: {profile}. "
            f"Choose from: {', '.join(strategies.keys())}"
        )
    
    return strategies[profile] 