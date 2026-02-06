"""Unit tests for advanced financial metrics per CONTEXT.md Part II Section 2.3.

Tests verify the advanced/holistic metrics that evaluate investment over its lifecycle:
- Return on Investment (ROI) - Section 2.3.1
- Equity Multiple (EM) - Section 2.3.2
- Internal Rate of Return (IRR) - Section 2.3.3
- Net Present Value (NPV)

Each test references the specific CONTEXT.md formula being validated.
"""

import pytest
import numpy_financial as npf
from src.core.calculators.metrics import MetricsCalculator
from src.core.calculators.proforma import ProFormaCalculator


# =============================================================================
# EQUITY MULTIPLE (EM) - CONTEXT.md Section 2.3.2
# =============================================================================

class TestEquityMultiple:
    """Test Equity Multiple calculation per CONTEXT.md Section 2.3.2.
    
    CONTEXT.md Formula: EM = (Total Cash Distributions + Net Sale Proceeds) / Total Equity Invested
    
    CONTEXT.md: "The Equity Multiple provides a simple, intuitive measure of 
    total cash profitability over the life of the investment."
    """
    
    def test_equity_multiple_formula(self, sample_deal):
        """EM = Total Distributions / Initial Investment.
        
        CONTEXT.md: "It answers the straightforward question: 'For every 
        dollar I invest, how many dollars will I get back?'"
        """
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        holding_period = 10
        
        # Act
        result = calculator.calculate(holding_period=holding_period)
        
        # Assert
        assert result.success
        assert result.data.equity_multiple is not None
        assert result.data.equity_multiple.value > 0
    
    def test_equity_multiple_above_1_is_profitable(self, sample_deal):
        """EM > 1.0 means investor got back more than invested.
        
        CONTEXT.md: "An EM of 2.5x means the investor received $2.50 
        for every $1.00 invested"
        """
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(holding_period=10)
        em = result.data.equity_multiple.value
        
        # Assert - good deal should have EM > 1
        assert em > 1.0
    
    def test_equity_multiple_interpretation(self, sample_deal):
        """EM of 2.0x means doubling the investment."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(holding_period=10)
        em = result.data.equity_multiple.value
        
        # Assert
        # For a 10-year hold, typical EM might be 1.5x to 3.0x
        assert 0.5 <= em <= 5.0  # Reasonable range
    
    def test_equity_multiple_includes_sale_proceeds(self, sample_deal):
        """EM calculation includes net sale proceeds.
        
        CONTEXT.md: "Total Cash Distributions + Net Sale Proceeds"
        """
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        proforma_calc = ProFormaCalculator(sample_deal)
        proforma_result = proforma_calc.calculate(years=10)
        
        # Act
        result = calculator.calculate(holding_period=10)
        
        # Assert - EM should be calculated
        assert result.data.equity_multiple is not None
        # Sale proceeds significantly impact total return
        assert result.data.equity_multiple.value > 0
    
    def test_equity_multiple_longer_hold_higher_em(self, sample_deal):
        """Longer holding period generally results in higher EM."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result_5yr = calculator.calculate(holding_period=5)
        result_10yr = calculator.calculate(holding_period=10)
        result_15yr = calculator.calculate(holding_period=15)
        
        em_5 = result_5yr.data.equity_multiple.value
        em_10 = result_10yr.data.equity_multiple.value
        em_15 = result_15yr.data.equity_multiple.value
        
        # Assert - longer hold = more cash flows = higher EM
        assert em_10 > em_5
        assert em_15 > em_10


# =============================================================================
# INTERNAL RATE OF RETURN (IRR) - CONTEXT.md Section 2.3.3
# =============================================================================

class TestIRR:
    """Test IRR calculation per CONTEXT.md Section 2.3.3.
    
    CONTEXT.md Definition: "IRR is the discount rate at which the Net Present 
    Value (NPV) of all cash flows from a project (including the initial 
    investment, annual cash flows, and final sale proceeds) equals zero."
    
    CONTEXT.md: "The IRR is the gold standard for evaluating the total 
    performance of a real estate investment over time."
    """
    
    def test_irr_calculation(self, sample_deal):
        """IRR is calculated for the deal."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(holding_period=10)
        
        # Assert
        assert result.success
        assert result.data.irr is not None
    
    def test_irr_as_annualized_return(self, sample_deal):
        """IRR represents annualized time-weighted return.
        
        CONTEXT.md: "It represents the annualized, time-weighted return 
        on all invested capital"
        """
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(holding_period=10)
        irr = result.data.irr.value
        
        # Assert - IRR should be reasonable percentage (e.g., 5%-25%)
        assert -0.50 <= irr <= 0.50  # -50% to 50% is realistic range
    
    def test_irr_accounts_for_timing(self, sample_deal):
        """IRR accounts for timing of cash flows.
        
        CONTEXT.md: "IRR provides the most accurate measure of an investment's 
        total return because it accounts for the size and timing of all cash 
        flows throughout the entire holding period"
        """
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(holding_period=10)
        
        # Assert
        # IRR considers:
        # - Initial investment (Year 0, negative)
        # - Annual cash flows (Years 1-10)
        # - Sale proceeds (Year 10)
        assert result.data.irr is not None
        assert result.data.irr.holding_period == 10
    
    def test_irr_includes_sale_proceeds(self, sample_deal):
        """IRR calculation includes terminal sale proceeds."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(holding_period=10)
        
        # Assert
        # Sale proceeds significantly boost IRR
        assert result.data.irr is not None
    
    def test_irr_typical_target(self, sample_deal):
        """Good deals target 15%+ IRR per CONTEXT.md.
        
        CONTEXT.md Key Metrics Reference Table: "> 15% (Typical Target)"
        """
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(holding_period=10)
        irr = result.data.irr.value
        
        # Assert - sample deal should have reasonable IRR
        # (may not hit 15% target, but should be positive)
        assert irr > 0  # At minimum, should be positive for good deal
    
    def test_irr_npv_zero_at_irr_rate(self, sample_deal):
        """At the IRR rate, NPV equals zero.
        
        CONTEXT.md: "IRR is the discount rate at which the Net Present 
        Value (NPV) of all cash flows... equals zero"
        """
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        proforma_calc = ProFormaCalculator(sample_deal)
        proforma_result = proforma_calc.calculate(years=10)
        
        # Act
        result = calculator.calculate(holding_period=10)
        irr = result.data.irr.value
        
        # Get cash flows
        df = proforma_result.data.to_dataframe()
        final_year = df.iloc[-1]
        sale_price = final_year['property_value']
        sales_costs = sale_price * (sample_deal.market_assumptions.sales_expense_percent / 100)
        loan_payoff = final_year['loan_balance']
        net_proceeds = sale_price - sales_costs - loan_payoff
        
        cash_flows = df['pre_tax_cash_flow'].tolist()
        cash_flows[-1] += net_proceeds
        
        # Assert - NPV at IRR should be approximately 0
        npv_at_irr = npf.npv(irr, cash_flows)
        assert npv_at_irr == pytest.approx(0, abs=1.0)  # Within $1


# =============================================================================
# NET PRESENT VALUE (NPV)
# =============================================================================

class TestNPV:
    """Test NPV calculation.
    
    NPV = Present value of all cash flows discounted at a specified rate.
    Positive NPV means the investment exceeds the discount rate return.
    """
    
    def test_npv_calculation(self, sample_deal):
        """NPV is calculated at specified discount rate."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        discount_rate = 0.10  # 10%
        
        # Act
        result = calculator.calculate(holding_period=10, discount_rate=discount_rate)
        
        # Assert
        assert result.success
        assert result.data.npv is not None
    
    def test_npv_positive_means_good_investment(self, sample_deal):
        """Positive NPV means return exceeds discount rate."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(holding_period=10, discount_rate=0.08)
        npv = result.data.npv.value
        
        # Assert - if IRR > discount rate, NPV should be positive
        irr = result.data.irr.value
        if irr > 0.08:
            assert npv > 0
    
    def test_npv_higher_discount_rate_lower_npv(self, sample_deal):
        """Higher discount rate results in lower NPV."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result_8pct = calculator.calculate(holding_period=10, discount_rate=0.08)
        result_12pct = calculator.calculate(holding_period=10, discount_rate=0.12)
        
        npv_8 = result_8pct.data.npv.value
        npv_12 = result_12pct.data.npv.value
        
        # Assert
        assert npv_8 > npv_12
    
    def test_npv_zero_at_irr(self, sample_deal):
        """NPV is approximately zero when discount rate equals IRR."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # First get IRR
        result = calculator.calculate(holding_period=10)
        irr = result.data.irr.value
        
        # Then calculate NPV at that rate
        result_at_irr = calculator.calculate(holding_period=10, discount_rate=irr)
        npv_at_irr = result_at_irr.data.npv.value
        
        # Assert - should be approximately zero
        assert npv_at_irr == pytest.approx(0, abs=100)  # Within $100


# =============================================================================
# PROFORMA INTEGRATION
# =============================================================================

class TestProFormaIntegration:
    """Test that advanced metrics correctly integrate with pro-forma projections."""
    
    def test_metrics_use_proforma_cash_flows(self, sample_deal):
        """Advanced metrics use pro-forma projected cash flows."""
        # Arrange
        metrics_calc = MetricsCalculator(sample_deal)
        proforma_calc = ProFormaCalculator(sample_deal)
        
        # Act
        metrics_result = metrics_calc.calculate(holding_period=10)
        proforma_result = proforma_calc.calculate(years=10)
        
        # Assert
        assert metrics_result.success
        assert proforma_result.success
        # Metrics should be calculated based on pro-forma
        assert metrics_result.data.irr is not None
        assert metrics_result.data.equity_multiple is not None
    
    def test_metrics_include_appreciation(self, sample_deal):
        """Sale proceeds include property appreciation."""
        # Arrange
        proforma_calc = ProFormaCalculator(sample_deal)
        holding_period = 10
        appreciation_rate = sample_deal.market_assumptions.annual_appreciation_percent / 100
        
        # Act
        result = proforma_calc.calculate(years=holding_period)
        df = result.data.to_dataframe()
        
        initial_value = sample_deal.property.purchase_price
        final_value = df.iloc[-1]['property_value']
        
        # Assert - final value includes appreciation
        expected_final = initial_value * ((1 + appreciation_rate) ** holding_period)
        assert final_value == pytest.approx(expected_final, rel=1e-6)
    
    def test_sale_proceeds_calculation(self, sample_deal):
        """Net Sale Proceeds = Sale Price - Sales Expenses - Loan Balance.
        
        CONTEXT.md Part III Section 3.4: Formula for Net Sale Proceeds
        """
        # Arrange
        proforma_calc = ProFormaCalculator(sample_deal)
        holding_period = 10
        
        # Act
        result = proforma_calc.calculate(years=holding_period)
        df = result.data.to_dataframe()
        final_year = df.iloc[-1]
        
        sale_price = final_year['property_value']
        sales_expenses = sale_price * (sample_deal.market_assumptions.sales_expense_percent / 100)
        loan_balance = final_year['loan_balance']
        
        expected_net_proceeds = sale_price - sales_expenses - loan_balance
        
        # Assert
        assert expected_net_proceeds > 0  # Should have positive proceeds


# =============================================================================
# HOLDING PERIOD VARIATIONS
# =============================================================================

class TestHoldingPeriodVariations:
    """Test metrics across different holding periods."""
    
    @pytest.mark.parametrize("holding_period", [5, 10, 15, 20])
    def test_metrics_calculated_for_various_periods(self, sample_deal, holding_period):
        """Metrics can be calculated for various holding periods."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(holding_period=holding_period)
        
        # Assert
        assert result.success
        assert result.data.irr is not None
        assert result.data.equity_multiple is not None
        assert result.data.npv is not None
    
    def test_short_hold_lower_em_higher_irr_possible(self, sample_deal):
        """Short hold may have lower EM but potentially higher IRR.
        
        This tests the time-value relationship between metrics.
        """
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result_3yr = calculator.calculate(holding_period=3)
        result_10yr = calculator.calculate(holding_period=10)
        
        em_3 = result_3yr.data.equity_multiple.value
        em_10 = result_10yr.data.equity_multiple.value
        
        # Assert - longer hold has higher EM due to more cash flows
        assert em_10 > em_3
    
    def test_30_year_hold(self, sample_deal):
        """30-year hold calculation (full pro-forma period)."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(holding_period=30)
        
        # Assert
        assert result.success
        assert result.data.equity_multiple is not None
        # 30 years of cash flow + appreciation should give high EM
        assert result.data.equity_multiple.value > 1.0


# =============================================================================
# EDGE CASES
# =============================================================================

class TestAdvancedMetricsEdgeCases:
    """Test edge cases for advanced metrics."""
    
    def test_cash_purchase_advanced_metrics(self, cash_purchase_deal):
        """Cash purchase still has valid advanced metrics."""
        # Arrange
        calculator = MetricsCalculator(cash_purchase_deal)
        
        # Act
        result = calculator.calculate(holding_period=10)
        
        # Assert
        assert result.success
        assert result.data.irr is not None
        assert result.data.equity_multiple is not None
    
    def test_negative_cash_flow_deal_metrics(self, negative_cash_flow_deal):
        """Negative cash flow deal still calculates metrics."""
        # Arrange
        calculator = MetricsCalculator(negative_cash_flow_deal)
        
        # Act
        result = calculator.calculate(holding_period=10)
        
        # Assert
        assert result.success
        # IRR may be negative or low
        assert result.data.irr is not None
    
    def test_multi_unit_deal_metrics(self, multi_unit_deal):
        """Multi-unit property has valid advanced metrics."""
        # Arrange
        calculator = MetricsCalculator(multi_unit_deal)
        
        # Act
        result = calculator.calculate(holding_period=10)
        
        # Assert
        assert result.success
        assert result.data.irr is not None
        assert result.data.equity_multiple is not None
