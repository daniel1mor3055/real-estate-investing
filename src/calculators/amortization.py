"""Amortization schedule calculator."""

from typing import List
import pandas as pd
import numpy_financial as npf
from pydantic import BaseModel, Field

from .base import Calculator, CalculatorResult


class AmortizationPayment(BaseModel):
    """Single payment in amortization schedule."""
    
    payment_number: int
    year: int
    month: int
    beginning_balance: float
    payment_amount: float
    principal_payment: float
    interest_payment: float
    ending_balance: float
    cumulative_principal: float
    cumulative_interest: float


class AmortizationSchedule(BaseModel):
    """Complete amortization schedule."""
    
    loan_amount: float
    interest_rate: float
    loan_term_years: int
    monthly_payment: float
    total_interest_paid: float
    payments: List[AmortizationPayment]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert schedule to pandas DataFrame."""
        return pd.DataFrame([p.dict() for p in self.payments])
    
    def get_yearly_summary(self) -> pd.DataFrame:
        """Get yearly summary of payments."""
        df = self.to_dataframe()
        yearly = df.groupby('year').agg({
            'payment_amount': 'sum',
            'principal_payment': 'sum',
            'interest_payment': 'sum',
            'ending_balance': 'last',
            'cumulative_principal': 'last',
            'cumulative_interest': 'last'
        }).round(2)
        return yearly


class AmortizationCalculator(Calculator):
    """Calculator for loan amortization schedules."""
    
    def calculate(self, **kwargs) -> CalculatorResult[AmortizationSchedule]:
        """Calculate amortization schedule."""
        errors = self.validate_inputs()
        if errors:
            return CalculatorResult(
                success=False,
                data=None,
                errors=errors
            )
        
        financing = self.deal.financing
        
        # Handle cash purchases
        if financing.is_cash_purchase or financing.loan_amount == 0:
            return CalculatorResult(
                success=True,
                data=AmortizationSchedule(
                    loan_amount=0,
                    interest_rate=0,
                    loan_term_years=0,
                    monthly_payment=0,
                    total_interest_paid=0,
                    payments=[]
                ),
                warnings=["This is a cash purchase - no amortization schedule needed"]
            )
        
        # Calculate schedule
        schedule = self._calculate_schedule(
            financing.loan_amount,
            financing.interest_rate / 100,
            financing.loan_term_years
        )
        
        return CalculatorResult(
            success=True,
            data=schedule
        )
    
    def _calculate_schedule(
        self, 
        loan_amount: float, 
        annual_rate: float, 
        years: int
    ) -> AmortizationSchedule:
        """Calculate the amortization schedule."""
        monthly_rate = annual_rate / 12
        num_payments = years * 12
        
        # Calculate monthly payment
        if monthly_rate > 0:
            monthly_payment = float(
                npf.pmt(monthly_rate, num_payments, -loan_amount)
            )
        else:
            monthly_payment = loan_amount / num_payments
        
        # Build payment schedule
        payments = []
        balance = loan_amount
        cumulative_principal = 0
        cumulative_interest = 0
        
        for i in range(1, num_payments + 1):
            # Calculate interest and principal for this payment
            interest = balance * monthly_rate
            principal = monthly_payment - interest
            
            # Adjust final payment if needed
            if balance < principal:
                principal = balance
                monthly_payment = principal + interest
            
            balance -= principal
            cumulative_principal += principal
            cumulative_interest += interest
            
            # Create payment record
            payment = AmortizationPayment(
                payment_number=i,
                year=(i - 1) // 12 + 1,
                month=(i - 1) % 12 + 1,
                beginning_balance=balance + principal,
                payment_amount=monthly_payment,
                principal_payment=principal,
                interest_payment=interest,
                ending_balance=max(0, balance),
                cumulative_principal=cumulative_principal,
                cumulative_interest=cumulative_interest
            )
            
            payments.append(payment)
            
            if balance <= 0:
                break
        
        # Create schedule
        total_interest = cumulative_interest
        
        return AmortizationSchedule(
            loan_amount=loan_amount,
            interest_rate=annual_rate * 100,
            loan_term_years=years,
            monthly_payment=monthly_payment,
            total_interest_paid=total_interest,
            payments=payments
        ) 