"""Cash flow analysis calculator."""

from typing import Dict, List
import pandas as pd
from pydantic import BaseModel, Field

from .base import Calculator, CalculatorResult


class MonthlyCashFlow(BaseModel):
    """Monthly cash flow breakdown."""
    
    month: int
    year: int
    
    # Income
    gross_rent: float = 0
    other_income: float = 0
    vacancy_loss: float = 0
    effective_income: float = 0
    
    # Expenses
    property_tax: float = 0
    insurance: float = 0
    hoa: float = 0
    utilities: float = 0
    maintenance: float = 0
    property_management: float = 0
    other_expenses: float = 0
    total_expenses: float = 0
    
    # Cash Flow
    net_operating_income: float = 0
    debt_service: float = 0
    pre_tax_cash_flow: float = 0
    
    # Cumulative
    cumulative_cash_flow: float = 0


class CashFlowAnalysis(BaseModel):
    """Complete cash flow analysis."""
    
    monthly_flows: List[MonthlyCashFlow]
    
    # Summary Statistics
    average_monthly_noi: float
    average_monthly_cash_flow: float
    total_year1_cash_flow: float
    
    # Cash Flow Metrics
    months_to_positive_cash_flow: int
    cash_flow_volatility: float
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        return pd.DataFrame([flow.dict() for flow in self.monthly_flows])
    
    def get_yearly_summary(self) -> pd.DataFrame:
        """Get yearly summary of cash flows."""
        df = self.to_dataframe()
        return df.groupby('year').agg({
            'effective_income': 'sum',
            'total_expenses': 'sum',
            'net_operating_income': 'sum',
            'debt_service': 'sum',
            'pre_tax_cash_flow': 'sum'
        }).round(2)


class CashFlowCalculator(Calculator):
    """Calculator for detailed cash flow analysis."""
    
    def calculate(self, years: int = 1, **kwargs) -> CalculatorResult[CashFlowAnalysis]:
        """Calculate monthly cash flows."""
        errors = self.validate_inputs()
        if errors:
            return CalculatorResult(
                success=False,
                data=None,
                errors=errors
            )
        
        monthly_flows = []
        cumulative_cash_flow = 0
        
        for year in range(1, years + 1):
            for month in range(1, 13):
                month_data = self._calculate_month(year, month)
                cumulative_cash_flow += month_data.pre_tax_cash_flow
                month_data.cumulative_cash_flow = cumulative_cash_flow
                monthly_flows.append(month_data)
        
        # Calculate summary statistics
        df = pd.DataFrame([flow.dict() for flow in monthly_flows])
        
        analysis = CashFlowAnalysis(
            monthly_flows=monthly_flows,
            average_monthly_noi=df['net_operating_income'].mean(),
            average_monthly_cash_flow=df['pre_tax_cash_flow'].mean(),
            total_year1_cash_flow=df[df['year'] == 1]['pre_tax_cash_flow'].sum(),
            months_to_positive_cash_flow=self._find_positive_cash_flow_month(monthly_flows),
            cash_flow_volatility=df['pre_tax_cash_flow'].std()
        )
        
        return CalculatorResult(
            success=True,
            data=analysis
        )
    
    def _calculate_month(self, year: int, month: int) -> MonthlyCashFlow:
        """Calculate cash flow for a specific month."""
        deal = self.deal
        
        # Income with growth
        growth_factor = (1 + deal.income.annual_rent_increase_percent / 100) ** (year - 1)
        
        gross_rent = (deal.income.monthly_rent_per_unit * deal.property.num_units) * growth_factor
        other_income = sum(
            item.get_total_monthly(deal.property.num_units) 
            for item in deal.income.other_income
        ) * growth_factor
        
        total_income = gross_rent + other_income
        vacancy_loss = total_income * (deal.income.vacancy_rate_percent / 100)
        effective_income = total_income - vacancy_loss
        
        # Monthly expenses with growth
        expense_growth = (1 + deal.expenses.annual_expense_growth_percent / 100) ** (year - 1)
        
        property_tax = (deal.expenses.property_tax_annual / 12) * expense_growth
        insurance = (deal.expenses.insurance_annual / 12) * expense_growth
        hoa = deal.expenses.hoa_monthly * expense_growth
        utilities = deal.expenses.landlord_paid_utilities_monthly * expense_growth
        
        # Variable expenses based on income
        annual_egi = effective_income * 12
        maintenance = (annual_egi * deal.expenses.maintenance_percent / 100) / 12
        property_management = (annual_egi * deal.expenses.property_management_percent / 100) / 12
        
        # Other expenses
        other_expenses = sum(
            expense.calculate_annual_expense(annual_egi, deal.property.num_units) / 12
            for expense in deal.expenses.other_expenses
        )
        
        total_expenses = (
            property_tax + insurance + hoa + utilities + 
            maintenance + property_management + other_expenses
        )
        
        # NOI and cash flow
        noi = effective_income - total_expenses
        debt_service = deal.financing.monthly_payment or 0
        cash_flow = noi - debt_service
        
        return MonthlyCashFlow(
            month=month,
            year=year,
            gross_rent=gross_rent,
            other_income=other_income,
            vacancy_loss=vacancy_loss,
            effective_income=effective_income,
            property_tax=property_tax,
            insurance=insurance,
            hoa=hoa,
            utilities=utilities,
            maintenance=maintenance,
            property_management=property_management,
            other_expenses=other_expenses,
            total_expenses=total_expenses,
            net_operating_income=noi,
            debt_service=debt_service,
            pre_tax_cash_flow=cash_flow
        )
    
    def _find_positive_cash_flow_month(self, flows: List[MonthlyCashFlow]) -> int:
        """Find first month with positive cumulative cash flow."""
        for i, flow in enumerate(flows):
            if flow.cumulative_cash_flow > 0:
                return i + 1
        return -1  # Never positive 