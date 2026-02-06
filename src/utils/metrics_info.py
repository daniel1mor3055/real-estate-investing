"""Utility module for loading and accessing metric definitions."""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from functools import lru_cache


class MetricInfo:
    """Information about a specific metric."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize metric info from dictionary data."""
        self.name = data.get("name", "")
        self.short_name = data.get("shortName", "")
        self.definition = data.get("definition", "")
        self.formula = data.get("formula", "")
        self.includes = data.get("includes", [])
        self.excludes = data.get("excludes", [])
        self.higher_is_better = data.get("higherIsBetter", True)
        self.benchmarks = data.get("benchmarks")
        self.category = data.get("category", "")
        self.tooltip_text = data.get("tooltipText", "")
        self.note = data.get("note", "")
        self.interpretation = data.get("interpretation", {})
    
    def get_tooltip_html(self) -> str:
        """Generate HTML for tooltip display."""
        html_parts = [f"<div style='padding: 10px;'>"]
        
        # Title
        html_parts.append(f"<h4 style='margin-top: 0;'>{self.name}</h4>")
        
        # Definition
        html_parts.append(f"<p><strong>What it means:</strong> {self.tooltip_text}</p>")
        
        # Formula
        if self.formula:
            html_parts.append(f"<p><strong>Formula:</strong> <code>{self.formula}</code></p>")
        
        # Includes/Excludes for ambiguous metrics
        if self.includes:
            includes_str = ", ".join(self.includes)
            html_parts.append(f"<p><strong>Includes:</strong> {includes_str}</p>")
        
        if self.excludes:
            excludes_str = ", ".join(self.excludes)
            html_parts.append(f"<p><strong>Excludes:</strong> {excludes_str}</p>")
        
        # Note
        if self.note:
            html_parts.append(f"<p><em>Note: {self.note}</em></p>")
        
        html_parts.append("</div>")
        return "".join(html_parts)
    
    def get_performance_indicator(self, value: float) -> tuple[str, str]:
        """Get color and label for a metric value based on benchmarks.
        
        Returns:
            Tuple of (color, label) where color is CSS color and label is performance text
        """
        if self.benchmarks is None:
            return "gray", "N/A"
        
        low = self.benchmarks.get("low")
        target = self.benchmarks.get("target")
        high = self.benchmarks.get("high")
        
        if low is None or target is None or high is None:
            return "gray", "N/A"
        
        if self.higher_is_better:
            if value >= high:
                return "green", "Excellent"
            elif value >= target:
                return "lightgreen", "Good"
            elif value >= low:
                return "orange", "Fair"
            else:
                return "red", "Poor"
        else:  # Lower is better
            if value <= low:
                return "green", "Excellent"
            elif value <= target:
                return "lightgreen", "Good"
            elif value <= high:
                return "orange", "Fair"
            else:
                return "red", "Poor"


@lru_cache(maxsize=1)
def load_metrics_definitions() -> Dict[str, MetricInfo]:
    """Load metric definitions from JSON config file.
    
    Returns:
        Dictionary mapping metric type keys to MetricInfo objects
    """
    config_path = Path(__file__).parent.parent / "config" / "metrics_definitions.json"
    
    if not config_path.exists():
        return {}
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return {key: MetricInfo(value) for key, value in data.items()}


def get_metric_info(metric_type: str) -> Optional[MetricInfo]:
    """Get information for a specific metric type.
    
    Args:
        metric_type: The metric type (e.g., 'NOI', 'CAP_RATE', 'DSCR')
        
    Returns:
        MetricInfo object or None if not found
    """
    definitions = load_metrics_definitions()
    # Normalize the metric type key
    key = metric_type.upper().replace(" ", "_")
    return definitions.get(key)


def get_tooltip_for_metric(metric_type: str) -> str:
    """Get tooltip text for a metric type.
    
    Args:
        metric_type: The metric type (e.g., 'noi', 'cap_rate', 'dscr')
        
    Returns:
        Tooltip text or empty string if not found
    """
    info = get_metric_info(metric_type)
    return info.tooltip_text if info else ""
