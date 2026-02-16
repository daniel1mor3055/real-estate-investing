"""Financial metrics calculator with investor profile strategies."""

from typing import Dict, List, Optional
import numpy as np
import numpy_financial as npf
from pydantic import BaseModel, Field
from loguru import logger

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
    roe_year1: Optional[MetricResult] = None
    average_roe: Optional[MetricResult] = None
    
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
        
        # IRR Calculation with detailed logging
        logger.info(f"\n{'='*90}")
        logger.info(f"📈 IRR (INTERNAL RATE OF RETURN) CALCULATION | Deal: {self.deal.deal_id}")
        logger.info(f"{'='*90}")
        
        logger.info(f"\n💰 SALE PROCEEDS CALCULATION (Year {holding_period}):")
        logger.info(f"  Property Value = ${sale_price:,.2f}")
        logger.info(f"  Sales Costs ({self.deal.market_assumptions.sales_expense_percent}%) = ${sales_costs:,.2f}")
        logger.info(f"  Loan Payoff = ${loan_payoff:,.2f}")
        logger.info(f"  ➡️  Net Sale Proceeds = ${sale_price:,.2f} - ${sales_costs:,.2f} - ${loan_payoff:,.2f} = ${net_proceeds:,.2f}")
        
        # Build cash flows array
        cash_flows = df['pre_tax_cash_flow'].tolist()
        cash_flows[-1] += net_proceeds  # Add sale proceeds to final year
        
        logger.info(f"\n💵 CASH FLOWS FOR IRR CALCULATION:")
        logger.info(f"  IRR is the rate where NPV of all cash flows = 0")
        logger.info(f"  This means finding the discount rate that makes the present value of all")
        logger.info(f"  inflows equal to the present value of all outflows.\n")
        
        logger.info(f"  Complete Cash Flow Series (Years 0-{holding_period}):")
        total_outflows = 0.0
        total_inflows = 0.0
        for i, cf in enumerate(cash_flows):
            if i == 0:
                logger.info(f"    Year {i}: ${cf:,.2f} (Initial Investment - Outflow)")
                total_outflows += abs(cf)
            elif i == len(cash_flows) - 1:
                logger.info(f"    Year {i}: ${cf:,.2f} (Operating CF + Sale Proceeds)")
                if cf >= 0:
                    total_inflows += cf
                else:
                    total_outflows += abs(cf)
            else:
                if cf >= 0:
                    logger.info(f"    Year {i}: ${cf:,.2f} (Operating Cash Flow)")
                    total_inflows += cf
                else:
                    logger.info(f"    Year {i}: ${cf:,.2f} ⚠️ Negative Cash Flow (Additional Capital)")
                    total_outflows += abs(cf)
        
        logger.info(f"\n  📊 CASH FLOW SUMMARY:")
        logger.info(f"    Total Outflows (Investments): ${total_outflows:,.2f}")
        logger.info(f"    Total Inflows (Returns): ${total_inflows:,.2f}")
        net_cash = total_inflows - total_outflows
        logger.info(f"    Net Cash Flow: ${net_cash:,.2f}")
        
        try:
            irr = float(npf.irr(cash_flows))
            logger.info(f"\n🎯 IRR CALCULATION RESULT:")
            logger.info(f"  Using numpy_financial.irr() function to solve for rate where NPV = 0")
            logger.info(f"  ➡️  IRR = {irr*100:.2f}%")
            
            if irr > 0:
                logger.info(f"\n  ✅ POSITIVE RETURN: The investment generates a {irr*100:.2f}% annualized return")
                logger.info(f"  This is the effective annual rate of return considering:")
                logger.info(f"    - Time value of money (earlier cash flows are worth more)")
                logger.info(f"    - All cash inflows and outflows")
                logger.info(f"    - The complete {holding_period}-year holding period")
            elif irr == 0:
                logger.info(f"\n  ⚠️  BREAKEVEN: The investment returns exactly the cost of capital")
            else:
                logger.info(f"\n  ❌ NEGATIVE RETURN: The investment loses {abs(irr)*100:.2f}% annually")
        except Exception as e:
            irr = 0.0
            logger.info(f"\n  ⚠️  IRR CALCULATION ERROR: {str(e)}")
            logger.info(f"  This can happen when:")
            logger.info(f"    - Cash flows don't change sign (all positive or all negative)")
            logger.info(f"    - Multiple IRRs exist (cash flows alternate signs frequently)")
            logger.info(f"  Setting IRR = 0.0%")
        
        logger.info(f"{'='*90}\n")
        
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
        
        # Equity Multiple - Log detailed calculation
        logger.info(f"\n{'='*90}")
        logger.info(f"📊 EQUITY MULTIPLE CALCULATION | Deal: {self.deal.deal_id}")
        logger.info(f"{'='*90}")
        
        # Calculate components - CORRECT METHOD:
        # Negative cash flows = Additional capital contributions (go in denominator)
        # Positive cash flows = Distributions (go in numerator)
        # This is the standard in private equity and real estate (MOIC calculation)
        
        positive_cash_flows = 0.0
        additional_capital = 0.0
        positive_years = 0
        negative_years = 0
        
        logger.info(f"\n💵 ANALYZING ANNUAL CASH FLOWS (Years 1-{holding_period}):")
        for year in range(1, holding_period + 1):
            if year <= len(df):
                cf = df.loc[year, 'pre_tax_cash_flow']
                if cf >= 0:
                    logger.info(f"  Year {year}: +${cf:,.2f} (Distribution)")
                    positive_cash_flows += cf
                    positive_years += 1
                else:
                    logger.info(f"  Year {year}: ${cf:,.2f} ⚠️ ADDITIONAL CAPITAL REQUIRED")
                    additional_capital += abs(cf)  # Make it positive for clarity
                    negative_years += 1
        
        # Total Invested Capital (Denominator)
        logger.info(f"\n💸 TOTAL INVESTED CAPITAL (Denominator):")
        logger.info(f"  Initial Investment (Year 0) = ${proforma.initial_investment:,.2f}")
        if negative_years > 0:
            logger.info(f"  Additional Capital (from {negative_years} negative years) = ${additional_capital:,.2f}")
            logger.info(f"  ⚠️  Note: Negative cash flow years = additional capital contributions")
        total_invested_capital = proforma.initial_investment + additional_capital
        logger.info(f"  ➡️  Total Invested Capital = ${proforma.initial_investment:,.2f} + ${additional_capital:,.2f} = ${total_invested_capital:,.2f}")
        
        # Total Distributions (Numerator)
        logger.info(f"\n💰 TOTAL DISTRIBUTIONS (Numerator):")
        logger.info(f"  Positive Operating Cash Flows (from {positive_years} years) = ${positive_cash_flows:,.2f}")
        logger.info(f"  Net Sale Proceeds (Year {holding_period}) = ${net_proceeds:,.2f}")
        total_distributions = positive_cash_flows + net_proceeds
        logger.info(f"  ➡️  Total Distributions = ${positive_cash_flows:,.2f} + ${net_proceeds:,.2f} = ${total_distributions:,.2f}")
        
        # Calculate Equity Multiple
        equity_multiple = total_distributions / total_invested_capital if total_invested_capital > 0 else 0
        
        logger.info(f"\n🎯 EQUITY MULTIPLE CALCULATION:")
        logger.info(f"  Formula: Equity Multiple = Total Distributions ÷ Total Invested Capital")
        logger.info(f"  Equity Multiple = ${total_distributions:,.2f} ÷ ${total_invested_capital:,.2f}")
        logger.info(f"  ➡️  Equity Multiple = {equity_multiple:.2f}x")
        
        if equity_multiple > 1.0:
            profit = total_distributions - total_invested_capital
            logger.info(f"\n  ✅ PROFITABLE: For every $1 invested, you get ${equity_multiple:.2f} back")
            logger.info(f"  💵 Total Profit = ${total_distributions:,.2f} - ${total_invested_capital:,.2f} = ${profit:,.2f}")
        elif equity_multiple == 1.0:
            logger.info(f"\n  ⚠️  BREAKEVEN: You get back exactly what you invested")
        else:
            loss = total_invested_capital - total_distributions
            logger.info(f"\n  ❌ LOSS: You get back ${equity_multiple:.2f} for every $1 invested")
            logger.info(f"  💸 Total Loss = ${total_invested_capital:,.2f} - ${total_distributions:,.2f} = ${loss:,.2f}")
        
        logger.info(f"{'='*90}\n")
        
        em_metric = MetricResult.create_equity_multiple(equity_multiple, holding_period)
        
        # ROE Calculation with detailed logging
        logger.info(f"\n{'='*90}")
        logger.info(f"📊 RETURN ON EQUITY (ROE) ANALYSIS | Deal: {self.deal.deal_id}")
        logger.info(f"{'='*90}")
        
        # Get Year 1 ROE from proforma
        year_1_row = df.loc[1]
        roe_year1_value = year_1_row['roe']
        
        logger.info(f"\n💵 YEAR 1 ROE:")
        logger.info(f"  Year 1 Cash Flow = ${year_1_row['pre_tax_cash_flow']:,.2f}")
        logger.info(f"  Year 1 Average Equity = ${year_1_row['average_equity']:,.2f}")
        logger.info(f"  ➡️  Year 1 ROE = ${year_1_row['pre_tax_cash_flow']:,.2f} / ${year_1_row['average_equity']:,.2f} = {roe_year1_value:.2%}")
        
        # Calculate average ROE across all years
        roe_values = df.loc[1:, 'roe']  # Exclude year 0
        avg_roe_value = roe_values.mean()
        
        logger.info(f"\n📈 AVERAGE ROE (Years 1-{holding_period}):")
        logger.info(f"  Average ROE across {holding_period} years = {avg_roe_value:.2%}")
        
        # Show ROE trend
        logger.info(f"\n📊 ROE TREND OVER TIME:")
        for year in [1, 2, 3, 5, 10, holding_period]:
            if year <= holding_period and year in df.index:
                year_roe = df.loc[year, 'roe']
                logger.info(f"    Year {year:2d}: {year_roe:>7.2%}")
        
        logger.info(f"\n💡 ROE INTERPRETATION:")
        logger.info(f"  ROE measures how efficiently your equity is working each year.")
        logger.info(f"  As equity builds (through appreciation + principal paydown), ROE may decline")
        logger.info(f"  if cash flow doesn't grow proportionally. This can signal opportunities to")
        logger.info(f"  refinance or sell and redeploy capital into higher-yielding investments.")
        
        if avg_roe_value < 0.08:
            logger.info(f"\n  ⚠️  BELOW TARGET: Average ROE of {avg_roe_value:.2%} is below typical target (8-12%)")
            logger.info(f"  Consider: Refinancing to extract equity or selling to redeploy capital")
        elif avg_roe_value >= 0.12:
            logger.info(f"\n  ✅ STRONG PERFORMANCE: Average ROE of {avg_roe_value:.2%} indicates efficient equity usage")
        else:
            logger.info(f"\n  ✅ ACCEPTABLE: Average ROE of {avg_roe_value:.2%} is within normal range (8-12%)")
        
        logger.info(f"{'='*90}\n")
        
        roe_year1_metric = MetricResult.create_roe(roe_year1_value, year=1)
        average_roe_metric = MetricResult.create_average_roe(avg_roe_value, holding_period)
        
        return {
            "irr": irr_metric,
            "npv": npv_metric,
            "equity_multiple": em_metric,
            "roe_year1": roe_year1_metric,
            "average_roe": average_roe_metric,
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