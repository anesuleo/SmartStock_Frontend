import requests

BASE_URL = "http://localhost:8002"
class InventoryService:

    @staticmethod
    def list_items():
        res = requests.get(f"{BASE_URL}/api/inventory")
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_item(item_id: int):
        res = requests.get(f"{BASE_URL}/api/inventory/{item_id}")
        res.raise_for_status()
        return res.json()

    @staticmethod
    def create_item(data: dict):
        res = requests.post(f"{BASE_URL}/api/inventory", json=data)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def update_item(item_id: int, data: dict):
        res = requests.put(f"{BASE_URL}/api/inventory/{item_id}", json=data)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def patch_item(item_id: int, data: dict):
        res = requests.patch(f"{BASE_URL}/api/inventory/{item_id}", json=data)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def delete_item(item_id: int):
        res = requests.delete(f"{BASE_URL}/api/inventory/{item_id}")
        res.raise_for_status()
        return True
    
    @staticmethod
    def scan_barcode(code: str):
        res = requests.post(
            f"{BASE_URL}/api/inventory/scan",
            json={"barcode": code}
        )
        res.raise_for_status()
        return res.json()
