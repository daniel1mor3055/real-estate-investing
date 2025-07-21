"""
Pytest unit tests for financing calculations.
Run with: venv/bin/python3 -m pytest tests/test_financing.py -v
"""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.models.financing import Financing, FinancingType
import numpy_financial as npf


class TestFinancingCalculations:
    """Test class for financing calculations."""

    def test_standard_30_year_loan(self):
        """Test standard 30-year conventional loan calculation."""
        # Arrange
        financing = Financing(
            financing_type=FinancingType.CONVENTIONAL,
            is_cash_purchase=False,
            down_payment_percent=20.0,
            interest_rate=7.0,
            loan_term_years=30,
        )
        purchase_price = 300000

        # Act
        financing.calculate_loan_details(purchase_price)

        # Assert
        expected_down_payment = purchase_price * 0.20
        expected_loan_amount = purchase_price - expected_down_payment
        monthly_rate = 7.0 / 100 / 12
        num_payments = 30 * 12
        expected_payment = float(
            npf.pmt(monthly_rate, num_payments, -expected_loan_amount)
        )

        assert financing.down_payment_amount == expected_down_payment
        assert financing.loan_amount == expected_loan_amount
        assert abs(financing.monthly_payment - expected_payment) < 0.01

        # Additional assertions for specific values
        assert financing.down_payment_amount == 60000.0
        assert financing.loan_amount == 240000.0
        assert (
            abs(financing.monthly_payment - 1596.22) < 1.0
        )  # Approximate expected payment

    def test_15_year_loan_different_parameters(self):
        """Test 15-year loan with different down payment and interest rate."""
        # Arrange
        financing = Financing(
            financing_type=FinancingType.CONVENTIONAL,
            is_cash_purchase=False,
            down_payment_percent=25.0,
            interest_rate=6.5,
            loan_term_years=15,
        )
        purchase_price = 500000

        # Act
        financing.calculate_loan_details(purchase_price)

        # Assert
        expected_down_payment = purchase_price * 0.25
        expected_loan_amount = purchase_price - expected_down_payment
        monthly_rate = 6.5 / 100 / 12
        num_payments = 15 * 12
        expected_payment = float(
            npf.pmt(monthly_rate, num_payments, -expected_loan_amount)
        )

        assert financing.down_payment_amount == expected_down_payment
        assert financing.loan_amount == expected_loan_amount
        assert abs(financing.monthly_payment - expected_payment) < 0.01

        # Additional assertions for specific values
        assert financing.down_payment_amount == 125000.0
        assert financing.loan_amount == 375000.0
        assert (
            abs(financing.monthly_payment - 3267.0) < 1.0
        )  # Approximate expected payment

    def test_cash_purchase(self):
        """Test cash purchase scenario."""
        # Arrange
        financing = Financing(financing_type=FinancingType.CASH, is_cash_purchase=True)
        purchase_price = 400000

        # Act
        financing.calculate_loan_details(purchase_price)

        # Assert
        assert financing.down_payment_amount == purchase_price
        assert financing.loan_amount == 0
        assert financing.monthly_payment == 0

    def test_zero_interest_loan(self):
        """Test edge case with 0% interest rate."""
        # Arrange
        financing = Financing(
            financing_type=FinancingType.PRIVATE_MONEY,
            is_cash_purchase=False,
            down_payment_percent=10.0,
            interest_rate=0.00001,
            loan_term_years=10,
        )
        purchase_price = 200000

        # Act
        financing.calculate_loan_details(purchase_price)

        # Assert
        expected_down_payment = purchase_price * 0.10
        expected_loan_amount = purchase_price - expected_down_payment
        expected_payment = expected_loan_amount / (
            10 * 12
        )  # Simple division for 0% interest

        assert financing.down_payment_amount == expected_down_payment
        assert financing.loan_amount == expected_loan_amount
        assert abs(financing.monthly_payment - expected_payment) < 0.01

        # Additional assertions for specific values
        assert financing.down_payment_amount == 20000.0
        assert financing.loan_amount == 180000.0
        assert abs(financing.monthly_payment - 1500.0) < 0.01

    def test_high_down_payment_scenario(self):
        """Test scenario with high down payment percentage."""
        # Arrange
        financing = Financing(
            financing_type=FinancingType.CONVENTIONAL,
            is_cash_purchase=False,
            down_payment_percent=50.0,
            interest_rate=5.5,
            loan_term_years=20,
        )
        purchase_price = 600000

        # Act
        financing.calculate_loan_details(purchase_price)

        # Assert
        expected_down_payment = purchase_price * 0.50
        expected_loan_amount = purchase_price - expected_down_payment
        monthly_rate = 5.5 / 100 / 12
        num_payments = 20 * 12
        expected_payment = float(
            npf.pmt(monthly_rate, num_payments, -expected_loan_amount)
        )

        assert financing.down_payment_amount == expected_down_payment
        assert financing.loan_amount == expected_loan_amount
        assert abs(financing.monthly_payment - expected_payment) < 0.01

        # Additional assertions for specific values
        assert financing.down_payment_amount == 300000.0
        assert financing.loan_amount == 300000.0

    def test_loan_properties(self):
        """Test calculated properties of the financing object."""
        # Arrange
        financing = Financing(
            financing_type=FinancingType.CONVENTIONAL,
            is_cash_purchase=False,
            down_payment_percent=20.0,
            interest_rate=7.0,
            loan_term_years=30,
        )
        purchase_price = 300000

        # Act
        financing.calculate_loan_details(purchase_price)

        # Assert properties
        assert financing.annual_debt_service == financing.monthly_payment * 12
        assert financing.loan_to_value_ratio == 80.0  # 100 - 20% down payment
        assert financing.total_interest_paid > 0

    @pytest.mark.parametrize(
        "purchase_price,down_percent,rate,term",
        [
            (250000, 20, 6.0, 30),
            (400000, 25, 7.5, 15),
            (750000, 30, 5.0, 20),
        ],
    )
    def test_parametrized_loan_calculations(
        self, purchase_price, down_percent, rate, term
    ):
        """Test multiple loan scenarios using parametrized testing."""
        # Arrange
        financing = Financing(
            financing_type=FinancingType.CONVENTIONAL,
            is_cash_purchase=False,
            down_payment_percent=down_percent,
            interest_rate=rate,
            loan_term_years=term,
        )

        # Act
        financing.calculate_loan_details(purchase_price)

        # Assert basic calculations are correct
        expected_down_payment = purchase_price * (down_percent / 100)
        expected_loan_amount = purchase_price - expected_down_payment

        assert financing.down_payment_amount == expected_down_payment
        assert financing.loan_amount == expected_loan_amount
        assert financing.monthly_payment > 0
        assert financing.loan_to_value_ratio == (100 - down_percent)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
