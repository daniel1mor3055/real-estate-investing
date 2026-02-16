"""Pro-forma financial projections calculator."""

from typing import Dict, List
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from loguru import logger

from .base import Calculator, CalculatorResult
from .amortization import AmortizationCalculator


class ProFormaYear(BaseModel):
    """Financial data for a single year."""
    
    year: int
    
    # Income
    gross_potential_rent: float = 0
    other_income: float = 0
    vacancy_loss: float = 0
    effective_gross_income: float = 0
    
    # Expenses
    operating_expenses: float = 0
    expense_breakdown: Dict[str, float] = Field(default_factory=dict)
    
    # NOI and Cash Flow
    net_operating_income: float = 0
    debt_service: float = 0
    pre_tax_cash_flow: float = 0
    
    # Loan Details
    principal_payment: float = 0
    interest_payment: float = 0
    loan_balance: float = 0
    
    # Property Value and Equity
    property_value: float = 0
    total_equity: float = 0
    equity_from_appreciation: float = 0
    equity_from_principal_paydown: float = 0
    
    # ROE Metrics
    average_equity: float = 0  # Average of beginning and ending equity
    roe: float = 0  # Return on Equity for this year
    
    # Cumulative Metrics
    cumulative_cash_flow: float = 0
    cumulative_principal_paid: float = 0


class ProForma(BaseModel):
    """Complete pro-forma projection."""
    
    years: List[ProFormaYear]
    initial_investment: float
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert pro-forma to pandas DataFrame."""
        data = []
        for year in self.years:
            year_dict = year.dict()
            year_dict.pop('expense_breakdown')  # Remove nested dict
            data.append(year_dict)
        return pd.DataFrame(data).set_index('year')
    
    def get_summary_metrics(self) -> Dict[str, float]:
        """Get summary metrics from the pro-forma."""
        df = self.to_dataframe()
        
        return {
            'total_cash_flow': df['pre_tax_cash_flow'].sum(),
            'average_noi': df['net_operating_income'].mean(),
            'average_cash_flow': df['pre_tax_cash_flow'].mean(),
            'total_principal_paid': df['cumulative_principal_paid'].iloc[-1] if len(df) > 0 else 0,
            'ending_property_value': df['property_value'].iloc[-1] if len(df) > 0 else 0,
            'ending_equity': df['total_equity'].iloc[-1] if len(df) > 0 else 0,
        }


class ProFormaCalculator(Calculator):
    """Calculator for multi-year financial projections."""
    
    def calculate(self, years: int = 30, **kwargs) -> CalculatorResult[ProForma]:
        """Calculate pro-forma projections."""
        errors = self.validate_inputs()
        if errors:
            return CalculatorResult(
                success=False,
                data=None,
                errors=errors
            )
        
        # Get amortization schedule if financed
        amort_schedule = None
        if not self.deal.financing.is_cash_purchase:
            amort_calc = AmortizationCalculator(self.deal)
            amort_result = amort_calc.calculate()
            if amort_result.success:
                amort_schedule = amort_result.data.get_yearly_summary()
        
        # Build pro-forma
        proforma_years = []
        cumulative_cash_flow = 0
        cumulative_principal = 0
        previous_equity = 0  # Track previous year's equity for ROE calculation
        
        # Year 0 - Initial Investment
        year_0 = ProFormaYear(
            year=0,
            pre_tax_cash_flow=-self.deal.get_total_cash_needed(),
            property_value=self.deal.property.purchase_price,
            loan_balance=self.deal.financing.loan_amount,
            total_equity=self.deal.property.purchase_price - self.deal.financing.loan_amount,
        )
        proforma_years.append(year_0)
        previous_equity = year_0.total_equity
        
        # Years 1 through N
        for year in range(1, years + 1):
            year_data = self._calculate_year(
                year, 
                amort_schedule, 
                cumulative_cash_flow,
                cumulative_principal,
                previous_equity
            )
            
            # Update cumulative values
            cumulative_cash_flow += year_data.pre_tax_cash_flow
            year_data.cumulative_cash_flow = cumulative_cash_flow
            
            if year_data.principal_payment > 0:
                cumulative_principal += year_data.principal_payment
                year_data.cumulative_principal_paid = cumulative_principal
            
            proforma_years.append(year_data)
            previous_equity = year_data.total_equity
        
        proforma = ProForma(
            years=proforma_years,
            initial_investment=self.deal.get_total_cash_needed()
        )
        
        return CalculatorResult(
            success=True,
            data=proforma
        )
    
    def _calculate_year(
        self, 
        year: int, 
        amort_schedule: pd.DataFrame,
        cumulative_cash_flow: float,
        cumulative_principal: float,
        previous_equity: float
    ) -> ProFormaYear:
        """Calculate financials for a specific year."""
        # Income projections
        income = self.deal.income
        num_units = self.deal.property.num_units
        
        # Calculate base income with growth
        if year == 1:
            gpr = income.calculate_gross_potential_rent(num_units)
            other = income.calculate_other_income_annual(num_units)
            income_growth_factor = 1.0
        else:
            income_growth_factor = (1 + income.annual_rent_increase_percent / 100) ** (year - 1)
            gpr = income.calculate_gross_potential_rent(num_units) * income_growth_factor
            other = income.calculate_other_income_annual(num_units) * income_growth_factor
        
        total_potential = gpr + other
        vacancy_loss = total_potential * (income.vacancy_rate_percent / 100)
        egi = total_potential - vacancy_loss
        
        # Expense projections
        expenses = self.deal.expenses
        if year == 1:
            opex = expenses.calculate_total_operating_expenses(egi, num_units)
            expense_breakdown = expenses.get_expense_breakdown(egi, num_units, year=1)
            expense_growth_factor = 1.0
        else:
            expense_growth_factor = (1 + expenses.annual_expense_growth_percent / 100) ** (year - 1)
            # Use project_expenses which correctly applies growth only to fixed expenses
            opex = expenses.project_expenses(year, egi, num_units)
            # Get expense breakdown with year parameter for proper growth calculation
            expense_breakdown = expenses.get_expense_breakdown(egi, num_units, year=year)
        
        # NOI
        noi = egi - opex
        
        # Debt service and loan details
        if amort_schedule is not None and year <= len(amort_schedule):
            year_amort = amort_schedule.iloc[year - 1]
            debt_service = year_amort['payment_amount']
            principal = year_amort['principal_payment']
            interest = year_amort['interest_payment']
            loan_balance = year_amort['ending_balance']
        else:
            debt_service = 0
            principal = 0
            interest = 0
            loan_balance = 0
        
        # Cash flow
        cash_flow = noi - debt_service
        
        # Property value with appreciation
        appreciation_rate = self.deal.market_assumptions.annual_appreciation_percent / 100
        property_value = self.deal.property.purchase_price * ((1 + appreciation_rate) ** year)
        
        # Equity calculation
        total_equity = property_value - loan_balance
        equity_from_appreciation = property_value - self.deal.property.purchase_price
        equity_from_principal = cumulative_principal + principal
        
        # ANNUAL OPEX LOGGING - Log every year
        logger.info(f"\n{'='*90}")
        logger.info(f"📅 ANNUAL PRO-FORMA - YEAR {year} | Deal: {self.deal.deal_id}")
        logger.info(f"{'='*90}")
        
        # Income section
        logger.info(f"\n💵 ANNUAL INCOME:")
        logger.info(f"  Base Rent/Unit = {income.monthly_rent_per_unit:.2f}")
        logger.info(f"  Income Growth Factor = (1 + {income.annual_rent_increase_percent}% / 100) ^ ({year} - 1) = {income_growth_factor:.4f}")
        base_gpr = income.calculate_gross_potential_rent(num_units)
        logger.info(f"  Gross Potential Rent = {base_gpr:.2f} × {income_growth_factor:.4f} = {gpr:.2f}")
        logger.info(f"  Other Income = {other:.2f}")
        logger.info(f"  Total Potential = {gpr:.2f} + {other:.2f} = {total_potential:.2f}")
        logger.info(f"  Vacancy Loss = {total_potential:.2f} × {income.vacancy_rate_percent}% = {vacancy_loss:.2f}")
        logger.info(f"  ➡️  Effective Gross Income = {egi:.2f}")
        
        # OPEX section with detailed breakdown
        logger.info(f"\n💰 ANNUAL OPEX BREAKDOWN:")
        logger.info(f"  Expense Growth Factor = (1 + {expenses.annual_expense_growth_percent}% / 100) ^ ({year} - 1) = {expense_growth_factor:.4f}")
        
        logger.info(f"\n  📌 FIXED EXPENSES (Annual):")
        prop_tax_base = expenses.property_tax_annual
        prop_tax_year = expense_breakdown.get('property_tax', 0)
        logger.info(f"    Property Tax = {prop_tax_base:.2f} × {expense_growth_factor:.4f} = {prop_tax_year:.2f}")
        
        ins_base = expenses.insurance_annual
        ins_year = expense_breakdown.get('insurance', 0)
        logger.info(f"    Insurance = {ins_base:.2f} × {expense_growth_factor:.4f} = {ins_year:.2f}")
        
        hoa_base = expenses.hoa_monthly * 12
        hoa_year = expense_breakdown.get('hoa', 0)
        logger.info(f"    HOA = {hoa_base:.2f} × {expense_growth_factor:.4f} = {hoa_year:.2f}")
        
        util_base = expenses.landlord_paid_utilities_monthly * 12
        util_year = expense_breakdown.get('utilities', 0)
        logger.info(f"    Utilities = {util_base:.2f} × {expense_growth_factor:.4f} = {util_year:.2f}")
        
        fixed_total = prop_tax_year + ins_year + hoa_year + util_year
        logger.info(f"    ➡️  Fixed Total = {fixed_total:.2f} ({fixed_total/egi*100:.2f}% of EGI)")
        
        logger.info(f"\n  📊 VARIABLE EXPENSES (% of EGI - No Additional Growth Factor):")
        maint = expense_breakdown.get('maintenance', 0)
        logger.info(f"    Maintenance = {egi:.2f} × {expenses.maintenance_percent}% = {maint:.2f}")
        
        mgmt = expense_breakdown.get('property_management', 0)
        logger.info(f"    Property Management = {egi:.2f} × {expenses.property_management_percent}% = {mgmt:.2f}")
        
        capex = expense_breakdown.get('capex_reserve', 0)
        logger.info(f"    CapEx Reserve = {egi:.2f} × {expenses.capex_reserve_percent}% = {capex:.2f}")
        
        variable_total = maint + mgmt + capex
        logger.info(f"    ➡️  Variable Total = {variable_total:.2f} ({variable_total/egi*100:.2f}% of EGI)")
        
        # Other expenses
        other_total = 0
        other_keys = [k for k in expense_breakdown.keys() 
                     if k not in ['property_tax', 'insurance', 'hoa', 'utilities', 
                                 'maintenance', 'property_management', 'capex_reserve']]
        if other_keys:
            logger.info(f"\n  📝 OTHER EXPENSES:")
            for key in other_keys:
                val = expense_breakdown[key]
                other_total += val
                logger.info(f"    {key}: {val:.2f}")
            logger.info(f"    ➡️  Other Total = {other_total:.2f} ({other_total/egi*100:.2f}% of EGI)")
        
        logger.info(f"\n  💵 TOTAL ANNUAL OPEX:")
        logger.info(f"    Fixed: {fixed_total:.2f}")
        logger.info(f"    Variable: {variable_total:.2f}")
        logger.info(f"    Other: {other_total:.2f}")
        logger.info(f"    ➡️  TOTAL = {opex:.2f}")
        
        opex_ratio = (opex / egi * 100) if egi > 0 else 0
        logger.info(f"    📈 Operating Expense Ratio = {opex:.2f} / {egi:.2f} = {opex_ratio:.2f}%")
        
        # NOI and Cash Flow
        logger.info(f"\n💸 NET OPERATING INCOME & CASH FLOW:")
        logger.info(f"  NOI = {egi:.2f} - {opex:.2f} = {noi:.2f}")
        cap_rate = (noi / self.deal.property.purchase_price * 100) if self.deal.property.purchase_price > 0 else 0
        logger.info(f"  Cap Rate = {noi:.2f} / {self.deal.property.purchase_price:.2f} = {cap_rate:.2f}%")
        logger.info(f"  Debt Service = {debt_service:.2f}")
        logger.info(f"    (Principal: {principal:.2f}, Interest: {interest:.2f})")
        logger.info(f"  ➡️  Pre-Tax Cash Flow = {noi:.2f} - {debt_service:.2f} = {cash_flow:.2f}")
        
        if debt_service > 0:
            dscr = noi / debt_service if debt_service > 0 else 0
            logger.info(f"  📊 DSCR = {noi:.2f} / {debt_service:.2f} = {dscr:.2f}x")
        
        # Property Value & Equity
        logger.info(f"\n🏠 PROPERTY VALUE & EQUITY:")
        logger.info(f"  Property Value = {self.deal.property.purchase_price:.2f} × (1 + {appreciation_rate*100:.2f}%)^{year} = {property_value:.2f}")
        logger.info(f"  Loan Balance = {loan_balance:.2f}")
        logger.info(f"  Total Equity = {property_value:.2f} - {loan_balance:.2f} = {total_equity:.2f}")
        logger.info(f"    (Appreciation: {equity_from_appreciation:.2f}, Principal Paydown: {equity_from_principal:.2f})")
        
        # ROE Calculation
        average_equity = (previous_equity + total_equity) / 2
        roe = cash_flow / average_equity if average_equity > 0 else 0
        
        logger.info(f"\n📊 RETURN ON EQUITY (ROE):")
        logger.info(f"  Previous Year Equity = {previous_equity:.2f}")
        logger.info(f"  Current Year Equity = {total_equity:.2f}")
        logger.info(f"  Average Equity = ({previous_equity:.2f} + {total_equity:.2f}) / 2 = {average_equity:.2f}")
        logger.info(f"  Annual Pre-Tax Cash Flow = {cash_flow:.2f}")
        logger.info(f"  ➡️  ROE = {cash_flow:.2f} / {average_equity:.2f} = {roe:.2%}")
        
        if roe > 0:
            logger.info(f"  ✅ Positive return on equity: {roe:.2%}")
        elif roe == 0:
            logger.info(f"  ⚠️  Break-even: No return on equity")
        else:
            logger.info(f"  ❌ Negative return: Equity is losing {abs(roe):.2%}")
        
        logger.info(f"{'='*90}\n")
        
        return ProFormaYear(
            year=year,
            gross_potential_rent=gpr,
            other_income=other,
            vacancy_loss=vacancy_loss,
            effective_gross_income=egi,
            operating_expenses=opex,
            expense_breakdown=expense_breakdown,
            net_operating_income=noi,
            debt_service=debt_service,
            pre_tax_cash_flow=cash_flow,
            principal_payment=principal,
            interest_payment=interest,
            loan_balance=loan_balance,
            property_value=property_value,
            total_equity=total_equity,
            equity_from_appreciation=equity_from_appreciation,
            equity_from_principal_paydown=equity_from_principal,
            average_equity=average_equity,
            roe=roe,
        ) 