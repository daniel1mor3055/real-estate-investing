"""Analysis service - coordinates advanced analysis operations."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel

from ..core.models import Deal
from ..core.calculators import MetricsCalculator, ProFormaCalculator
from ..analysis.sensitivity import SensitivityAnalyzer, SensitivityResult
from ..analysis.scenario import ScenarioAnalyzer, ScenarioResult, Scenario


class AnalysisService:
    """Service for advanced deal analysis operations."""

    def run_sensitivity_analysis(
        self,
        deal: Deal,
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
            deal: Base deal to analyze
            variable1: First variable to vary (e.g., 'purchase_price', 'rent', 'vacancy_rate')
            variable2: Second variable to vary
            range1: Percentage range for variable1 (min%, max%)
            range2: Percentage range for variable2 (min%, max%)
            steps: Number of steps in each dimension
            target_metric: Metric to calculate (irr, coc_return, npv, etc.)
            holding_period: Holding period for calculations
            
        Returns:
            SensitivityResult with grid of metric values
        """
        analyzer = SensitivityAnalyzer(deal)
        return analyzer.analyze(
            variable1=variable1,
            variable2=variable2,
            range1=range1,
            range2=range2,
            steps=steps,
            target_metric=target_metric,
            holding_period=holding_period,
        )

    def run_scenario_analysis(
        self,
        deal: Deal,
        scenarios: Optional[List[Scenario]] = None,
        holding_period: int = 10,
    ) -> ScenarioResult:
        """Run scenario analysis with pessimistic, base, and optimistic cases.
        
        Args:
            deal: Base deal to analyze
            scenarios: Custom scenarios (uses defaults if None)
            holding_period: Holding period for calculations
            
        Returns:
            ScenarioResult with metrics for each scenario
        """
        analyzer = ScenarioAnalyzer(deal)
        return analyzer.analyze(
            scenarios=scenarios,
            holding_period=holding_period,
        )

    def calculate_break_even_rent(
        self,
        deal: Deal,
    ) -> float:
        """Calculate the minimum rent needed to break even.
        
        Args:
            deal: The deal to analyze
            
        Returns:
            Monthly rent per unit needed for zero cash flow
        """
        # Binary search for break-even rent
        low = 0
        high = deal.income.monthly_rent_per_unit * 3  # Upper bound
        
        while high - low > 1:
            mid = (low + high) / 2
            
            # Create modified deal with test rent
            test_deal = deal.model_copy(deep=True)
            test_deal.income.monthly_rent_per_unit = mid
            
            # Calculate cash flow
            cash_flow = test_deal.get_year_1_cash_flow()
            
            if cash_flow < 0:
                low = mid
            else:
                high = mid
        
        return high

    def calculate_max_purchase_price(
        self,
        deal: Deal,
        target_coc: float = 0.08,
    ) -> float:
        """Calculate maximum purchase price to achieve target cash-on-cash return.
        
        Args:
            deal: The deal to analyze
            target_coc: Target cash-on-cash return (e.g., 0.08 for 8%)
            
        Returns:
            Maximum purchase price
        """
        # Binary search for max price
        low = 0
        high = deal.property.purchase_price * 2  # Upper bound
        
        while high - low > 1000:  # $1000 precision
            mid = (low + high) / 2
            
            # Create modified deal with test price
            test_deal = deal.model_copy(deep=True)
            test_deal.property.purchase_price = mid
            test_deal.financing.calculate_loan_details(mid)
            
            # Calculate CoC
            coc = test_deal.get_cash_on_cash_return()
            
            if coc > target_coc:
                low = mid
            else:
                high = mid
        
        return low

    def compare_holding_periods(
        self,
        deal: Deal,
        periods: List[int],
        discount_rate: float = 0.10,
    ) -> List[Dict]:
        """Compare key metrics across multiple holding periods.

        Args:
            deal: Base deal to analyze
            periods: List of holding periods in years (e.g., [5, 10, 15, 20])
            discount_rate: Discount rate for NPV calculation

        Returns:
            List of dicts, one per period, with IRR, equity multiple, NPV, CoC, and more.
        """
        results = []

        for period in periods:
            metrics_calc = MetricsCalculator(deal)
            metrics_result = metrics_calc.calculate(
                holding_period=period,
                discount_rate=discount_rate,
            )

            if not metrics_result.success:
                continue

            m = metrics_result.data
            results.append({
                "holding_period": period,
                "irr": m.irr.value if m.irr else None,
                "equity_multiple": m.equity_multiple.value if m.equity_multiple else None,
                "npv": m.npv.value if m.npv else None,
                "coc_return": m.coc_return.value,
                "dscr": m.dscr.value,
                "average_roe": m.average_roe.value if m.average_roe else None,
            })

        return results

    def compare_financing_options(
        self,
        deal: Deal,
        financing_options: List[Dict],
        holding_period: int = 10,
    ) -> List[Dict]:
        """Compare different financing options for the same deal.
        
        Args:
            deal: Base deal to analyze
            financing_options: List of financing configurations to compare
            holding_period: Holding period for calculations
            
        Returns:
            List of results with metrics for each option
        """
        results = []
        
        for i, fin_config in enumerate(financing_options):
            # Create deal copy with modified financing
            test_deal = deal.model_copy(deep=True)
            
            # Apply financing changes
            if "down_payment_percent" in fin_config:
                test_deal.financing.down_payment_percent = fin_config["down_payment_percent"]
            if "interest_rate" in fin_config:
                test_deal.financing.interest_rate = fin_config["interest_rate"]
            if "loan_term_years" in fin_config:
                test_deal.financing.loan_term_years = fin_config["loan_term_years"]
            
            # Recalculate loan details
            test_deal.financing.calculate_loan_details(test_deal.property.purchase_price)
            
            # Calculate metrics
            metrics_calc = MetricsCalculator(test_deal)
            metrics_result = metrics_calc.calculate(holding_period=holding_period)
            
            if metrics_result.success:
                results.append({
                    "option": i + 1,
                    "name": fin_config.get("name", f"Option {i + 1}"),
                    "config": fin_config,
                    "total_cash_needed": test_deal.get_total_cash_needed(),
                    "monthly_payment": test_deal.financing.monthly_payment,
                    "coc_return": metrics_result.data.coc_return.value,
                    "irr": metrics_result.data.irr.value if metrics_result.data.irr else None,
                    "dscr": metrics_result.data.dscr.value,
                })
        
        return results
