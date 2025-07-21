"""Pro-forma financial projections calculator."""

from typing import Dict, List
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

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
        
        # Year 0 - Initial Investment
        year_0 = ProFormaYear(
            year=0,
            pre_tax_cash_flow=-self.deal.total_cash_needed,
            property_value=self.deal.property.purchase_price,
            loan_balance=self.deal.financing.loan_amount,
            total_equity=self.deal.property.purchase_price - self.deal.financing.loan_amount,
        )
        proforma_years.append(year_0)
        
        # Years 1 through N
        for year in range(1, years + 1):
            year_data = self._calculate_year(
                year, 
                amort_schedule, 
                cumulative_cash_flow,
                cumulative_principal
            )
            
            # Update cumulative values
            cumulative_cash_flow += year_data.pre_tax_cash_flow
            year_data.cumulative_cash_flow = cumulative_cash_flow
            
            if year_data.principal_payment > 0:
                cumulative_principal += year_data.principal_payment
                year_data.cumulative_principal_paid = cumulative_principal
            
            proforma_years.append(year_data)
        
        proforma = ProForma(
            years=proforma_years,
            initial_investment=self.deal.total_cash_needed
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
        cumulative_principal: float
    ) -> ProFormaYear:
        """Calculate financials for a specific year."""
        # Income projections
        income = self.deal.income
        num_units = self.deal.property.num_units
        
        # Calculate base income with growth
        if year == 1:
            gpr = income.calculate_gross_potential_rent(num_units)
            other = income.calculate_other_income_annual(num_units)
        else:
            growth_factor = (1 + income.annual_rent_increase_percent / 100) ** (year - 1)
            gpr = income.calculate_gross_potential_rent(num_units) * growth_factor
            other = income.calculate_other_income_annual(num_units) * growth_factor
        
        total_potential = gpr + other
        vacancy_loss = total_potential * (income.vacancy_rate_percent / 100)
        egi = total_potential - vacancy_loss
        
        # Expense projections
        expenses = self.deal.expenses
        if year == 1:
            opex = expenses.calculate_total_operating_expenses(egi, num_units)
            expense_breakdown = expenses.get_expense_breakdown(egi, num_units)
        else:
            growth_factor = (1 + expenses.annual_expense_growth_percent / 100) ** (year - 1)
            base_opex = expenses.calculate_total_operating_expenses(egi, num_units)
            opex = base_opex * growth_factor
            
            # Scale expense breakdown
            base_breakdown = expenses.get_expense_breakdown(egi, num_units)
            expense_breakdown = {k: v * growth_factor for k, v in base_breakdown.items()}
        
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
        ) 