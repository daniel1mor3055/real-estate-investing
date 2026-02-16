"""Sensitivity analysis for real estate investments."""

from typing import Dict, List, Tuple, Callable
import numpy as np
from pydantic import BaseModel, Field

from ..core.models import Deal
from ..core.calculators import MetricsCalculator, ProFormaCalculator


class SensitivityResult(BaseModel):
    """Result of a two-variable sensitivity analysis."""

    variable1_name: str
    variable2_name: str
    variable1_values: List[float]
    variable2_values: List[float]
    metric_name: str
    metric_grid: List[List[float]]  # 2D grid of metric values
    base_value: float  # Metric value at base case (0%, 0%)
    
    def to_numpy_grid(self) -> np.ndarray:
        """Convert metric grid to numpy array."""
        return np.array(self.metric_grid)
    
    def get_value_at(self, var1_pct: float, var2_pct: float) -> float:
        """Get the metric value at specific percentage changes."""
        # Find closest indices
        var1_idx = min(
            range(len(self.variable1_values)),
            key=lambda i: abs(self.variable1_values[i] - var1_pct)
        )
        var2_idx = min(
            range(len(self.variable2_values)),
            key=lambda i: abs(self.variable2_values[i] - var2_pct)
        )
        return self.metric_grid[var2_idx][var1_idx]


class SensitivityAnalyzer:
    """Performs sensitivity analysis on real estate deals."""

    # Mapping of variable names to deal attribute paths
    VARIABLE_MAP = {
        "purchase_price": ("property", "purchase_price"),
        "rent": ("income", "monthly_rent_per_unit"),
        "vacancy_rate": ("income", "vacancy_rate_percent"),
        "interest_rate": ("financing", "interest_rate"),
        "appreciation": ("market_assumptions", "annual_appreciation_percent"),
        "expense_growth": ("expenses", "annual_expense_growth_percent"),
        "rent_growth": ("income", "annual_rent_increase_percent"),
        "down_payment": ("financing", "down_payment_percent"),
        "property_tax": ("expenses", "property_tax_annual"),
        "insurance": ("expenses", "insurance_annual"),
    }

    def __init__(self, deal: Deal):
        """Initialize the analyzer with a base deal.
        
        Args:
            deal: The base deal to analyze
        """
        self.base_deal = deal

    def analyze(
        self,
        variable1: str,
        variable2: str,
        range1: Tuple[float, float] = (-10, 10),
        range2: Tuple[float, float] = (-10, 10),
        steps: int = 10,
        target_metric: str = "irr",
        holding_period: int = 10,
    ) -> SensitivityResult:
        """Run two-variable sensitivity analysis.
        
        Args:
            variable1: First variable to vary
            variable2: Second variable to vary
            range1: Percentage range for variable1 (min%, max%)
            range2: Percentage range for variable2 (min%, max%)
            steps: Number of steps in each dimension
            target_metric: Metric to calculate
            holding_period: Holding period for calculations
            
        Returns:
            SensitivityResult with grid of metric values
        """
        # Validate variables
        if variable1 not in self.VARIABLE_MAP:
            raise ValueError(f"Unknown variable: {variable1}. Valid options: {list(self.VARIABLE_MAP.keys())}")
        if variable2 not in self.VARIABLE_MAP:
            raise ValueError(f"Unknown variable: {variable2}. Valid options: {list(self.VARIABLE_MAP.keys())}")

        # Create percentage ranges
        var1_pcts = np.linspace(range1[0], range1[1], steps).tolist()
        var2_pcts = np.linspace(range2[0], range2[1], steps).tolist()

        # Calculate base case value
        base_metric = self._calculate_metric(self.base_deal, target_metric, holding_period)

        # Build the grid
        metric_grid = []
        for var2_pct in var2_pcts:
            row = []
            for var1_pct in var1_pcts:
                # Create modified deal
                modified_deal = self._apply_percentage_change(
                    variable1, var1_pct, variable2, var2_pct
                )
                
                # Calculate metric
                metric_value = self._calculate_metric(
                    modified_deal, target_metric, holding_period
                )
                row.append(metric_value)
            metric_grid.append(row)

        return SensitivityResult(
            variable1_name=variable1,
            variable2_name=variable2,
            variable1_values=var1_pcts,
            variable2_values=var2_pcts,
            metric_name=target_metric,
            metric_grid=metric_grid,
            base_value=base_metric,
        )

    def analyze_single_variable(
        self,
        variable: str,
        range_pct: Tuple[float, float] = (-20, 20),
        steps: int = 20,
        target_metrics: List[str] = None,
        holding_period: int = 10,
    ) -> Dict[str, List[Tuple[float, float]]]:
        """Run single-variable sensitivity analysis for multiple metrics.
        
        Args:
            variable: Variable to vary
            range_pct: Percentage range (min%, max%)
            steps: Number of steps
            target_metrics: List of metrics to calculate (defaults to common ones)
            holding_period: Holding period for calculations
            
        Returns:
            Dictionary mapping metric names to list of (pct_change, value) tuples
        """
        if target_metrics is None:
            target_metrics = ["coc_return", "irr", "dscr", "cap_rate"]

        if variable not in self.VARIABLE_MAP:
            raise ValueError(f"Unknown variable: {variable}")

        percentages = np.linspace(range_pct[0], range_pct[1], steps).tolist()
        results = {metric: [] for metric in target_metrics}

        for pct in percentages:
            # Create modified deal
            modified_deal = self._apply_percentage_change(variable, pct)
            
            for metric in target_metrics:
                value = self._calculate_metric(modified_deal, metric, holding_period)
                results[metric].append((pct, value))

        return results

    def _apply_percentage_change(
        self,
        variable1: str,
        pct1: float,
        variable2: str = None,
        pct2: float = None,
    ) -> Deal:
        """Create a modified deal with percentage changes applied.
        
        Args:
            variable1: First variable to modify
            pct1: Percentage change for variable1
            variable2: Optional second variable to modify
            pct2: Percentage change for variable2
            
        Returns:
            Modified Deal object
        """
        # Deep copy the base deal
        modified = self.base_deal.model_copy(deep=True)

        # Apply first change
        self._set_modified_value(modified, variable1, pct1)

        # Apply second change if provided
        if variable2 and pct2 is not None:
            self._set_modified_value(modified, variable2, pct2)

        # Recalculate financing if needed
        if variable1 in ("purchase_price", "down_payment") or variable2 in ("purchase_price", "down_payment"):
            modified.financing.calculate_loan_details(modified.property.purchase_price)

        return modified

    def _set_modified_value(self, deal: Deal, variable: str, pct_change: float) -> None:
        """Set a modified value on the deal based on percentage change."""
        path = self.VARIABLE_MAP[variable]
        
        # Navigate to the attribute
        obj = deal
        for attr in path[:-1]:
            obj = getattr(obj, attr)
        
        # Get current value and apply change
        current = getattr(obj, path[-1])
        new_value = current * (1 + pct_change / 100)
        
        # Handle special cases
        if "percent" in path[-1] or "rate" in path[-1]:
            # For percentages, add the change directly instead of multiplying
            new_value = current + pct_change
            new_value = max(0, new_value)  # Ensure non-negative
        
        setattr(obj, path[-1], new_value)

    def _calculate_metric(
        self, deal: Deal, metric_name: str, holding_period: int
    ) -> float:
        """Calculate a specific metric for a deal."""
        # Quick metrics that don't need full calculation
        quick_metrics = {
            "cap_rate": lambda d: d.get_cap_rate(),
            "coc_return": lambda d: d.get_cash_on_cash_return(),
            "dscr": lambda d: d.get_debt_service_coverage_ratio(),
            "noi": lambda d: d.get_year_1_noi(),
            "cash_flow": lambda d: d.get_year_1_cash_flow(),
            "grm": lambda d: d.get_gross_rent_multiplier(),
        }

        if metric_name in quick_metrics:
            value = quick_metrics[metric_name](deal)
            if value == float('inf'):
                return 999.99
            return value

        # Metrics requiring full calculation
        calculator = MetricsCalculator(deal)
        result = calculator.calculate(holding_period=holding_period)
        
        if not result.success:
            return 0.0

        metrics = result.data
        
        metric_map = {
            "irr": metrics.irr.value if metrics.irr else 0,
            "npv": metrics.npv.value if metrics.npv else 0,
            "equity_multiple": metrics.equity_multiple.value if metrics.equity_multiple else 0,
            "break_even_ratio": metrics.break_even_ratio.value if metrics.break_even_ratio else 0,
        }
        
        return metric_map.get(metric_name, 0)
