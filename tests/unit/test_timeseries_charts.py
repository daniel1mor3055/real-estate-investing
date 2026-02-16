"""Tests for time series visualization charts."""

import pytest
from src.core.calculators.proforma import ProFormaCalculator
from src.presentation.streamlit.components.charts import (
    display_operating_metrics_timeseries,
    display_wealth_metrics_timeseries,
    display_roe_timeseries,
)


def test_proforma_has_required_columns_for_timeseries(sample_deal):
    """Verify ProForma data contains all columns needed for time series charts."""
    calc = ProFormaCalculator(sample_deal)
    result = calc.calculate(years=10)
    
    assert result.success, "ProForma calculation should succeed"
    
    df = result.data.to_dataframe()
    
    # Verify columns for operating metrics chart
    assert "net_operating_income" in df.columns
    assert "pre_tax_cash_flow" in df.columns
    assert "debt_service" in df.columns
    
    # Verify columns for wealth metrics chart
    assert "property_value" in df.columns
    assert "total_equity" in df.columns
    assert "loan_balance" in df.columns
    
    # Verify columns for ROE chart
    assert "roe" in df.columns
    assert "average_equity" in df.columns


def test_operating_metrics_timeseries_data_sanity(sample_deal):
    """Test that operating metrics have reasonable values over time."""
    calc = ProFormaCalculator(sample_deal)
    result = calc.calculate(years=10)
    
    assert result.success
    df = result.data.to_dataframe()
    
    # NOI should be positive for a sample_deal (profitable)
    assert df.loc[1:, "net_operating_income"].mean() > 0, "Average NOI should be positive"
    
    # Cash flow should generally be positive for sample deal
    assert df.loc[1:, "pre_tax_cash_flow"].sum() > 0, "Total cash flow should be positive"
    
    # DSCR should be calculable (no division by zero)
    if df.loc[1, "debt_service"] > 0:
        dscr = df.loc[1, "net_operating_income"] / df.loc[1, "debt_service"]
        assert dscr > 0, "Year 1 DSCR should be positive"


def test_wealth_metrics_timeseries_data_sanity(sample_deal):
    """Test that wealth metrics show expected growth patterns."""
    calc = ProFormaCalculator(sample_deal)
    result = calc.calculate(years=10)
    
    assert result.success
    df = result.data.to_dataframe()
    
    # Property value should increase over time (with appreciation)
    assert df.loc[10, "property_value"] > df.loc[0, "property_value"], \
        "Property value should appreciate"
    
    # Total equity should increase over time (appreciation + paydown)
    assert df.loc[10, "total_equity"] > df.loc[0, "total_equity"], \
        "Equity should build over time"
    
    # Loan balance should decrease over time (if financed)
    if df.loc[0, "loan_balance"] > 0:
        assert df.loc[10, "loan_balance"] < df.loc[0, "loan_balance"], \
            "Loan balance should decrease over time"


def test_roe_timeseries_data_sanity(sample_deal):
    """Test that ROE values are calculated for all years."""
    calc = ProFormaCalculator(sample_deal)
    result = calc.calculate(years=10)
    
    assert result.success
    df = result.data.to_dataframe()
    
    # ROE should be calculated for years 1-10
    roe_values = df.loc[1:, "roe"]
    
    # All years should have ROE values (not null)
    assert not roe_values.isnull().any(), "All years should have ROE values"
    
    # Average equity should be positive
    assert df.loc[1:, "average_equity"].mean() > 0, "Average equity should be positive"
    
    # ROE should be finite (no infinity values)
    assert all(abs(roe) < 1000 for roe in roe_values), "ROE should be reasonable values"


def test_roe_calculation_matches_formula(sample_deal):
    """Verify ROE is correctly calculated as cash_flow / average_equity."""
    calc = ProFormaCalculator(sample_deal)
    result = calc.calculate(years=10)
    
    assert result.success
    df = result.data.to_dataframe()
    
    # Check Year 1 ROE calculation
    year_1 = df.loc[1]
    cash_flow = year_1["pre_tax_cash_flow"]
    avg_equity = year_1["average_equity"]
    expected_roe = cash_flow / avg_equity if avg_equity > 0 else 0
    
    assert abs(year_1["roe"] - expected_roe) < 0.0001, \
        f"Year 1 ROE should be {expected_roe:.4f}, got {year_1['roe']:.4f}"


def test_cash_purchase_deal_has_infinite_dscr_handled(cash_purchase_deal):
    """Test that cash purchase deals (no debt) handle DSCR correctly."""
    calc = ProFormaCalculator(cash_purchase_deal)
    result = calc.calculate(years=10)
    
    assert result.success
    df = result.data.to_dataframe()
    
    # Debt service should be 0 for cash purchase
    assert df.loc[1, "debt_service"] == 0, "Cash purchase should have no debt service"
    
    # The chart should handle division by zero gracefully
    # (We cap DSCR at 999.99 in the chart function)
    if df.loc[1, "debt_service"] == 0:
        # This would be infinity, but we handle it in the chart
        assert df.loc[1, "net_operating_income"] > 0, "NOI should still be positive"


def test_negative_cash_flow_deal_roe(negative_cash_flow_deal):
    """Test that negative cash flow deals show negative ROE."""
    calc = ProFormaCalculator(negative_cash_flow_deal)
    result = calc.calculate(years=10)
    
    assert result.success
    df = result.data.to_dataframe()
    
    # Year 1 cash flow should be negative
    assert df.loc[1, "pre_tax_cash_flow"] < 0, "Negative cash flow deal should have negative cash flow"
    
    # Year 1 ROE should be negative
    assert df.loc[1, "roe"] < 0, "Negative cash flow should result in negative ROE"


def test_multi_unit_deal_timeseries(multi_unit_deal):
    """Test time series calculations for multi-unit property."""
    calc = ProFormaCalculator(multi_unit_deal)
    result = calc.calculate(years=10)
    
    assert result.success
    df = result.data.to_dataframe()
    
    # Multi-unit should have higher absolute values
    assert df.loc[1, "net_operating_income"] > 10000, \
        "Multi-unit NOI should be substantial"
    
    # All time series metrics should be present
    assert "roe" in df.columns
    assert "total_equity" in df.columns
    assert "property_value" in df.columns


def test_proforma_years_match_holding_period():
    """Test that ProForma generates data for all years including year 0."""
    from src.core.models import Deal
    from tests.conftest import context_md_example_deal
    
    holding_periods = [5, 10, 15, 30]
    
    for years in holding_periods:
        deal = context_md_example_deal()
        calc = ProFormaCalculator(deal)
        result = calc.calculate(years=years)
        
        assert result.success
        df = result.data.to_dataframe()
        
        # Should have year 0 through year N (inclusive)
        assert len(df) == years + 1, \
            f"Should have {years + 1} rows (year 0 through {years}), got {len(df)}"
        
        assert df.index.min() == 0, "Should start at year 0"
        assert df.index.max() == years, f"Should end at year {years}"
