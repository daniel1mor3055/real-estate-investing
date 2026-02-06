"""
Pytest unit tests for Israeli mortgage financing calculations.
Run with: venv/bin/python3 -m pytest tests/test_financing.py -v
"""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.core.models.financing import Financing, FinancingType, SubLoan, IsraeliMortgageTrack
import numpy_financial as npf


class TestIsraeliMortgageTracks:
    """Test class for Israeli mortgage track functionality."""

    def test_fixed_unlinked_track(self):
        """Test Fixed Unlinked (קל"צ) track - most stable option."""
        # Arrange
        track = SubLoan(
            name="Fixed Unlinked Track",
            track_type=IsraeliMortgageTrack.FIXED_UNLINKED,
            loan_amount=500000,
            base_interest_rate=5.5,
            loan_term_years=25,
        )

        # Act
        effective_rate = track.calculate_effective_rate()
        monthly_payment = track.calculate_payment()

        # Assert
        assert effective_rate == 5.5  # Uses base rate as-is
        assert track.effective_interest_rate == 5.5
        assert not track.track_type.is_cpi_linked
        assert track.track_type.is_fixed_rate

        # Verify payment calculation
        monthly_rate = 5.5 / 100 / 12
        num_payments = 25 * 12
        expected_payment = float(npf.pmt(monthly_rate, num_payments, -500000))
        assert abs(monthly_payment - expected_payment) < 0.01

    def test_prime_rate_track(self):
        """Test Prime Rate Track (מסלול פריים) - variable based on BoI rate."""
        # Arrange
        track = SubLoan(
            name="Prime Rate Track",
            track_type=IsraeliMortgageTrack.PRIME_RATE,
            loan_amount=1000000,
            base_interest_rate=4.0,  # This gets overridden
            loan_term_years=30,
            bank_of_israel_rate=3.25,  # BoI official rate
        )

        # Act
        effective_rate = track.calculate_effective_rate()
        monthly_payment = track.calculate_payment()

        # Assert
        assert effective_rate == 4.75  # 3.25% + 1.5% margin
        assert track.effective_interest_rate == 4.75
        assert not track.track_type.is_cpi_linked
        assert not track.track_type.is_fixed_rate
        assert track.track_type.is_prime_based

        # Verify payment calculation with prime rate
        monthly_rate = 4.75 / 100 / 12
        num_payments = 30 * 12
        expected_payment = float(npf.pmt(monthly_rate, num_payments, -1000000))
        assert abs(monthly_payment - expected_payment) < 0.01

    def test_fixed_rate_linked_track(self):
        """Test Fixed-Rate Linked (ריבית קבועה צמודה) - fixed rate but CPI-linked principal."""
        # Arrange
        track = SubLoan(
            name="Fixed-Rate Linked Track",
            track_type=IsraeliMortgageTrack.FIXED_RATE_LINKED,
            loan_amount=800000,
            base_interest_rate=3.8,  # Lower than Fixed Unlinked
            loan_term_years=30,
            expected_cpi=2.5,
        )

        # Act
        effective_rate = track.calculate_effective_rate()

        # Test with no CPI adjustment (year 0)
        monthly_payment_year0 = track.calculate_payment(years_elapsed=0)

        # Test with CPI adjustment after 5 years
        monthly_payment_year5 = track.calculate_payment(years_elapsed=5)

        # Assert
        assert effective_rate == 3.8  # Fixed rate doesn't change
        assert track.track_type.is_cpi_linked
        assert track.track_type.is_fixed_rate

        # Principal should be adjusted for CPI
        expected_principal_year5 = 800000 * (1.025**5)  # 2.5% annual CPI
        assert abs(track.cpi_adjusted_principal - expected_principal_year5) < 1

        # Payment in year 5 should be higher due to CPI adjustment
        assert monthly_payment_year5 > monthly_payment_year0

    def test_track_hebrew_names(self):
        """Test Hebrew names for tracks."""
        # Arrange & Act & Assert
        assert (
            IsraeliMortgageTrack.FIXED_UNLINKED.hebrew_name
            == 'ריבית קבועה לא צמודה (קל"צ)'
        )
        assert IsraeliMortgageTrack.PRIME_RATE.hebrew_name == "מסלול פריים"
        assert IsraeliMortgageTrack.FIXED_RATE_LINKED.hebrew_name == "ריבית קבועה צמודה"

    def test_track_validation_errors(self):
        """Test validation errors for Israeli mortgage tracks."""

        # Prime track without BoI rate should fail
        with pytest.raises(
            ValueError, match="Prime rate track must specify bank_of_israel_rate"
        ):
            SubLoan(
                name="Bad Prime",
                track_type=IsraeliMortgageTrack.PRIME_RATE,
                loan_amount=100000,
                base_interest_rate=4.0,
                loan_term_years=30,
            )

        # CPI-linked track without expected CPI should fail
        with pytest.raises(
            ValueError, match="CPI-linked tracks must specify expected_cpi"
        ):
            SubLoan(
                name="Bad CPI-Linked",
                track_type=IsraeliMortgageTrack.FIXED_RATE_LINKED,
                loan_amount=100000,
                base_interest_rate=4.0,
                loan_term_years=30,
            )

        # Non-prime track with BoI rate should fail
        with pytest.raises(
            ValueError, match="Non-prime tracks should not specify bank_of_israel_rate"
        ):
            SubLoan(
                name="Bad Fixed",
                track_type=IsraeliMortgageTrack.FIXED_UNLINKED,
                loan_amount=100000,
                base_interest_rate=4.0,
                loan_term_years=30,
                bank_of_israel_rate=3.0,
            )

        # Non-CPI-linked track with CPI should fail
        with pytest.raises(
            ValueError, match="Non-CPI-linked tracks should not specify expected_cpi"
        ):
            SubLoan(
                name="Bad Unlinked",
                track_type=IsraeliMortgageTrack.FIXED_UNLINKED,
                loan_amount=100000,
                base_interest_rate=4.0,
                loan_term_years=30,
                expected_cpi=2.0,
            )


class TestIsraeliMortgageRegulations:
    """Test class for Israeli Bank regulations compliance."""

    def test_compliant_mortgage_composition(self):
        """Test a mortgage that complies with Israeli regulations."""
        # Arrange - 40% Fixed Unlinked, 60% Prime (compliant)
        track1 = SubLoan(
            name="Fixed Unlinked 40%",
            track_type=IsraeliMortgageTrack.FIXED_UNLINKED,
            loan_amount=1200000,  # 40% of 3M
            base_interest_rate=5.5,
            loan_term_years=30,
        )

        track2 = SubLoan(
            name="Prime 60%",
            track_type=IsraeliMortgageTrack.PRIME_RATE,
            loan_amount=1800000,  # 60% of 3M
            base_interest_rate=4.0,
            loan_term_years=30,
            bank_of_israel_rate=3.25,
        )

        # Act & Assert - Should not raise validation error
        financing = Financing.create_israeli_mortgage(
            financing_type=FinancingType.CONVENTIONAL,
            down_payment_percent=0,
            mortgage_tracks=[track1, track2],
        )

        # Verify regulatory compliance
        summary = financing.get_israeli_mortgage_summary()
        compliance = summary["regulatory_compliance"]
        assert compliance["status"] == "Compliant"
        assert compliance["fixed_rate_ratio"] >= 1 / 3
        assert compliance["prime_rate_ratio"] <= 2 / 3

    def test_insufficient_fixed_rate_violation(self):
        """Test violation of minimum 1/3 fixed-rate requirement."""
        # Arrange - Only 20% fixed rate (violation)
        track1 = SubLoan(
            name="Fixed Only 20%",
            track_type=IsraeliMortgageTrack.FIXED_UNLINKED,
            loan_amount=600000,  # 20% of 3M
            base_interest_rate=5.5,
            loan_term_years=30,
        )

        track2 = SubLoan(
            name="Prime 80%",
            track_type=IsraeliMortgageTrack.PRIME_RATE,
            loan_amount=2400000,  # 80% of 3M
            base_interest_rate=4.0,
            loan_term_years=30,
            bank_of_israel_rate=3.25,
        )

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Israeli regulation requires at least 1/3 of mortgage to be fixed-rate",
        ):
            Financing.create_israeli_mortgage(
                financing_type=FinancingType.CONVENTIONAL,
                down_payment_percent=0,
                mortgage_tracks=[track1, track2],
            )

    def test_excessive_prime_rate_violation(self):
        """Test violation of maximum 2/3 prime rate limit."""
        # Arrange - 75% prime rate (violation)
        track1 = SubLoan(
            name="Fixed 25%",
            track_type=IsraeliMortgageTrack.FIXED_UNLINKED,
            loan_amount=750000,  # 25% of 3M
            base_interest_rate=5.5,
            loan_term_years=30,
        )

        track2 = SubLoan(
            name="Prime 75%",
            track_type=IsraeliMortgageTrack.PRIME_RATE,
            loan_amount=2250000,  # 75% of 3M (exceeds 2/3 limit)
            base_interest_rate=4.0,
            loan_term_years=30,
            bank_of_israel_rate=3.25,
        )

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Israeli regulation limits prime rate track to maximum 2/3",
        ):
            Financing.create_israeli_mortgage(
                financing_type=FinancingType.CONVENTIONAL,
                down_payment_percent=0,
                mortgage_tracks=[track1, track2],
            )

    def test_three_track_compliant_mortgage(self):
        """Test a compliant 3-track Israeli mortgage."""
        # Arrange - Mix that satisfies regulations
        track1 = SubLoan(
            name="Fixed Unlinked",
            track_type=IsraeliMortgageTrack.FIXED_UNLINKED,
            loan_amount=1000000,  # 33.3%
            base_interest_rate=5.5,
            loan_term_years=25,
        )

        track2 = SubLoan(
            name="Fixed-Rate Linked",
            track_type=IsraeliMortgageTrack.FIXED_RATE_LINKED,
            loan_amount=1000000,  # 33.3%
            base_interest_rate=3.8,
            loan_term_years=30,
            expected_cpi=2.5,
        )

        track3 = SubLoan(
            name="Prime Rate",
            track_type=IsraeliMortgageTrack.PRIME_RATE,
            loan_amount=1000000,  # 33.3%
            base_interest_rate=4.0,
            loan_term_years=30,
            bank_of_israel_rate=3.25,
        )

        # Act
        financing = Financing.create_israeli_mortgage(
            financing_type=FinancingType.CONVENTIONAL,
            down_payment_percent=0,
            mortgage_tracks=[track1, track2, track3],
        )

        financing.calculate_loan_details(3000000)

        # Assert
        assert financing.loan_amount == 3000000

        # Check regulatory compliance
        summary = financing.get_israeli_mortgage_summary()
        compliance = summary["regulatory_compliance"]
        assert compliance["status"] == "Compliant"

        # 66.6% fixed rate (tracks 1 & 2), 33.3% prime
        assert compliance["fixed_rate_ratio"] >= 1 / 3
        assert compliance["prime_rate_ratio"] <= 2 / 3


class TestFinancingLegacyCompatibility:
    """Test class for backward compatibility with legacy financing."""

    def test_legacy_single_loan_still_works(self):
        """Test that legacy single-loan creation still works."""
        # Arrange & Act
        financing = Financing.create_simple_loan(
            financing_type=FinancingType.CONVENTIONAL,
            down_payment_percent=20.0,
            interest_rate=7.0,
            loan_term_years=30,
        )

        financing.calculate_loan_details(300000)

        # Assert
        assert financing.financing_type == FinancingType.CONVENTIONAL
        assert financing.down_payment_percent == 20.0
        assert financing.interest_rate == 7.0
        assert financing.loan_term_years == 30
        assert len(financing.sub_loans) == 0
        assert financing.loan_amount == 240000
        assert financing.monthly_payment > 0

    def test_cash_purchase_compatibility(self):
        """Test cash purchase still works."""
        # Arrange
        financing = Financing.create_simple_loan(
            financing_type=FinancingType.CASH,
            down_payment_percent=100.0,
            interest_rate=0.0,
            loan_term_years=30,
            is_cash_purchase=True,
        )

        # Act
        financing.calculate_loan_details(500000)

        # Assert
        assert financing.loan_amount == 0
        assert financing.down_payment_amount == 500000
        assert financing.monthly_payment == 0


class TestIsraeliMortgageReporting:
    """Test class for Israeli mortgage reporting and summary functionality."""

    def test_israeli_mortgage_summary_detailed(self):
        """Test detailed Israeli mortgage summary with all track types."""
        # Arrange
        track1 = SubLoan(
            name="Fixed Unlinked Track",
            track_type=IsraeliMortgageTrack.FIXED_UNLINKED,
            loan_amount=1000000,
            base_interest_rate=5.5,
            loan_term_years=25,
        )

        track2 = SubLoan(
            name="Prime Track",
            track_type=IsraeliMortgageTrack.PRIME_RATE,
            loan_amount=1500000,
            base_interest_rate=4.0,
            loan_term_years=30,
            bank_of_israel_rate=3.25,
        )

        track3 = SubLoan(
            name="CPI-Linked Track",
            track_type=IsraeliMortgageTrack.FIXED_RATE_LINKED,
            loan_amount=500000,
            base_interest_rate=3.8,
            loan_term_years=30,
            expected_cpi=2.5,
        )

        financing = Financing.create_israeli_mortgage(
            financing_type=FinancingType.CONVENTIONAL,
            down_payment_percent=0,
            mortgage_tracks=[track1, track2, track3],
        )

        financing.calculate_loan_details(3000000)

        # Act
        summary = financing.get_israeli_mortgage_summary()

        # Assert
        assert summary["type"] == "israeli_mortgage"
        assert summary["total_amount"] == 3000000
        assert len(summary["tracks"]) == 3

        # Check track details
        track_summary = summary["tracks"][0]  # Fixed Unlinked
        assert track_summary["name"] == "Fixed Unlinked Track"
        assert track_summary["track_type"] == "fixed_unlinked"
        assert track_summary["hebrew_name"] == 'ריבית קבועה לא צמודה (קל"צ)'
        assert track_summary["amount"] == 1000000
        assert track_summary["percentage"] == pytest.approx(33.33, abs=0.1)
        assert track_summary["base_rate"] == 5.5
        assert track_summary["effective_rate"] == 5.5
        assert not track_summary["is_cpi_linked"]

        # Check regulatory compliance
        compliance = summary["regulatory_compliance"]
        assert compliance["status"] == "Compliant"
        assert compliance["fixed_rate_ratio"] >= 1 / 3  # 50% fixed (tracks 1 & 3)
        assert compliance["prime_rate_ratio"] <= 2 / 3  # 50% prime (track 2)

    def test_cpi_adjustment_over_time(self):
        """Test CPI adjustment calculations over time."""
        # Arrange
        track = SubLoan(
            name="CPI Test Track",
            track_type=IsraeliMortgageTrack.FIXED_RATE_LINKED,
            loan_amount=1000000,
            base_interest_rate=3.5,
            loan_term_years=30,
            expected_cpi=3.0,  # 3% annual CPI
        )

        # Act & Assert
        # Year 0 - no adjustment
        principal_year0 = track.calculate_cpi_adjusted_principal(0)
        assert principal_year0 == 1000000

        # Year 5 - 3% annual CPI
        principal_year5 = track.calculate_cpi_adjusted_principal(5)
        expected_year5 = 1000000 * (1.03**5)
        assert abs(principal_year5 - expected_year5) < 1

        # Year 10 - compound effect
        principal_year10 = track.calculate_cpi_adjusted_principal(10)
        expected_year10 = 1000000 * (1.03**10)
        assert abs(principal_year10 - expected_year10) < 1

        # Payments should increase with CPI
        payment_year0 = track.calculate_payment(0)
        payment_year5 = track.calculate_payment(5)
        payment_year10 = track.calculate_payment(10)

        assert payment_year5 > payment_year0
        assert payment_year10 > payment_year5


@pytest.mark.parametrize(
    "track_type,has_boi_rate,has_cpi",
    [
        (IsraeliMortgageTrack.FIXED_UNLINKED, False, False),
        (IsraeliMortgageTrack.PRIME_RATE, True, False),
        (IsraeliMortgageTrack.FIXED_RATE_LINKED, False, True),
    ],
)
def test_all_israeli_track_types(track_type, has_boi_rate, has_cpi):
    """Parametrized test for all Israeli mortgage track types."""
    # Arrange
    kwargs = {
        "name": f"Test {track_type.value}",
        "track_type": track_type,
        "loan_amount": 1000000,
        "base_interest_rate": 4.0,
        "loan_term_years": 30,
    }

    if has_boi_rate:
        kwargs["bank_of_israel_rate"] = 3.25
    if has_cpi:
        kwargs["expected_cpi"] = 2.5

    # Act
    track = SubLoan(**kwargs)
    effective_rate = track.calculate_effective_rate()
    monthly_payment = track.calculate_payment()

    # Assert
    assert effective_rate > 0
    assert monthly_payment > 0
    assert track.monthly_payment == monthly_payment
    assert track.track_type.hebrew_name is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
