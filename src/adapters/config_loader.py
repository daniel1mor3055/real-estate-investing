"""Configuration loader for deal configurations."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_config_value(config_dict: Optional[Dict], key_path: str, default: Any = None) -> Any:
    """Get a value from nested config dictionary using dot notation.
    
    Args:
        config_dict: The configuration dictionary to search
        key_path: Dot-separated path to the value (e.g., 'property.address')
        default: Default value if path not found
        
    Returns:
        The value at the path, or default if not found
    """
    if config_dict is None:
        return default

    keys = key_path.split(".")
    value = config_dict

    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


class ConfigLoader:
    """Loads and manages deal configuration files."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the config loader.
        
        Args:
            config_dir: Directory containing config files. Defaults to deals/ folder.
        """
        self.config_dir = config_dir or Path.cwd() / "deals"
        self._config_files: Dict[str, Path] = {}
        self._refresh_config_list()

    def _refresh_config_list(self) -> None:
        """Scan config directory for JSON configuration files."""
        self._config_files = {}
        
        # Look for JSON files in the config directory
        for json_file in self.config_dir.glob("*.json"):
            # Use filename without extension as the config name
            name = json_file.stem.replace("_", " ").title()
            self._config_files[name] = json_file

    def list_available_configs(self) -> List[str]:
        """List available configuration names.
        
        Returns:
            List of configuration names
        """
        self._refresh_config_list()
        return list(self._config_files.keys())

    def load_configuration(self, config_name: str) -> Optional[Dict]:
        """Load a configuration file by name.
        
        Args:
            config_name: Name of the configuration to load
            
        Returns:
            Configuration dictionary or None if not found
        """
        # Handle manual input option
        if config_name in ["Manual", "None (Manual Input)"]:
            return None

        # Check if it's a known config
        if config_name in self._config_files:
            config_path = self._config_files[config_name]
        else:
            # Try to find by filename
            possible_path = self.config_dir / f"{config_name.lower().replace(' ', '_')}.json"
            if possible_path.exists():
                config_path = possible_path
            else:
                return None

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigLoadError(f"Error loading configuration '{config_name}': {e}")

    def save_configuration(self, config_name: str, config_data: Dict) -> Path:
        """Save a configuration to a file.
        
        Args:
            config_name: Name for the configuration
            config_data: Configuration dictionary to save
            
        Returns:
            Path to the saved file
        """
        filename = config_name.lower().replace(" ", "_") + ".json"
        config_path = self.config_dir / filename

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        self._refresh_config_list()
        return config_path

    def get_config_value(
        self, config: Optional[Dict], key_path: str, default: Any = None
    ) -> Any:
        """Get a value from a config dictionary using dot notation.
        
        Convenience method that wraps the module-level function.
        """
        return get_config_value(config, key_path, default)


class ConfigLoadError(Exception):
    """Raised when a configuration file cannot be loaded."""
    pass
