"""Base calculator abstract class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar

from pydantic import BaseModel

from ..models.deal import Deal

T = TypeVar('T', bound=BaseModel)


class CalculatorResult(BaseModel, Generic[T]):
    """Generic result container for calculator outputs."""
    
    success: bool = True
    data: T
    errors: list[str] = []
    warnings: list[str] = []
    metadata: Dict[str, Any] = {}


class Calculator(ABC):
    """Abstract base class for all calculators."""
    
    def __init__(self, deal: Deal):
        """Initialize calculator with a deal."""
        self.deal = deal
    
    @abstractmethod
    def calculate(self, **kwargs) -> CalculatorResult:
        """Perform the calculation and return results."""
        pass
    
    def validate_inputs(self) -> list[str]:
        """Validate inputs before calculation."""
        errors = []
        
        # Basic validation that all calculators need
        if not self.deal:
            errors.append("No deal provided")
        
        return errors 