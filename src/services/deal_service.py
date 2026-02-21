"""Deal service - coordinates deal operations."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel

from ..core.models import (
    Property,
    PropertyType,
    Financing,
    FinancingType,
    SubLoan,
    IsraeliMortgageTrack,
    RepaymentMethod,
    GraceType,
    GracePeriod,
    PrepaymentOption,
    Prepayment,
    Income,
    IncomeSource,
    OperatingExpenses,
    Deal,
    DealStatus,
    MarketAssumptions,
)
from ..core.calculators import (
    MetricsCalculator,
    ProFormaCalculator,
    AmortizationCalculator,
    CashFlowCalculator,
    CalculatorResult,
)
from ..core.calculators.metrics import MetricsBundle
from ..core.calculators.proforma import ProForma
from ..adapters.config_loader import ConfigLoader, get_config_value


class AnalysisResult(BaseModel):
    """Result of a deal analysis."""

    deal: Deal
    metrics: MetricsBundle
    proforma: Optional[ProForma] = None
    holding_period: int

    class Config:
        arbitrary_types_allowed = True


class DealService:
    """Service for managing and analyzing real estate deals."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """Initialize the deal service.
        
        Args:
            config_loader: Optional config loader for loading deal configurations
        """
        self.config_loader = config_loader or ConfigLoader()

    def create_deal_from_config(self, config: Dict) -> Deal:
        """Create a Deal object from a configuration dictionary.
        
        Args:
            config: Configuration dictionary with deal parameters
            
        Returns:
            Fully constructed Deal object
        """
        # Property
        prop_config = config.get("property", {})
        property_obj = Property(
            address=prop_config.get("address", "Unknown"),
            property_type=PropertyType(prop_config.get("type", "single_family")),
            purchase_price=prop_config.get("purchase_price", 0),
            closing_costs=prop_config.get("closing_costs", 0),
            rehab_budget=prop_config.get("rehab_budget", 0),
            num_units=prop_config.get("units", 1),
            bedrooms=prop_config.get("bedrooms", 3),
            bathrooms=prop_config.get("bathrooms", 2),
            square_footage=prop_config.get("square_footage"),
            year_built=prop_config.get("year_built"),
        )

        # Financing
        fin_config = config.get("financing", {})
        financing = self._create_financing_from_config(fin_config, property_obj.purchase_price)

        # Income
        inc_config = config.get("income", {})
        income = Income(
            monthly_rent_per_unit=inc_config.get("monthly_rent", 0),
            vacancy_rate_percent=inc_config.get("vacancy_rate", 5),
            credit_loss_percent=inc_config.get("credit_loss", 1),
            annual_rent_increase_percent=inc_config.get("annual_increase", 3),
        )

        # Add other income sources if provided
        for item in inc_config.get("other_income", []):
            income.add_income_source(
                source=item.get("type", "other"),
                monthly_amount=item.get("amount", 0),
                description=item.get("description"),
                is_per_unit=item.get("per_unit", False),
            )

        # Expenses
        exp_config = config.get("expenses", {})
        expenses = OperatingExpenses(
            property_tax_annual=exp_config.get("property_tax", 0),
            insurance_annual=exp_config.get("insurance", 0),
            hoa_monthly=exp_config.get("hoa", 0),
            maintenance_percent=exp_config.get("maintenance_percent", 5),
            property_management_percent=exp_config.get("management_percent", 8),
            capex_reserve_percent=exp_config.get("capex_percent", 5),
            landlord_paid_utilities_monthly=exp_config.get("utilities", 0),
            annual_expense_growth_percent=exp_config.get("annual_increase", 3),
        )

        # Market assumptions
        market_config = config.get("market", {})
        market = MarketAssumptions(
            annual_appreciation_percent=market_config.get("appreciation", 3.5),
            sales_expense_percent=market_config.get("sales_expense", 7),
            inflation_rate_percent=market_config.get("inflation", 2.5),
        )

        # Create deal
        return Deal(
            deal_id=config.get("id", f"deal-{datetime.now().timestamp()}"),
            deal_name=config.get("name", property_obj.address),
            property=property_obj,
            financing=financing,
            income=income,
            expenses=expenses,
            market_assumptions=market,
            holding_period_years=config.get("holding_period", 10),
        )

    def _create_financing_from_config(
        self, fin_config: Dict, purchase_price: float
    ) -> Financing:
        """Create financing object from config, supporting Israeli mortgage tracks."""
        is_cash = fin_config.get("cash_purchase", False)
        
        if is_cash:
            return Financing(
                financing_type=FinancingType.CASH,
                is_cash_purchase=True,
                down_payment_percent=100,
                interest_rate=0,
                loan_term_years=30,
            )

        # Check for Israeli mortgage tracks
        tracks_config = fin_config.get("israeli_mortgage_tracks", [])
        
        if tracks_config:
            # Israeli mortgage with multiple tracks
            down_payment_pct = fin_config.get("down_payment_percent", 20)
            loan_amount = purchase_price * (1 - down_payment_pct / 100)
            
            sub_loans = []
            for track in tracks_config:
                track_amount = loan_amount * (track.get("percentage", 33) / 100)

                # Resolve term: prefer loan_term_months, fall back to loan_term (years) * 12
                term_months = track.get("loan_term_months")
                if term_months is None:
                    term_months = track.get("loan_term", 30) * 12

                # Build optional grace period
                grace_period = None
                grace_months = track.get("grace_period")
                grace_type_str = track.get("grace_type")
                if grace_months and grace_months > 0 and grace_type_str:
                    grace_period = GracePeriod(
                        duration_months=int(grace_months),
                        grace_type=GraceType(grace_type_str),
                    )

                # Build optional prepayments list
                prepayments = []
                pp_month = track.get("prepayment_month")
                pp_amount = track.get("prepayment_amount")
                if pp_month and pp_amount and pp_amount > 0:
                    prepayments.append(
                        Prepayment(
                            month=int(pp_month),
                            amount=float(pp_amount),
                            option=PrepaymentOption(
                                track.get("prepayment_type", "reduce_payment")
                            ),
                        )
                    )

                sub_loan = SubLoan(
                    name=track.get("name", "Track"),
                    track_type=IsraeliMortgageTrack(track.get("track_type", "fixed_unlinked")),
                    loan_amount=track_amount,
                    base_interest_rate=track.get("base_rate", 5.0),
                    loan_term_months=int(term_months),
                    bank_of_israel_rate=track.get("bank_of_israel_rate"),
                    expected_cpi=track.get("expected_cpi"),
                    repayment_method=RepaymentMethod(
                        track.get("repayment_method", "spitzer")
                    ),
                    grace_period=grace_period,
                    prepayments=prepayments,
                )
                sub_loans.append(sub_loan)

            return Financing.create_israeli_mortgage(
                financing_type=FinancingType(fin_config.get("type", "conventional")),
                down_payment_percent=down_payment_pct,
                mortgage_tracks=sub_loans,
                loan_points=fin_config.get("points", 0),
            )
        else:
            # Simple single loan
            return Financing(
                financing_type=FinancingType(fin_config.get("type", "conventional")),
                is_cash_purchase=False,
                down_payment_percent=fin_config.get("down_payment_percent", 20),
                interest_rate=fin_config.get("interest_rate", 7),
                loan_term_years=fin_config.get("loan_term", 30),
                loan_points=fin_config.get("points", 0),
            )

    def create_deal_from_inputs(
        self,
        property_inputs: Dict[str, Any],
        financing_inputs: Dict[str, Any],
        income_inputs: Dict[str, Any],
        expenses_inputs: Dict[str, Any],
        market_inputs: Optional[Dict[str, Any]] = None,
    ) -> Deal:
        """Create a Deal from structured input dictionaries.
        
        This is primarily used by the Streamlit UI where inputs come from forms.
        """
        # Build config dictionary from inputs
        config = {
            "property": {
                "address": property_inputs.get("address", ""),
                "type": property_inputs.get("property_type", "single_family"),
                "purchase_price": property_inputs.get("purchase_price", 0),
                "closing_costs": property_inputs.get("closing_costs", 0),
                "rehab_budget": property_inputs.get("rehab_budget", 0),
                "units": property_inputs.get("units", 1),
                "bedrooms": property_inputs.get("bedrooms", 3),
                "bathrooms": property_inputs.get("bathrooms", 2),
                "square_footage": property_inputs.get("sqft", property_inputs.get("square_feet", 0)),
                "year_built": property_inputs.get("year_built"),
            },
            "income": {
                "monthly_rent": income_inputs.get("monthly_rent", 0),
                "vacancy_rate": income_inputs.get("vacancy_rate", 5),
                "credit_loss": income_inputs.get("credit_loss", 1),
                "annual_increase": income_inputs.get("annual_increase", 3),
                "other_income": income_inputs.get("other_income", []),
            },
            "expenses": {
                "property_tax": expenses_inputs.get("property_tax", 0),
                "insurance": expenses_inputs.get("insurance", 0),
                "hoa": expenses_inputs.get("hoa", 0),
                "utilities": expenses_inputs.get("utilities", 0),
                "maintenance_percent": expenses_inputs.get("maintenance", 5),
                "management_percent": expenses_inputs.get("management", 8),
                "capex_percent": expenses_inputs.get("capex", 5),
                "annual_increase": expenses_inputs.get("annual_increase", 3),
            },
        }

        # Handle financing based on mode
        fin_mode = financing_inputs.get("mode", "simple")
        
        if fin_mode == "cash":
            config["financing"] = {"cash_purchase": True}
        elif fin_mode == "israeli" and financing_inputs.get("tracks"):
            config["financing"] = {
                "type": financing_inputs.get("financing_type", "conventional"),
                "down_payment_percent": financing_inputs.get("down_payment", 20),
                "israeli_mortgage_tracks": financing_inputs.get("tracks", []),
            }
        else:
            config["financing"] = {
                "type": financing_inputs.get("financing_type", "conventional"),
                "down_payment_percent": financing_inputs.get("down_payment", 20),
                "interest_rate": financing_inputs.get("interest_rate", 7),
                "loan_term": financing_inputs.get("loan_term", 30),
                "points": financing_inputs.get("points", 0),
            }

        # Market assumptions
        if market_inputs:
            config["market"] = market_inputs

        return self.create_deal_from_config(config)

    def run_analysis(
        self,
        deal: Deal,
        holding_period: int = 10,
        include_proforma: bool = True,
    ) -> AnalysisResult:
        """Run comprehensive analysis on a deal.
        
        Args:
            deal: The deal to analyze
            holding_period: Investment holding period in years
            include_proforma: Whether to include full pro-forma in results
            
        Returns:
            AnalysisResult with metrics and optional pro-forma
        """
        # Calculate metrics
        metrics_calc = MetricsCalculator(deal)
        metrics_result = metrics_calc.calculate(
            holding_period=holding_period,
        )

        if not metrics_result.success:
            raise ValueError(f"Metrics calculation failed: {metrics_result.errors}")

        # Calculate pro-forma if requested
        proforma = None
        if include_proforma:
            proforma_calc = ProFormaCalculator(deal)
            proforma_result = proforma_calc.calculate(years=holding_period)
            if proforma_result.success:
                proforma = proforma_result.data

        return AnalysisResult(
            deal=deal,
            metrics=metrics_result.data,
            proforma=proforma,
            holding_period=holding_period,
        )

    def calculate_metrics(
        self,
        deal: Deal,
        holding_period: int = 10,
    ) -> CalculatorResult[MetricsBundle]:
        """Calculate financial metrics for a deal.
        
        Args:
            deal: The deal to analyze
            holding_period: Investment holding period in years
            
        Returns:
            CalculatorResult containing MetricsBundle
        """
        calculator = MetricsCalculator(deal)
        return calculator.calculate(
            holding_period=holding_period,
        )

    def calculate_proforma(
        self, deal: Deal, years: int = 30
    ) -> CalculatorResult[ProForma]:
        """Calculate pro-forma projections for a deal.
        
        Args:
            deal: The deal to analyze
            years: Number of years to project
            
        Returns:
            CalculatorResult containing ProForma
        """
        calculator = ProFormaCalculator(deal)
        return calculator.calculate(years=years)

    def calculate_amortization(self, deal: Deal) -> CalculatorResult:
        """Calculate loan amortization schedule.
        
        Args:
            deal: The deal with financing to analyze
            
        Returns:
            CalculatorResult containing amortization schedule
        """
        calculator = AmortizationCalculator(deal)
        return calculator.calculate()

    def calculate_cash_flow(
        self, deal: Deal, years: int = 3
    ) -> CalculatorResult:
        """Calculate monthly cash flow projections.
        
        Args:
            deal: The deal to analyze
            years: Number of years for monthly projections
            
        Returns:
            CalculatorResult containing cash flow data
        """
        calculator = CashFlowCalculator(deal)
        return calculator.calculate(years=years)
