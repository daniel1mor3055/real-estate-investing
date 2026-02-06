"""Deal repository for persistence operations."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from abc import ABC, abstractmethod


class DealRepository(ABC):
    """Abstract base class for deal persistence."""

    @abstractmethod
    def save(self, deal_id: str, deal_data: Dict) -> None:
        """Save a deal to the repository."""
        pass

    @abstractmethod
    def load(self, deal_id: str) -> Optional[Dict]:
        """Load a deal from the repository."""
        pass

    @abstractmethod
    def list_all(self) -> List[str]:
        """List all deal IDs in the repository."""
        pass

    @abstractmethod
    def delete(self, deal_id: str) -> bool:
        """Delete a deal from the repository."""
        pass

    @abstractmethod
    def exists(self, deal_id: str) -> bool:
        """Check if a deal exists in the repository."""
        pass


class JsonFileRepository(DealRepository):
    """File-based JSON repository for deal persistence."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize the repository.
        
        Args:
            storage_dir: Directory to store deal files. Defaults to ./deals/
        """
        self.storage_dir = storage_dir or Path.cwd() / "deals"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, deal_id: str) -> Path:
        """Get the file path for a deal ID."""
        # Sanitize deal_id for use as filename
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in deal_id)
        return self.storage_dir / f"{safe_id}.json"

    def save(self, deal_id: str, deal_data: Dict) -> None:
        """Save a deal to a JSON file.
        
        Args:
            deal_id: Unique identifier for the deal
            deal_data: Deal data dictionary to save
        """
        file_path = self._get_file_path(deal_id)
        
        # Add metadata
        data_with_meta = {
            "_metadata": {
                "deal_id": deal_id,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0",
            },
            **deal_data,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_with_meta, f, indent=2, default=str)

    def load(self, deal_id: str) -> Optional[Dict]:
        """Load a deal from a JSON file.
        
        Args:
            deal_id: Unique identifier for the deal
            
        Returns:
            Deal data dictionary or None if not found
        """
        file_path = self._get_file_path(deal_id)

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Remove metadata before returning
                data.pop("_metadata", None)
                return data
        except (json.JSONDecodeError, IOError):
            return None

    def list_all(self) -> List[str]:
        """List all deal IDs in the repository.
        
        Returns:
            List of deal IDs
        """
        deal_ids = []
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "_metadata" in data and "deal_id" in data["_metadata"]:
                        deal_ids.append(data["_metadata"]["deal_id"])
                    else:
                        deal_ids.append(file_path.stem)
            except (json.JSONDecodeError, IOError):
                continue
        return deal_ids

    def delete(self, deal_id: str) -> bool:
        """Delete a deal from the repository.
        
        Args:
            deal_id: Unique identifier for the deal
            
        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_file_path(deal_id)

        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def exists(self, deal_id: str) -> bool:
        """Check if a deal exists in the repository.
        
        Args:
            deal_id: Unique identifier for the deal
            
        Returns:
            True if exists, False otherwise
        """
        return self._get_file_path(deal_id).exists()


class InMemoryRepository(DealRepository):
    """In-memory repository for testing and temporary storage."""

    def __init__(self):
        """Initialize the in-memory repository."""
        self._storage: Dict[str, Dict] = {}

    def save(self, deal_id: str, deal_data: Dict) -> None:
        """Save a deal to memory."""
        self._storage[deal_id] = deal_data.copy()

    def load(self, deal_id: str) -> Optional[Dict]:
        """Load a deal from memory."""
        if deal_id in self._storage:
            return self._storage[deal_id].copy()
        return None

    def list_all(self) -> List[str]:
        """List all deal IDs in memory."""
        return list(self._storage.keys())

    def delete(self, deal_id: str) -> bool:
        """Delete a deal from memory."""
        if deal_id in self._storage:
            del self._storage[deal_id]
            return True
        return False

    def exists(self, deal_id: str) -> bool:
        """Check if a deal exists in memory."""
        return deal_id in self._storage

    def clear(self) -> None:
        """Clear all deals from memory."""
        self._storage.clear()
