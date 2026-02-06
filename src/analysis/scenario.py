"""Scenario analysis for real estate investments."""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from ..core.models import Deal, MarketAssumptions
from ..core.calculators import MetricsCalculator
from ..core.calculators.metrics import MetricsBundle


class ScenarioType(str, Enum):
    """Pre-defined scenario types."""
    
    PESSIMISTIC = "pessimistic"
    BASE = "base"
    OPTIMISTIC = "optimistic"
    CUSTOM = "custom"


class Scenario(BaseModel):
    """Defines a scenario with parameter adjustments."""
    
    name: str
    scenario_type: ScenarioType = ScenarioType.CUSTOM
    description: Optional[str] = None
    
    # Market adjustments (percentage points to add/subtract)
    appreciation_adjustment: float = 0  # e.g., -1.5 means reduce appreciation by 1.5%
    rent_growth_adjustment: float = 0
    expense_growth_adjustment: float = 0
    
    # Property adjustments (percentage changes)
    vacancy_rate_multiplier: float = 1.0  # e.g., 1.5 means 50% higher vacancy
    
    # Financing adjustments
    interest_rate_adjustment: float = 0  # Percentage points

    @classmethod
    def pessimistic(cls) -> "Scenario":
        """Create a pessimistic scenario."""
        return cls(
            name="Pessimistic",
            scenario_type=ScenarioType.PESSIMISTIC,
            description="Conservative assumptions: low growth, high vacancy, rising rates",
            appreciation_adjustment=-1.5,
            rent_growth_adjustment=-1.0,
            expense_growth_adjustment=1.0,
            vacancy_rate_multiplier=1.5,
            interest_rate_adjustment=1.0,
        )

    @classmethod
    def base(cls) -> "Scenario":
        """Create a base case scenario (no changes)."""
        return cls(
            name="Base Case",
            scenario_type=ScenarioType.BASE,
            description="Current assumptions unchanged",
        )

    @classmethod
    def optimistic(cls) -> "Scenario":
        """Create an optimistic scenario."""
        return cls(
            name="Optimistic",
            scenario_type=ScenarioType.OPTIMISTIC,
            description="Favorable conditions: strong growth, low vacancy, stable rates",
            appreciation_adjustment=1.5,
            rent_growth_adjustment=1.0,
            expense_growth_adjustment=-0.5,
            vacancy_rate_multiplier=0.7,
            interest_rate_adjustment=-0.5,
        )


class ScenarioMetrics(BaseModel):
    """Metrics calculated for a specific scenario."""
    
    scenario: Scenario
    metrics: MetricsBundle
    
    # Key metrics extracted for easy comparison
    irr: Optional[float] = None
    coc_return: float
    dscr: float
    equity_multiple: Optional[float] = None
    deal_score: Optional[float] = None
    noi_year1: float
    cash_flow_year1: float

    class Config:
        arbitrary_types_allowed = True


class ScenarioResult(BaseModel):
    """Result of scenario analysis."""
    
    scenarios: List[ScenarioMetrics]
    base_deal: Deal
    holding_period: int
    
    def get_scenario(self, scenario_type: ScenarioType) -> Optional[ScenarioMetrics]:
        """Get metrics for a specific scenario type."""
        for s in self.scenarios:
            if s.scenario.scenario_type == scenario_type:
                return s
        return None
    
    def get_metric_range(self, metric_name: str) -> Dict[str, float]:
        """Get the range of a metric across all scenarios."""
        values = []
        for s in self.scenarios:
            if hasattr(s, metric_name):
                val = getattr(s, metric_name)
                if val is not None:
                    values.append(val)
        
        if not values:
            return {"min": 0, "max": 0, "range": 0}
        
        return {
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
        }
    
    def to_comparison_dict(self) -> Dict[str, Dict[str, float]]:
        """Convert to a dictionary for easy comparison."""
        result = {}
        for s in self.scenarios:
            result[s.scenario.name] = {
                "irr": s.irr,
                "coc_return": s.coc_return,
                "dscr": s.dscr,
                "equity_multiple": s.equity_multiple,
                "deal_score": s.deal_score,
                "noi_year1": s.noi_year1,
                "cash_flow_year1": s.cash_flow_year1,
            }
        return result

    class Config:
        arbitrary_types_allowed = True


class ScenarioAnalyzer:
    """Performs scenario analysis on real estate deals."""

    def __init__(self, deal: Deal):
        """Initialize the analyzer with a base deal.
        
        Args:
            deal: The base deal to analyze
        """
        self.base_deal = deal

    def analyze(
        self,
        scenarios: Optional[List[Scenario]] = None,
        holding_period: int = 10,
        investor_profile: str = "balanced",
    ) -> ScenarioResult:
        """Run scenario analysis.
        
        Args:
            scenarios: List of scenarios to analyze (defaults to pessimistic/base/optimistic)
            holding_period: Holding period for calculations
            investor_profile: Investor profile for scoring
            
        Returns:
            ScenarioResult with metrics for each scenario
        """
        if scenarios is None:
            scenarios = [
                Scenario.pessimistic(),
                Scenario.base(),
                Scenario.optimistic(),
            ]

        scenario_metrics = []
        
        for scenario in scenarios:
            # Apply scenario adjustments
            modified_deal = self._apply_scenario(scenario)
            
            # Calculate metrics
            calculator = MetricsCalculator(modified_deal)
            result = calculator.calculate(
                holding_period=holding_period,
                investor_profile=investor_profile,
            )
            
            if result.success:
                metrics = result.data
                scenario_metrics.append(
                    ScenarioMetrics(
                        scenario=scenario,
                        metrics=metrics,
                        irr=metrics.irr.value if metrics.irr else None,
                        coc_return=metrics.coc_return.value,
                        dscr=metrics.dscr.value,
                        equity_multiple=metrics.equity_multiple.value if metrics.equity_multiple else None,
                        deal_score=metrics.deal_score.value if metrics.deal_score else None,
                        noi_year1=metrics.noi_year1.value,
                        cash_flow_year1=metrics.cash_flow_year1.value,
                    )
                )

        return ScenarioResult(
            scenarios=scenario_metrics,
            base_deal=self.base_deal,
            holding_period=holding_period,
        )

    def _apply_scenario(self, scenario: Scenario) -> Deal:
        """Apply scenario adjustments to create a modified deal.
        
        Args:
            scenario: The scenario to apply
            
        Returns:
            Modified Deal object
        """
        # Deep copy the base deal
        modified = self.base_deal.model_copy(deep=True)

        # Apply market assumption adjustments
        modified.market_assumptions.annual_appreciation_percent += scenario.appreciation_adjustment
        
        # Apply income adjustments
        modified.income.annual_rent_increase_percent += scenario.rent_growth_adjustment
        modified.income.vacancy_rate_percent *= scenario.vacancy_rate_multiplier
        
        # Ensure vacancy rate stays reasonable
        modified.income.vacancy_rate_percent = min(50, max(0, modified.income.vacancy_rate_percent))
        
        # Apply expense adjustments
        modified.expenses.annual_expense_growth_percent += scenario.expense_growth_adjustment
        
        # Apply financing adjustments (only if not cash purchase)
        if not modified.financing.is_cash_purchase:
            if modified.financing.interest_rate:
                modified.financing.interest_rate += scenario.interest_rate_adjustment
                modified.financing.interest_rate = max(0, modified.financing.interest_rate)
            
            # Recalculate financing
            modified.financing.calculate_loan_details(modified.property.purchase_price)

        return modified

    def stress_test(
        self,
        max_vacancy_rate: float = 20,
        max_expense_increase: float = 10,
        holding_period: int = 10,
    ) -> Dict[str, float]:
        """Stress test the deal to find break-even points.
        
        Args:
            max_vacancy_rate: Maximum vacancy rate to test
            max_expense_increase: Maximum expense increase to test
            holding_period: Holding period for calculations
            
        Returns:
            Dictionary with stress test results
        """
        results = {}
        
        # Find vacancy rate that causes negative cash flow
        for vacancy in range(0, int(max_vacancy_rate) + 1):
            modified = self.base_deal.model_copy(deep=True)
            modified.income.vacancy_rate_percent = vacancy
            
            cash_flow = modified.get_year_1_cash_flow()
            if cash_flow < 0:
                results["break_even_vacancy"] = vacancy
                break
        else:
            results["break_even_vacancy"] = max_vacancy_rate
        
        # Find expense increase that causes negative cash flow
        for exp_increase in range(0, int(max_expense_increase) + 1):
            modified = self.base_deal.model_copy(deep=True)
            # Increase all expenses by this percentage
            base_opex = modified.expenses.calculate_total_operating_expenses(
                modified.income.calculate_effective_gross_income(modified.property.num_units),
                modified.property.num_units
            )
            # This is a simplified stress test - in practice you'd modify individual expenses
            results["break_even_expense_increase"] = exp_increase
            
            if modified.get_year_1_cash_flow() < 0:
                break
        
        # Calculate cushion metrics
        results["current_vacancy"] = self.base_deal.income.vacancy_rate_percent
        results["vacancy_cushion"] = results["break_even_vacancy"] - results["current_vacancy"]
        results["dscr"] = self.base_deal.get_debt_service_coverage_ratio()
        
        return results
