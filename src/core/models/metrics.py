"""Metrics result domain model."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of financial metrics."""
    
    # Basic Metrics
    NOI = "noi"
    CAP_RATE = "cap_rate"
    CASH_FLOW = "cash_flow"
    COC_RETURN = "coc_return"
    DSCR = "dscr"
    GRM = "grm"
    
    # Advanced Metrics
    IRR = "irr"
    NPV = "npv"
    EQUITY_MULTIPLE = "equity_multiple"
    AVERAGE_ANNUAL_RETURN = "average_annual_return"
    ROE = "roe"
    AVERAGE_ROE = "average_roe"
    
    # Risk Metrics
    BREAK_EVEN_RATIO = "break_even_ratio"
    DEFAULT_RATIO = "default_ratio"
    
    # Score
    DEAL_SCORE = "deal_score"


class MetricResult(BaseModel):
    """Result of a metric calculation."""
    
    metric_type: MetricType = Field(..., description="Type of metric")
    value: float = Field(..., description="Calculated value")
    formatted_value: str = Field(..., description="Human-readable formatted value")
    
    # Context
    year: Optional[int] = Field(None, description="Year of calculation (if applicable)")
    holding_period: Optional[int] = Field(None, description="Holding period used")
    
    # Benchmarking
    benchmark_low: Optional[float] = Field(None, description="Low benchmark value")
    benchmark_target: Optional[float] = Field(None, description="Target benchmark value")
    benchmark_high: Optional[float] = Field(None, description="High benchmark value")
    
    # Additional Data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def is_good(self) -> Optional[bool]:
        """Determine if the metric value is good based on benchmarks."""
        if self.benchmark_target is None:
            return None
        
        # For some metrics, higher is better
        higher_is_better = self.metric_type in [
            MetricType.NOI,
            MetricType.CAP_RATE,
            MetricType.CASH_FLOW,
            MetricType.COC_RETURN,
            MetricType.DSCR,
            MetricType.IRR,
            MetricType.NPV,
            MetricType.EQUITY_MULTIPLE,
            MetricType.AVERAGE_ANNUAL_RETURN,
            MetricType.DEAL_SCORE,
            MetricType.ROE,
            MetricType.AVERAGE_ROE,
        ]
        
        # For some metrics, lower is better
        lower_is_better = self.metric_type in [
            MetricType.GRM,
            MetricType.BREAK_EVEN_RATIO,
            MetricType.DEFAULT_RATIO,
        ]
        
        if higher_is_better:
            return self.value >= self.benchmark_target
        elif lower_is_better:
            return self.value <= self.benchmark_target
        
        return None
    
    @property
    def performance_rating(self) -> str:
        """Get performance rating based on benchmarks."""
        if not all([self.benchmark_low, self.benchmark_target, self.benchmark_high]):
            return "Unknown"
        
        if self.is_good is None:
            return "Unknown"
        
        # Determine if higher or lower is better
        higher_is_better = self.is_good == (self.value >= self.benchmark_target)
        
        if higher_is_better:
            if self.value >= self.benchmark_high:
                return "Excellent"
            elif self.value >= self.benchmark_target:
                return "Good"
            elif self.value >= self.benchmark_low:
                return "Fair"
            else:
                return "Poor"
        else:  # Lower is better
            if self.value <= self.benchmark_low:
                return "Excellent"
            elif self.value <= self.benchmark_target:
                return "Good"
            elif self.value <= self.benchmark_high:
                return "Fair"
            else:
                return "Poor"
    
    @classmethod
    def create_noi(
        cls, 
        value: float, 
        year: int = 1,
        benchmark_low: float = 10000,
        benchmark_target: float = 20000,
        benchmark_high: float = 40000
    ) -> "MetricResult":
        """Create NOI metric result."""
        return cls(
            metric_type=MetricType.NOI,
            value=value,
            formatted_value=f"${value:,.0f}",
            year=year,
            benchmark_low=benchmark_low,
            benchmark_target=benchmark_target,
            benchmark_high=benchmark_high,
        )
    
    @classmethod
    def create_cap_rate(
        cls, 
        value: float,
        benchmark_low: float = 0.04,
        benchmark_target: float = 0.065,
        benchmark_high: float = 0.09
    ) -> "MetricResult":
        """Create Cap Rate metric result."""
        return cls(
            metric_type=MetricType.CAP_RATE,
            value=value,
            formatted_value=f"{value:.2%}",
            benchmark_low=benchmark_low,
            benchmark_target=benchmark_target,
            benchmark_high=benchmark_high,
        )
    
    @classmethod
    def create_coc_return(
        cls, 
        value: float,
        year: int = 1,
        benchmark_low: float = 0.06,
        benchmark_target: float = 0.10,
        benchmark_high: float = 0.15
    ) -> "MetricResult":
        """Create Cash-on-Cash Return metric result."""
        return cls(
            metric_type=MetricType.COC_RETURN,
            value=value,
            formatted_value=f"{value:.2%}",
            year=year,
            benchmark_low=benchmark_low,
            benchmark_target=benchmark_target,
            benchmark_high=benchmark_high,
        )
    
    @classmethod
    def create_dscr(
        cls, 
        value: float,
        benchmark_low: float = 1.2,
        benchmark_target: float = 1.5,
        benchmark_high: float = 2.0
    ) -> "MetricResult":
        """Create DSCR metric result."""
        return cls(
            metric_type=MetricType.DSCR,
            value=value,
            formatted_value=f"{value:.2f}x",
            benchmark_low=benchmark_low,
            benchmark_target=benchmark_target,
            benchmark_high=benchmark_high,
        )
    
    @classmethod
    def create_irr(
        cls, 
        value: float,
        holding_period: int,
        benchmark_low: float = 0.08,
        benchmark_target: float = 0.15,
        benchmark_high: float = 0.25
    ) -> "MetricResult":
        """Create IRR metric result."""
        return cls(
            metric_type=MetricType.IRR,
            value=value,
            formatted_value=f"{value:.2%}",
            holding_period=holding_period,
            benchmark_low=benchmark_low,
            benchmark_target=benchmark_target,
            benchmark_high=benchmark_high,
        )
    
    @classmethod
    def create_equity_multiple(
        cls, 
        value: float,
        holding_period: int,
        benchmark_low: float = 1.5,
        benchmark_target: float = 2.0,
        benchmark_high: float = 3.0
    ) -> "MetricResult":
        """Create Equity Multiple metric result."""
        return cls(
            metric_type=MetricType.EQUITY_MULTIPLE,
            value=value,
            formatted_value=f"{value:.2f}x",
            holding_period=holding_period,
            benchmark_low=benchmark_low,
            benchmark_target=benchmark_target,
            benchmark_high=benchmark_high,
        )
    
    @classmethod
    def create_deal_score(
        cls, 
        value: float,
        investor_profile: str,
        holding_period: int
    ) -> "MetricResult":
        """Create Deal Score metric result."""
        return cls(
            metric_type=MetricType.DEAL_SCORE,
            value=value,
            formatted_value=f"{value:.1f}/100",
            holding_period=holding_period,
            benchmark_low=40,
            benchmark_target=60,
            benchmark_high=80,
            metadata={"investor_profile": investor_profile}
        )
    
    @classmethod
    def create_roe(
        cls, 
        value: float,
        year: int = 1,
        benchmark_low: float = 0.05,
        benchmark_target: float = 0.10,
        benchmark_high: float = 0.15
    ) -> "MetricResult":
        """Create Return on Equity (ROE) metric result."""
        return cls(
            metric_type=MetricType.ROE,
            value=value,
            formatted_value=f"{value:.2%}",
            year=year,
            benchmark_low=benchmark_low,
            benchmark_target=benchmark_target,
            benchmark_high=benchmark_high,
        )
    
    @classmethod
    def create_average_roe(
        cls, 
        value: float,
        holding_period: int,
        benchmark_low: float = 0.08,
        benchmark_target: float = 0.12,
        benchmark_high: float = 0.18
    ) -> "MetricResult":
        """Create Average ROE metric result."""
        return cls(
            metric_type=MetricType.AVERAGE_ROE,
            value=value,
            formatted_value=f"{value:.2%}",
            holding_period=holding_period,
            benchmark_low=benchmark_low,
            benchmark_target=benchmark_target,
            benchmark_high=benchmark_high,
        )
    
    class Config:
        """Pydantic configuration."""
        
        use_enum_values = True
        validate_assignment = True 