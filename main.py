import pandas as pd
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt
import seaborn as sns

class RealEstateDeal:
    """
    A class to perform a comprehensive financial analysis of a rental property investment.
    """
    def __init__(self, property_address, purchase_price, closing_costs, rehab_budget,
                 is_cash_purchase, down_payment_pct, interest_rate, loan_term_years, loan_points,
                 gross_monthly_rent, other_monthly_income, vacancy_rate_pct,
                 property_taxes_yearly, property_insurance_yearly, hoa_monthly,
                 maintenance_pct_egi, capex_pct_egi, mgmt_fee_pct_egi,
                 landlord_paid_utilities_monthly,
                 income_growth_pct, expense_growth_pct, appreciation_pct, sales_expenses_pct):
        """
        Initializes the RealEstateDeal with all necessary input parameters.
        """
        # Store all inputs as attributes
        self.property_address = property_address
        self.purchase_price = purchase_price
        self.closing_costs = closing_costs
        self.rehab_budget = rehab_budget
        self.is_cash_purchase = is_cash_purchase
        self.down_payment_pct = down_payment_pct / 100
        self.interest_rate = interest_rate / 100
        self.loan_term_years = loan_term_years
        self.loan_points = loan_points / 100
        self.gross_monthly_rent = gross_monthly_rent
        self.other_monthly_income = other_monthly_income
        self.vacancy_rate_pct = vacancy_rate_pct / 100
        self.property_taxes_yearly = property_taxes_yearly
        self.property_insurance_yearly = property_insurance_yearly
        self.hoa_monthly = hoa_monthly
        self.maintenance_pct_egi = maintenance_pct_egi / 100
        self.capex_pct_egi = capex_pct_egi / 100
        self.mgmt_fee_pct_egi = mgmt_fee_pct_egi / 100
        self.landlord_paid_utilities_monthly = landlord_paid_utilities_monthly
        self.income_growth_pct = income_growth_pct / 100
        self.expense_growth_pct = expense_growth_pct / 100
        self.appreciation_pct = appreciation_pct / 100
        self.sales_expenses_pct = sales_expenses_pct / 100

        # Calculated initial values
        self.total_project_cost = self.purchase_price + self.closing_costs + self.rehab_budget
        if self.is_cash_purchase:
            self.loan_amount = 0
            self.down_payment = self.total_project_cost
            self.total_cash_invested = self.total_project_cost
        else:
            self.loan_amount = self.purchase_price * (1 - self.down_payment_pct)
            self.down_payment = self.purchase_price * self.down_payment_pct
            # Per document, total cash invested includes down payment, closing costs, rehab, and loan points
            self.total_cash_invested = self.down_payment + self.closing_costs + self.rehab_budget + (self.loan_amount * self.loan_points)

        # Initialize containers for calculated data
        self.amortization_schedule = None
        self.proforma = None

    def _calculate_amortization_schedule(self):
        """
        Generates a yearly loan amortization schedule.
        """
        if self.is_cash_purchase or self.loan_amount == 0:
            columns = ['Year', 'Total Payment', 'Principal', 'Interest', 'Ending Balance']
            self.amortization_schedule = pd.DataFrame(np.zeros((self.loan_term_years + 1, 5)), columns=columns)
            self.amortization_schedule['Year'] = range(self.loan_term_years + 1)
            return

        monthly_rate = self.interest_rate / 12
        num_payments = self.loan_term_years * 12

        if monthly_rate > 0:
            monthly_payment = npf.pmt(monthly_rate, num_payments, -self.loan_amount)
        else:
            monthly_payment = self.loan_amount / num_payments if num_payments > 0 else 0
        
        schedule = []
        balance = self.loan_amount

        for i in range(1, num_payments + 1):
            interest = balance * monthly_rate
            principal = monthly_payment - interest
            balance -= principal
            schedule.append([i, monthly_payment, principal, interest, balance])

        df = pd.DataFrame(schedule, columns=['Month', 'Total Payment', 'Principal', 'Interest', 'Ending Balance'])
        df['Year'] = (df['Month'] - 1) // 12 + 1
        
        yearly_summary = df.groupby('Year').agg({
            'Total Payment': 'sum',
            'Principal': 'sum',
            'Interest': 'sum',
            'Ending Balance': 'last'
        }).reset_index()

        year0 = pd.DataFrame({
            'Year': [0],
            'Total Payment': [0],
            'Principal': [0],
            'Interest': [0],
            'Ending Balance': [self.loan_amount]
        })
        self.amortization_schedule = pd.concat([year0, yearly_summary]).reset_index(drop=True)


    def _run_proforma_projections(self, years=30):
        """
        Builds a 30-year pro-forma financial projection.
        """
        if self.amortization_schedule is None:
            self._calculate_amortization_schedule()

        proforma = pd.DataFrame(index=range(years + 1))
        proforma['Year'] = proforma.index

        # Year 0 - Acquisition
        proforma.loc[0, 'Gross Potential Rent'] = 0
        proforma.loc[0, 'Vacancy Loss'] = 0
        proforma.loc[0, 'Effective Gross Income'] = 0
        proforma.loc[0, 'Total Operating Expenses'] = 0
        proforma.loc[0, 'Net Operating Income'] = 0
        proforma.loc[0, 'Debt Service'] = 0
        proforma.loc[0, 'Pre-Tax Cash Flow'] = -self.total_cash_invested
        proforma.loc[0, 'Property Value'] = self.purchase_price
        proforma.loc[0, 'Loan Balance'] = self.loan_amount
        proforma.loc[0, 'Total Equity'] = self.purchase_price - self.loan_amount
        proforma.loc[0, 'Cumulative Principal Paid'] = 0

        # Project Year 1 through 30
        for year in range(1, years + 1):
            if year == 1:
                gpr = (self.gross_monthly_rent + self.other_monthly_income) * 12
                prop_val = self.purchase_price * (1 + self.appreciation_pct)
            else:
                gpr = proforma.loc[year - 1, 'Gross Potential Rent'] * (1 + self.income_growth_pct)
                prop_val = proforma.loc[year - 1, 'Property Value'] * (1 + self.appreciation_pct)

            vacancy_loss = gpr * self.vacancy_rate_pct
            egi = gpr - vacancy_loss

            # Calculate expenses
            taxes = self.property_taxes_yearly * ((1 + self.expense_growth_pct) ** (year - 1))
            insurance = self.property_insurance_yearly * ((1 + self.expense_growth_pct) ** (year - 1))
            hoa = self.hoa_monthly * 12 * ((1 + self.expense_growth_pct) ** (year - 1))
            utilities = self.landlord_paid_utilities_monthly * 12 * ((1 + self.expense_growth_pct) ** (year - 1))
            maintenance = egi * self.maintenance_pct_egi
            capex = egi * self.capex_pct_egi
            mgmt_fee = egi * self.mgmt_fee_pct_egi
            total_opex = taxes + insurance + hoa + utilities + maintenance + capex + mgmt_fee

            noi = egi - total_opex
            
            debt_service = self.amortization_schedule.loc[year, 'Total Payment'] if year <= self.loan_term_years else 0
            cash_flow = noi - debt_service
            loan_balance = self.amortization_schedule.loc[year, 'Ending Balance'] if year <= self.loan_term_years else 0

            proforma.loc[year, 'Gross Potential Rent'] = gpr
            proforma.loc[year, 'Vacancy Loss'] = vacancy_loss
            proforma.loc[year, 'Effective Gross Income'] = egi
            proforma.loc[year, 'Total Operating Expenses'] = total_opex
            proforma.loc[year, 'Net Operating Income'] = noi
            proforma.loc[year, 'Debt Service'] = debt_service
            proforma.loc[year, 'Pre-Tax Cash Flow'] = cash_flow
            proforma.loc[year, 'Property Value'] = prop_val
            proforma.loc[year, 'Loan Balance'] = loan_balance
            proforma.loc[year, 'Total Equity'] = prop_val - loan_balance
            
            principal_paid_this_year = self.amortization_schedule.loc[year, 'Principal'] if year <= self.loan_term_years else 0
            proforma.loc[year, 'Cumulative Principal Paid'] = proforma.loc[year-1, 'Cumulative Principal Paid'] + principal_paid_this_year

        self.proforma = proforma.set_index('Year')

    def calculate_all_metrics(self, holding_period):
        """
        Calculates all key financial metrics for a given holding period.
        """
        if self.proforma is None:
            self._run_proforma_projections()
        
        metrics = {}

        # Year 1 Metrics
        metrics['noi_y1'] = self.proforma.loc[1, 'Net Operating Income']
        metrics['cap_rate_y1'] = metrics['noi_y1'] / self.purchase_price if self.purchase_price > 0 else 0
        metrics['cash_flow_y1'] = self.proforma.loc[1, 'Pre-Tax Cash Flow']
        metrics['coc_return_y1'] = metrics['cash_flow_y1'] / self.total_cash_invested if self.total_cash_invested > 0 else 0

        # Metrics over holding period
        noi_subset = self.proforma.loc[1:holding_period, 'Net Operating Income']
        debt_service_subset = self.proforma.loc[1:holding_period, 'Debt Service']
        metrics['average_dscr'] = (noi_subset / debt_service_subset).mean() if not self.is_cash_purchase and debt_service_subset.all() > 0 else float('inf')
        
        # Sale Proceeds Calculation
        sale_price = self.proforma.loc[holding_period, 'Property Value']
        sales_costs = sale_price * self.sales_expenses_pct
        loan_payoff = self.proforma.loc[holding_period, 'Loan Balance']
        net_sale_proceeds = sale_price - sales_costs - loan_payoff
        
        # IRR and Equity Multiple
        cash_flows = self.proforma.loc[0:holding_period, 'Pre-Tax Cash Flow'].tolist()
        cash_flows[-1] += net_sale_proceeds # Add sale proceeds to the last year's cash flow
        metrics['irr'] = npf.irr(cash_flows) if self.total_cash_invested > 0 else 0
        
        total_cash_in = self.proforma.loc[1:holding_period, 'Pre-Tax Cash Flow'].sum() + net_sale_proceeds
        metrics['equity_multiple'] = total_cash_in / self.total_cash_invested if self.total_cash_invested > 0 else 0
        
        return metrics

    def _normalize_metric(self, value, thresholds):
        """Helper to normalize a metric value to a 0-100 scale."""
        low, mid, high = thresholds
        if value <= low: return 0
        if value >= high: return 100
        if value <= mid:
            return 50 * (value - low) / (mid - low)
        else:
            return 50 + 50 * (value - mid) / (high - mid)

    def get_deal_score(self, investor_profile='balanced', holding_period=10):
        """
        Calculates a weighted Deal Score based on investor profile.
        """
        metrics = self.calculate_all_metrics(holding_period)
        
        # Define thresholds [Poor, Average, Excellent] for normalization
        thresholds = {
            'coc_return_y1': [0.02, 0.08, 0.15],
            'average_dscr': [1.2, 1.5, 2.0],
            'irr': [0.05, 0.12, 0.20],
            'equity_multiple': [1.2, 2.0, 3.0],
            'cap_rate_y1': [0.03, 0.055, 0.08]
        }
        
        # Define weights for each investor profile
        weights = {
            'cash_flow': {'coc_return_y1': 0.4, 'average_dscr': 0.3, 'irr': 0.1, 'equity_multiple': 0.1, 'cap_rate_y1': 0.1},
            'balanced': {'coc_return_y1': 0.25, 'average_dscr': 0.20, 'irr': 0.25, 'equity_multiple': 0.20, 'cap_rate_y1': 0.1},
            'appreciation': {'coc_return_y1': 0.1, 'average_dscr': 0.1, 'irr': 0.4, 'equity_multiple': 0.3, 'cap_rate_y1': 0.1}
        }
        
        if investor_profile not in weights:
            raise ValueError("Invalid investor profile. Choose from 'cash_flow', 'balanced', 'appreciation'.")
        
        selected_weights = weights[investor_profile]
        
        # Normalize scores
        norm_scores = {
            'coc_return_y1': self._normalize_metric(metrics['coc_return_y1'], thresholds['coc_return_y1']),
            'average_dscr': self._normalize_metric(metrics['average_dscr'], thresholds['average_dscr']),
            'irr': self._normalize_metric(metrics['irr'], thresholds['irr']),
            'equity_multiple': self._normalize_metric(metrics['equity_multiple'], thresholds['equity_multiple']),
            'cap_rate_y1': self._normalize_metric(metrics['cap_rate_y1'], thresholds['cap_rate_y1'])
        }
        
        # Calculate final score
        deal_score = sum(norm_scores[metric] * selected_weights[metric] for metric in selected_weights)
        
        return deal_score, metrics, norm_scores

    def plot_visualizations(self, holding_period=10):
        """
        Generates and displays key performance visualizations.
        """
        if self.proforma is None:
            self._run_proforma_projections()
        
        subset_proforma = self.proforma.loc[1:holding_period].copy()
        
        sns.set_style("whitegrid")
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Investment Analysis for {self.property_address} ({holding_period}-Year Hold)', fontsize=16)

        # 1. Equity Buildup
        ax1 = axes[0, 0]
        subset_proforma['Appreciation Equity'] = subset_proforma['Property Value'] - self.purchase_price
        # Correctly calculate principal paydown equity based on cumulative principal paid
        subset_proforma['Principal Paydown Equity'] = subset_proforma['Cumulative Principal Paid']
        ax1.stackplot(subset_proforma.index,
                      subset_proforma['Principal Paydown Equity'],
                      subset_proforma['Appreciation Equity'],
                      labels=['Principal Paydown', 'Appreciation'],
                      colors=['#3498db', '#2ecc71'])
        ax1.set_title('Equity Buildup Over Time')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Equity ($)')
        ax1.legend(loc='upper left')
        ax1.ticklabel_format(style='plain', axis='y')

        # 2. Annual Cash Flow & NOI
        ax2 = axes[0, 1]
        ax2.bar(subset_proforma.index, subset_proforma['Net Operating Income'], label='NOI', color='#e74c3c')
        ax2.bar(subset_proforma.index, subset_proforma['Pre-Tax Cash Flow'], label='Pre-Tax Cash Flow', color='#f1c40f')
        ax2.set_title('Annual Income and Cash Flow')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Amount ($)')
        ax2.legend(loc='upper left')
        ax2.ticklabel_format(style='plain', axis='y')

        # 3. Loan Amortization
        ax3 = axes[1, 0]
        if not self.is_cash_purchase:
            amort_subset = self.amortization_schedule[(self.amortization_schedule['Year'] >= 1) & (self.amortization_schedule['Year'] <= holding_period)]
            ax3.bar(amort_subset['Year'], amort_subset['Interest'], label='Interest Paid', color='#9b59b6')
            ax3.bar(amort_subset['Year'], amort_subset['Principal'], bottom=amort_subset['Interest'], label='Principal Paid', color='#34495e')
            ax3.set_title('Loan Amortization (Annual Payments)')
            ax3.set_xlabel('Year')
            ax3.set_ylabel('Payment Amount ($)')
            ax3.legend(loc='upper right')
            ax3.ticklabel_format(style='plain', axis='y')
        else:
            ax3.text(0.5, 0.5, "All-Cash Purchase\nNo Loan Amortization", ha='center', va='center', fontsize=12)
            ax3.set_title('Loan Amortization (Annual Payments)')
            ax3.axis('off')

        # 4. Key Metrics Table
        ax4 = axes[1, 1]
        deal_score, metrics, _ = self.get_deal_score(holding_period=holding_period)
        metrics_text = (
            f"Deal Score (Balanced): {deal_score:.1f} / 100\n\n"
            f"Year 1 Cap Rate: {metrics['cap_rate_y1']:.2%}\n"
            f"Year 1 CoC Return: {metrics['coc_return_y1']:.2%}\n"
            f"Average DSCR: {metrics['average_dscr']:.2f}x\n"
            f"{holding_period}-Year IRR: {metrics['irr']:.2%}\n"
            f"{holding_period}-Year Equity Multiple: {metrics['equity_multiple']:.2f}x"
        )
        ax4.text(0.5, 0.5, metrics_text, ha='center', va='center', fontsize=12,
                 bbox=dict(boxstyle="round,pad=0.5", fc='aliceblue', ec="black", lw=1))
        ax4.set_title('Key Performance Indicators')
        ax4.axis('off')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()

if __name__ == "__main__":
    # Demo: Analyzing a realistic rental property investment
    print("=" * 60)
    print("REAL ESTATE INVESTMENT ANALYSIS DEMO")
    print("=" * 60)
    
    # Create a deal with realistic parameters
    deal = RealEstateDeal(
        property_address="123 Oak Street, Denver, CO",
        purchase_price=275000,           # $275k purchase price
        closing_costs=6875,              # 2.5% of purchase price
        rehab_budget=18000,              # $18k for renovations
        is_cash_purchase=False,          # Financed purchase
        down_payment_pct=20,             # 20% down payment
        interest_rate=7.25,              # 7.25% interest rate
        loan_term_years=30,              # 30-year mortgage
        loan_points=1.0,                 # 1% loan points
        gross_monthly_rent=2400,         # $2,400/month rent
        other_monthly_income=150,        # $150 other income (laundry, parking)
        vacancy_rate_pct=6,              # 6% vacancy rate
        property_taxes_yearly=3850,      # $3,850 annual property taxes
        property_insurance_yearly=1320,  # $1,320 annual insurance
        hoa_monthly=75,                  # $75/month HOA fees
        maintenance_pct_egi=8,           # 8% of EGI for maintenance
        capex_pct_egi=5,                 # 5% of EGI for capital expenditures
        mgmt_fee_pct_egi=9,              # 9% management fee
        landlord_paid_utilities_monthly=125,  # $125/month utilities
        income_growth_pct=2.5,           # 2.5% annual rent growth
        expense_growth_pct=2.8,          # 2.8% annual expense growth
        appreciation_pct=3.2,            # 3.2% annual appreciation
        sales_expenses_pct=7             # 7% sales costs when selling
    )
    
    print(f"Property: {deal.property_address}")
    print(f"Purchase Price: ${deal.purchase_price:,}")
    print(f"Total Cash Invested: ${deal.total_cash_invested:,}")
    print(f"Loan Amount: ${deal.loan_amount:,}")
    print("-" * 60)
    
    # Calculate key metrics for different holding periods
    holding_periods = [5, 10, 15]
    
    for period in holding_periods:
        print(f"\n{period}-YEAR ANALYSIS:")
        print("-" * 30)
        
        metrics = deal.calculate_all_metrics(period)
        
        print(f"Year 1 Cap Rate: {metrics['cap_rate_y1']:.2%}")
        print(f"Year 1 Cash-on-Cash Return: {metrics['coc_return_y1']:.2%}")
        print(f"Average Debt Service Coverage Ratio: {metrics['average_dscr']:.2f}x")
        print(f"{period}-Year IRR: {metrics['irr']:.2%}")
        print(f"{period}-Year Equity Multiple: {metrics['equity_multiple']:.2f}x")
        
        # Get deal scores for different investor profiles
        for profile in ['cash_flow', 'balanced', 'appreciation']:
            score, _, _ = deal.get_deal_score(investor_profile=profile, holding_period=period)
            print(f"Deal Score ({profile.title()}): {score:.1f}/100")
    
    print("\n" + "=" * 60)
    print("GENERATING VISUALIZATIONS...")
    print("=" * 60)
    
    # Generate visualizations for 10-year hold
    deal.plot_visualizations(holding_period=10)
    
    print("\nAnalysis complete! Check the generated plots above.")