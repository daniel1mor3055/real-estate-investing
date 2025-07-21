"""Financial metrics calculator with investor profile strategies."""

from typing import Dict, List, Optional
import numpy as np
import numpy_financial as npf
from pydantic import BaseModel, Field

from .base import Calculator, CalculatorResult
from .proforma import ProFormaCalculator
from ..models.metrics import MetricResult, MetricType
from ..strategies.investor import InvestorStrategy, get_investor_strategy


class MetricsBundle(BaseModel):
    """Bundle of calculated metrics."""
    
    # Basic Metrics
    noi_year1: MetricResult
    cap_rate: MetricResult
    cash_flow_year1: MetricResult
    coc_return: MetricResult
    dscr: MetricResult
    grm: MetricResult
    
    # Advanced Metrics (if calculated)
    irr: Optional[MetricResult] = None
    npv: Optional[MetricResult] = None
    equity_multiple: Optional[MetricResult] = None
    
    # Deal Score
    deal_score: Optional[MetricResult] = None
    
    # Risk Metrics
    break_even_ratio: Optional[MetricResult] = None
    
    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to simple dictionary."""
        result = {}
        for field_name, field_value in self:
            if isinstance(field_value, MetricResult):
                result[field_name] = field_value.value
        return result
    
    def get_all_metrics(self) -> List[MetricResult]:
        """Get all metrics as a list."""
        metrics = []
        for field_name, field_value in self:
            if isinstance(field_value, MetricResult):
                metrics.append(field_value)
        return metrics


class MetricsCalculator(Calculator):
    """Calculator for all financial metrics."""
    
    def calculate(
        self, 
        holding_period: int = 10,
        investor_profile: str = "balanced",
        discount_rate: float = 0.10,
        **kwargs
    ) -> CalculatorResult[MetricsBundle]:
        """Calculate all metrics for the deal."""
        errors = self.validate_inputs()
        if errors:
            return CalculatorResult(
                success=False,
                data=None,
                errors=errors
            )
        
        # Calculate basic metrics
        basic_metrics = self._calculate_basic_metrics()
        
        # Calculate advanced metrics if holding period specified
        advanced_metrics = {}
        if holding_period > 0:
            advanced_metrics = self._calculate_advanced_metrics(
                holding_period, 
                discount_rate
            )
        
        # Calculate deal score
        deal_score = None
        if investor_profile:
            deal_score = self._calculate_deal_score(
                basic_metrics,
                advanced_metrics,
                investor_profile,
                holding_period
            )
        
        # Create metrics bundle
        metrics_bundle = MetricsBundle(
            **basic_metrics,
            **advanced_metrics,
            deal_score=deal_score
        )
        
        return CalculatorResult(
            success=True,
            data=metrics_bundle,
            metadata={
                "holding_period": holding_period,
                "investor_profile": investor_profile,
                "discount_rate": discount_rate
            }
        )
    
    def _calculate_basic_metrics(self) -> Dict[str, MetricResult]:
        """Calculate basic year 1 metrics."""
        deal = self.deal
        
        # NOI
        noi = deal.get_year_1_noi()
        noi_metric = MetricResult.create_noi(noi)
        
        # Cap Rate
        cap_rate = deal.get_cap_rate()
        cap_rate_metric = MetricResult.create_cap_rate(cap_rate)
        
        # Cash Flow
        cash_flow = deal.get_year_1_cash_flow()
        cash_flow_metric = MetricResult(
            metric_type=MetricType.CASH_FLOW,
            value=cash_flow,
            formatted_value=f"${cash_flow:,.0f}",
            year=1
        )
        
        # Cash-on-Cash Return
        coc = deal.get_cash_on_cash_return()
        coc_metric = MetricResult.create_coc_return(coc)
        
        # DSCR
        dscr = deal.get_debt_service_coverage_ratio()
        if dscr == float('inf'):
            dscr = 999.99  # Cap at reasonable number for display
        dscr_metric = MetricResult.create_dscr(dscr)
        
        # GRM
        grm = deal.get_gross_rent_multiplier()
        grm_metric = MetricResult(
            metric_type=MetricType.GRM,
            value=grm,
            formatted_value=f"{grm:.2f}",
            benchmark_low=4.0,
            benchmark_target=8.0,
            benchmark_high=12.0
        )
        
        # Break-even ratio
        if deal.income.calculate_effective_gross_income(deal.property.num_units) > 0:
            egi = deal.income.calculate_effective_gross_income(deal.property.num_units)
            total_expenses = (
                deal.expenses.calculate_total_operating_expenses(egi, deal.property.num_units) +
                deal.financing.annual_debt_service
            )
            break_even = total_expenses / egi
        else:
            break_even = 1.0
            
        break_even_metric = MetricResult(
            metric_type=MetricType.BREAK_EVEN_RATIO,
            value=break_even,
            formatted_value=f"{break_even:.2%}",
            benchmark_low=0.70,
            benchmark_target=0.85,
            benchmark_high=0.95
        )
        
        return {
            "noi_year1": noi_metric,
            "cap_rate": cap_rate_metric,
            "cash_flow_year1": cash_flow_metric,
            "coc_return": coc_metric,
            "dscr": dscr_metric,
            "grm": grm_metric,
            "break_even_ratio": break_even_metric
        }
    
    def _calculate_advanced_metrics(
        self, 
        holding_period: int,
        discount_rate: float
    ) -> Dict[str, MetricResult]:
        """Calculate advanced metrics requiring pro-forma."""
        # Get pro-forma
        proforma_calc = ProFormaCalculator(self.deal)
        proforma_result = proforma_calc.calculate(years=holding_period)
        
        if not proforma_result.success:
            return {}
        
        proforma = proforma_result.data
        df = proforma.to_dataframe()
        
        # Calculate sale proceeds
        final_year = df.iloc[-1]
        sale_price = final_year['property_value']
        sales_costs = sale_price * (self.deal.market_assumptions.sales_expense_percent / 100)
        loan_payoff = final_year['loan_balance']
        net_proceeds = sale_price - sales_costs - loan_payoff
        
        # IRR Calculation
        cash_flows = df['pre_tax_cash_flow'].tolist()
        cash_flows[-1] += net_proceeds  # Add sale proceeds to final year
        
        try:
            irr = float(npf.irr(cash_flows))
        except:
            irr = 0.0
        
        irr_metric = MetricResult.create_irr(irr, holding_period)
        
        # NPV Calculation
        try:
            npv = float(npf.npv(discount_rate, cash_flows))
        except:
            npv = 0.0
            
        npv_metric = MetricResult(
            metric_type=MetricType.NPV,
            value=npv,
            formatted_value=f"${npv:,.0f}",
            holding_period=holding_period,
            metadata={"discount_rate": discount_rate}
        )
        
        # Equity Multiple
        total_distributions = df.loc[1:, 'pre_tax_cash_flow'].sum() + net_proceeds
        equity_multiple = total_distributions / proforma.initial_investment if proforma.initial_investment > 0 else 0
        
        em_metric = MetricResult.create_equity_multiple(equity_multiple, holding_period)
        
        return {
            "irr": irr_metric,
            "npv": npv_metric,
            "equity_multiple": em_metric
        }
    
    def _calculate_deal_score(
        self,
        basic_metrics: Dict[str, MetricResult],
        advanced_metrics: Dict[str, MetricResult],
        investor_profile: str,
        holding_period: int
    ) -> MetricResult:
        """Calculate weighted deal score based on investor profile."""
        # Get investor strategy
        strategy = get_investor_strategy(investor_profile)
        
        # Prepare metrics for scoring
        metrics_dict = {
            "coc_return": basic_metrics["coc_return"].value,
            "dscr": min(basic_metrics["dscr"].value, 3.0),  # Cap DSCR at 3.0
            "cap_rate": basic_metrics["cap_rate"].value,
        }
        
        if "irr" in advanced_metrics:
            metrics_dict["irr"] = advanced_metrics["irr"].value
        if "equity_multiple" in advanced_metrics:
            metrics_dict["equity_multiple"] = advanced_metrics["equity_multiple"].value
        
        # Calculate score
        score = strategy.calculate_score(metrics_dict)
        
        return MetricResult.create_deal_score(
            score,
            investor_profile,
            holding_period
        ) 