"""
services/inventory_service.py

Handles all communication between the GUI and the Inventory microservice.
"""

import requests

BASE_URL = "http://34.226.237.66:8002"


class InventoryService:

    @staticmethod
    def list_items():
        """Fetch all inventory items."""
        res = requests.get(f"{BASE_URL}/api/inventory")
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_item(item_id: int):
        """Fetch a single inventory item by ID."""
        res = requests.get(f"{BASE_URL}/api/inventory/{item_id}")
        res.raise_for_status()
        return res.json()

    @staticmethod
    def create_item(data: dict):
        """Create a new inventory item."""
        res = requests.post(f"{BASE_URL}/api/inventory", json=data)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def update_item(item_id: int, data: dict):
        """Fully replace an inventory item."""
        res = requests.put(f"{BASE_URL}/api/inventory/{item_id}", json=data)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def patch_item(item_id: int, data: dict):
        """Partially update an inventory item."""
        res = requests.patch(f"{BASE_URL}/api/inventory/{item_id}", json=data)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def delete_item(item_id: int):
        """Delete an inventory item."""
        res = requests.delete(f"{BASE_URL}/api/inventory/{item_id}")
        res.raise_for_status()
        return True

    @staticmethod
    def scan_barcode(code: str):
        """Look up an inventory item by barcode."""
        res = requests.post(
            f"{BASE_URL}/api/inventory/scan",
            json={"barcode": code}
        )
        res.raise_for_status()
        return res.json()

    @staticmethod
    def list_movements(limit: int = 500):
        """
        Fetch all stock movements (IN and OUT), most recent first.
        Used by the Movements tab to display history.
        """
        res = requests.get(
            f"{BASE_URL}/api/movements",
            params={"limit": limit}
        )
        res.raise_for_status()
        return res.json()