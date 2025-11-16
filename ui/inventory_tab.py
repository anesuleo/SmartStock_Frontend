import customtkinter as ctk

class InventoryTab:
    def __init__(self, parent):
        self.parent = parent

        label = ctk.CTkLabel(parent, text="Inventory Page")
        label.pack(pady=20)