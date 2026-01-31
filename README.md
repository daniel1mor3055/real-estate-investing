# Real Estate Investment Analysis Tool

A professional-grade, modular Python application for analyzing rental property investments. Built with clean architecture principles, design patterns, and modern Python best practices.

## 🏗️ Architecture Overview

This application demonstrates a complete rewrite of a monolithic real estate analysis tool into a modular, maintainable architecture using:

- **Domain-Driven Design**: Clear separation of business logic into domain models
- **Strategy Pattern**: Flexible investor profiles (cash flow, balanced, appreciation)
- **Factory Pattern**: Dynamic creation of analysis strategies
- **Repository Pattern**: Data persistence abstraction
- **Clean Architecture**: Layered architecture with clear boundaries

## 📁 Project Structure

```
real_estate_investing/
├── src/
│   ├── models/          # Domain models with Pydantic validation
│   │   ├── property.py  # Property entity
│   │   ├── financing.py # Financing structure
│   │   ├── income.py    # Income projections
│   │   ├── expenses.py  # Operating expenses
│   │   ├── deal.py      # Deal aggregate root
│   │   └── metrics.py   # Metric results
│   ├── calculators/     # Business logic calculators
│   │   ├── base.py      # Abstract calculator
│   │   ├── amortization.py
│   │   ├── cash_flow.py
│   │   ├── metrics.py
│   │   └── proforma.py
│   ├── strategies/      # Investor strategies (Strategy Pattern)
│   │   └── investor.py
│   ├── utils/          # Utilities
│   │   ├── logging.py   # Loguru configuration
│   │   └── formatting.py
│   └── config/         # Configuration management
├── cli.py              # Command-line interface (Click)
├── app.py              # GUI interface (Streamlit)
├── main.py             # Demo script
├── requirements.txt    # Dependencies
└── sample_deal.json    # Sample configuration
```

## 🚀 Features

### Core Functionality
- **Comprehensive Financial Analysis**: NOI, Cap Rate, Cash-on-Cash Return, IRR, NPV, Equity Multiple
- **30-Year Pro-Forma Projections**: Detailed year-by-year financial projections
- **Loan Amortization**: Complete payment schedules with principal/interest breakdown
- **Cash Flow Analysis**: Monthly and annual cash flow projections
- **Deal Scoring**: Weighted scoring based on investor profile

### Advanced Features
- **Multiple Investor Profiles**: Cash flow, balanced, and appreciation strategies
- **Sensitivity Analysis**: Test how changes in variables affect returns
- **Risk Metrics**: DSCR, break-even ratio, and more
- **Data Validation**: Pydantic models ensure data integrity
- **Professional Visualizations**: Interactive charts with Plotly

### User Interfaces
- **CLI**: Rich command-line interface with formatted output
- **GUI**: Modern Streamlit web application
- **API-Ready**: Clean architecture allows easy API addition

## 🛠️ Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd real_estate_investing
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip3 install -r requirements.txt
```

## 📖 Usage

### Quick Demo
```bash
python3 main.py
```

### Command-Line Interface

#### Detailed Analysis from Config
```bash
python3 cli.py analyze -c sample_deal.json -p balanced -h 10
```

#### Generate Pro-Forma
```bash
python3 cli.py proforma -c sample_deal.json -y 30 -o proforma.csv
```

#### Calculate Amortization
```bash
python3 cli.py amortization -l 250000 -r 7.0 -t 30
```

### GUI Application
```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## 🏛️ Design Patterns

### Strategy Pattern
Different investor profiles are implemented as strategies:
```python
from src.strategies import get_investor_strategy

strategy = get_investor_strategy("balanced")
score = strategy.calculate_score(metrics)
```

### Factory Pattern
Calculators are created through a consistent interface:
```python
from src.calculators import MetricsCalculator

calculator = MetricsCalculator(deal)
result = calculator.calculate(holding_period=10)
```

### Domain Models
Rich domain models with validation:
```python
from src.models import Property, PropertyType

property = Property(
    address="123 Main St",
    property_type=PropertyType.SINGLE_FAMILY,
    purchase_price=300000,
    bedrooms=3,
    bathrooms=2
)
```

## 📊 Sample Analysis Output

```
REAL ESTATE INVESTMENT ANALYSIS: 123 Oak Street Investment
================================================================================

Property: 123 Oak Street, Denver, CO
Purchase Price: $275,000
Total Investment: $61,075
Financing: $220,000 @ 7.25%

KEY METRICS BY INVESTOR PROFILE:
--------------------------------------------------------------------------------

CASH FLOW INVESTOR:
  Deal Score: 72.5/100
  Year 1 Cap Rate: 4.56%
  Year 1 Cash-on-Cash: 6.47%
  10-Year IRR: 12.3%
  Equity Multiple: 2.15x

BALANCED INVESTOR:
  Deal Score: 68.9/100
  Year 1 Cap Rate: 4.56%
  Year 1 Cash-on-Cash: 6.47%
  10-Year IRR: 12.3%
  Equity Multiple: 2.15x
```

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/ -v --cov=src
```

## 📝 Configuration

### Deal Configuration (JSON)
```json
{
  "property": {
    "address": "123 Main St",
    "purchase_price": 300000,
    "units": 1
  },
  "financing": {
    "down_payment_percent": 20,
    "interest_rate": 7.0
  },
  "income": {
    "monthly_rent": 2500,
    "vacancy_rate": 5
  },
  "expenses": {
    "property_tax": 3600,
    "insurance": 1200
  }
}
```

## 🔧 Advanced Usage

### Custom Investor Strategies
Create custom strategies by extending `InvestorStrategy`:
```python
from src.strategies.investor import InvestorStrategy

class ConservativeInvestor(InvestorStrategy):
    @property
    def weights(self):
        return {
            "dscr": 0.50,
            "cap_rate": 0.30,
            "coc_return": 0.20
        }
```

### Adding New Calculators
Extend the `Calculator` base class:
```python
from src.calculators.base import Calculator, CalculatorResult

class TaxCalculator(Calculator):
    def calculate(self, **kwargs) -> CalculatorResult:
        # Implementation
        pass
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Original concept based on institutional real estate analysis frameworks
- Financial calculations use numpy-financial
- UI built with Streamlit and Click
- Visualizations powered by Plotly 