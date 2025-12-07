import customtkinter as ctk
from services.inventory_service import InventoryService

class InventoryTab:
    def __init__(self, parent):
        self.parent = parent

        title = ctk.CTkLabel(parent, text="Inventory", font=ctk.CTkFont(size=24))
        title.pack(pady=20)

        load_btn = ctk.CTkButton(parent, text="Load Inventory", command=self.load_items)
        load_btn.pack(pady=10)

        self.box = ctk.CTkTextbox(parent, width=700, height=400)
        self.box.pack(pady=20)

    def load_items(self):
        try:
            items = InventoryService.list_items()
        except Exception as e:
            self.box.insert("end", f"Error: {e}\n")
            return
        
        self.box.delete("1.0", "end")

        for item in items:
            line = (
                        f"{item['id']} | "
                        f"{item['drug_name']} | "
                        f"Qty: {item['stock_quantity']} | "
                        f"Price: {item['price']} | "
                        f"Barcode: {item['barcode']}\n"
                    )
            self.box.insert("end", line)