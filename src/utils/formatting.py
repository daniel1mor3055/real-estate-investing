"""Formatting utilities for display."""

from typing import Union


def format_currency(value: Union[int, float], decimals: int = 0) -> str:
    """
    Format a number as currency.
    
    Args:
        value: The numeric value to format
        decimals: Number of decimal places
    
    Returns:
        Formatted currency string
    """
    if decimals == 0:
        return f"${value:,.0f}"
    else:
        return f"${value:,.{decimals}f}"


def format_percentage(value: Union[int, float], decimals: int = 2) -> str:
    """
    Format a number as percentage.
    
    Args:
        value: The numeric value to format (0.1 = 10%)
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}%}"


def format_number(value: Union[int, float], decimals: int = 2) -> str:
    """
    Format a number with thousands separator.
    
    Args:
        value: The numeric value to format
        decimals: Number of decimal places
    
    Returns:
        Formatted number string
    """
    if decimals == 0:
        return f"{value:,.0f}"
    else:
        return f"{value:,.{decimals}f}"


def format_ratio(value: Union[int, float], decimals: int = 2) -> str:
    """
    Format a ratio (like DSCR).
    
    Args:
        value: The ratio value
        decimals: Number of decimal places
    
    Returns:
        Formatted ratio string
    """
    return f"{value:.{decimals}f}x" 