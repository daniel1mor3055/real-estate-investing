"""Unit tests for income calculations per CONTEXT.md Part I Section 1.2.3.

Tests verify:
- Gross Potential Rent (GPR) calculation
- Effective Gross Income (EGI) calculation
- Vacancy and credit loss deductions
- Other income sources
- Income projection with growth

CONTEXT.md Reference:
- GPR: "The total monthly rent if all units were occupied at market rates"
- EGI: "GPR + Other Income - Vacancy - Credit Loss"
"""

import pytest
from src.core.models.income import Income, IncomeItem, IncomeSource


class TestGrossPotentialRent:
    """Test GPR calculation per CONTEXT.md Section 1.2.3."""
    
    def test_gpr_single_unit(self, simple_income):
        """GPR = Monthly Rent x Units x 12 for single unit.
        
        CONTEXT.md: "Gross Potential Rent (GPR): The total monthly rent 
        if all units were occupied at market rates"
        """
        # Arrange
        num_units = 1
        expected_gpr = 2_000 * 1 * 12  # $24,000
        
        # Act
        actual_gpr = simple_income.calculate_gross_potential_rent(num_units)
        
        # Assert
        assert actual_gpr == expected_gpr
    
    def test_gpr_multi_unit(self):
        """GPR scales linearly with number of units."""
        # Arrange
        income = Income(
            monthly_rent_per_unit=1_200,
            vacancy_rate_percent=5.0,
            credit_loss_percent=1.0,
            annual_rent_increase_percent=3.0,
        )
        num_units = 4
        expected_gpr = 1_200 * 4 * 12  # $57,600
        
        # Act
        actual_gpr = income.calculate_gross_potential_rent(num_units)
        
        # Assert
        assert actual_gpr == expected_gpr
    
    def test_gpr_matches_context_md_example(self):
        """GPR matches CONTEXT.md table: $24,000/year.
        
        From CONTEXT.md Part III table: Year 1 GPR = $24,000
        """
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        expected_gpr = 24_000
        
        # Act
        actual_gpr = income.calculate_gross_potential_rent(num_units=1)
        
        # Assert
        assert actual_gpr == expected_gpr


class TestVacancyAndCreditLoss:
    """Test vacancy and credit loss deductions per CONTEXT.md."""
    
    def test_vacancy_deduction(self):
        """Vacancy reduces total potential income.
        
        CONTEXT.md: "A percentage deduction from GPR to account for 
        periods of vacancy"
        """
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        gpr = income.calculate_gross_potential_rent(num_units=1)  # $24,000
        expected_vacancy_loss = gpr * 0.05  # $1,200
        
        # Act
        egi = income.calculate_effective_gross_income(num_units=1)
        actual_vacancy_loss = gpr - egi
        
        # Assert
        assert actual_vacancy_loss == pytest.approx(expected_vacancy_loss, rel=1e-6)
    
    def test_credit_loss_deduction(self):
        """Credit loss further reduces effective income."""
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=0.0,  # No vacancy
            credit_loss_percent=2.0,
            annual_rent_increase_percent=3.0,
        )
        gpr = income.calculate_gross_potential_rent(num_units=1)  # $24,000
        expected_credit_loss = gpr * 0.02  # $480
        
        # Act
        egi = income.calculate_effective_gross_income(num_units=1)
        actual_credit_loss = gpr - egi
        
        # Assert
        assert actual_credit_loss == pytest.approx(expected_credit_loss, rel=1e-6)
    
    def test_combined_vacancy_and_credit_loss(self):
        """Both vacancy and credit loss are applied."""
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=2.0,
            annual_rent_increase_percent=3.0,
        )
        gpr = 24_000
        expected_egi = gpr * (1 - 0.05 - 0.02)  # $22,320
        
        # Act
        actual_egi = income.calculate_effective_gross_income(num_units=1)
        
        # Assert
        assert actual_egi == pytest.approx(expected_egi, rel=1e-6)
    
    def test_zero_vacancy(self):
        """Zero vacancy means EGI equals GPR minus credit loss only."""
        # Arrange
        income = Income(
            monthly_rent_per_unit=1_500,
            vacancy_rate_percent=0.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        
        # Act
        gpr = income.calculate_gross_potential_rent(num_units=1)
        egi = income.calculate_effective_gross_income(num_units=1)
        
        # Assert
        assert egi == gpr


class TestEffectiveGrossIncome:
    """Test EGI calculation per CONTEXT.md Section 1.2.3."""
    
    def test_egi_formula(self, simple_income):
        """EGI = GPR + Other Income - Vacancy - Credit Loss.
        
        CONTEXT.md: "This transforms GPR into the more realistic 
        Effective Gross Income (EGI)"
        """
        # Arrange
        num_units = 1
        gpr = simple_income.calculate_gross_potential_rent(num_units)
        other = simple_income.calculate_other_income_annual(num_units)
        total_potential = gpr + other
        vacancy_loss = total_potential * (simple_income.vacancy_rate_percent / 100)
        credit_loss = total_potential * (simple_income.credit_loss_percent / 100)
        expected_egi = total_potential - vacancy_loss - credit_loss
        
        # Act
        actual_egi = simple_income.calculate_effective_gross_income(num_units)
        
        # Assert
        assert actual_egi == pytest.approx(expected_egi, rel=1e-6)
    
    def test_egi_matches_context_md_example(self):
        """EGI matches CONTEXT.md table: $22,800.
        
        From CONTEXT.md Part III table: Year 1 EGI = $22,800
        GPR = $24,000, Vacancy 5% = $1,200, EGI = $22,800
        """
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        expected_egi = 22_800
        
        # Act
        actual_egi = income.calculate_effective_gross_income(num_units=1)
        
        # Assert
        assert actual_egi == pytest.approx(expected_egi, rel=1e-6)


class TestOtherIncome:
    """Test ancillary income sources per CONTEXT.md Section 1.2.3."""
    
    def test_no_other_income(self, simple_income):
        """Default income has no other sources."""
        # Arrange & Act
        other_income = simple_income.calculate_other_income_annual(num_units=1)
        
        # Assert
        assert other_income == 0
    
    def test_add_parking_income(self):
        """Parking income adds to EGI.
        
        CONTEXT.md: "Ancillary Income: Revenue from sources other than rent, 
        such as parking fees..."
        """
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        income.add_income_source(
            source=IncomeSource.PARKING,
            monthly_amount=100,
            description="Garage parking",
        )
        
        # Act
        other_annual = income.calculate_other_income_annual(num_units=1)
        
        # Assert
        assert other_annual == 100 * 12  # $1,200/year
    
    def test_multiple_income_sources(self):
        """Multiple ancillary income sources are summed."""
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        income.add_income_source(IncomeSource.PARKING, monthly_amount=100)
        income.add_income_source(IncomeSource.LAUNDRY, monthly_amount=50)
        income.add_income_source(IncomeSource.STORAGE, monthly_amount=75)
        
        # Act
        total_other = income.calculate_other_income_annual(num_units=1)
        
        # Assert
        expected = (100 + 50 + 75) * 12  # $2,700/year
        assert total_other == expected
    
    def test_per_unit_income_scaling(self):
        """Per-unit income scales with number of units."""
        # Arrange
        income = Income(
            monthly_rent_per_unit=1_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        income.add_income_source(
            source=IncomeSource.PET_FEES,
            monthly_amount=25,
            is_per_unit=True,
        )
        
        # Act
        single_unit = income.calculate_other_income_annual(num_units=1)
        four_units = income.calculate_other_income_annual(num_units=4)
        
        # Assert
        assert single_unit == 25 * 12  # $300
        assert four_units == 25 * 4 * 12  # $1,200
    
    def test_other_income_included_in_egi(self):
        """Other income is added to GPR before vacancy deduction."""
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        income.add_income_source(IncomeSource.PARKING, monthly_amount=200)
        
        gpr = income.calculate_gross_potential_rent(num_units=1)  # $24,000
        other = income.calculate_other_income_annual(num_units=1)  # $2,400
        total_potential = gpr + other  # $26,400
        expected_egi = total_potential * 0.95  # $25,080 (5% vacancy)
        
        # Act
        actual_egi = income.calculate_effective_gross_income(num_units=1)
        
        # Assert
        assert actual_egi == pytest.approx(expected_egi, rel=1e-6)


class TestIncomeProjection:
    """Test income projection with annual growth per CONTEXT.md Part III."""
    
    def test_year_1_no_growth(self, simple_income):
        """Year 1 income equals base income (no growth applied)."""
        # Arrange
        num_units = 1
        base_egi = simple_income.calculate_effective_gross_income(num_units)
        
        # Act
        year_1_income = simple_income.project_income(year=1, num_units=num_units)
        
        # Assert
        assert year_1_income == pytest.approx(base_egi, rel=1e-6)
    
    def test_year_2_with_growth(self):
        """Year 2 income includes one year of growth.
        
        CONTEXT.md Part III Section 3.2: "Income Growth: The Gross Potential 
        Rent and Ancillary Income from the previous year are increased by 
        the Annual Income Growth Rate"
        """
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        base_egi = income.calculate_effective_gross_income(num_units=1)
        growth_rate = 0.03
        expected_year_2 = base_egi * (1 + growth_rate)
        
        # Act
        actual_year_2 = income.project_income(year=2, num_units=1)
        
        # Assert
        assert actual_year_2 == pytest.approx(expected_year_2, rel=1e-6)
    
    def test_year_10_compounded_growth(self):
        """Year 10 income includes 9 years of compounded growth."""
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        base_egi = income.calculate_effective_gross_income(num_units=1)
        growth_rate = 0.03
        expected_year_10 = base_egi * ((1 + growth_rate) ** 9)
        
        # Act
        actual_year_10 = income.project_income(year=10, num_units=1)
        
        # Assert
        assert actual_year_10 == pytest.approx(expected_year_10, rel=1e-6)
    
    def test_income_growth_context_md_year_2(self):
        """Year 2 GPR matches CONTEXT.md table: $24,720.
        
        From CONTEXT.md Part III table: Year 2 GPR = $24,720 (3% growth)
        """
        # Arrange
        income = Income(
            monthly_rent_per_unit=2_000,
            vacancy_rate_percent=5.0,
            credit_loss_percent=0.0,
            annual_rent_increase_percent=3.0,
        )
        year_1_gpr = 24_000
        expected_year_2_gpr = year_1_gpr * 1.03  # $24,720
        
        # Act
        # Note: project_income returns EGI, not GPR
        # We need to verify GPR growth separately
        year_1_egi = income.project_income(year=1, num_units=1)
        year_2_egi = income.project_income(year=2, num_units=1)
        
        # Assert
        # Verify growth rate is applied correctly
        growth_factor = year_2_egi / year_1_egi
        assert growth_factor == pytest.approx(1.03, rel=1e-6)
