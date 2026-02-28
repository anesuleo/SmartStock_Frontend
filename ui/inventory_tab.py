import customtkinter as ctk
from services.inventory_service import InventoryService


class InventoryTab:
    def __init__(self, parent):
        self.parent = parent
        self.all_items = []

        # ================= Header =================
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="Inventory",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(side="left")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.on_search)

        ctk.CTkEntry(
            header,
            width=350,
            placeholder_text="Search inventory...",
            textvariable=self.search_var
        ).pack(side="right")

        # ================= Table =================
        self.table = ctk.CTkScrollableFrame(parent)
        self.table.pack(fill="both", expand=True, padx=20, pady=10)

        self.headers = ["ID", "Drug", "Qty", "Price", "Barcode", "Edit", "Delete"]
        for col, h in enumerate(self.headers):
            ctk.CTkLabel(
                self.table,
                text=h,
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=col, padx=10, pady=6, sticky="ew")

        for col in range(len(self.headers)):
            self.table.grid_columnconfigure(col, weight=1)

        self.load_items()

    # ================= Data =================
    def load_items(self):
        self.all_items = InventoryService.list_items()
        self.render(self.all_items)

    def render(self, items):
        for w in self.table.winfo_children():
            if int(w.grid_info()["row"]) > 0:
                w.destroy()

        for r, item in enumerate(items, start=1):
            bg = "#2b2b2b" if r % 2 == 0 else "#242424"

            def cell(text, c):
                ctk.CTkLabel(
                    self.table,
                    text=text,
                    fg_color=bg,
                    corner_radius=6
                ).grid(row=r, column=c, padx=6, pady=4, sticky="ew")

            cell(item["id"], 0)
            cell(item["drug_name"], 1)
            cell(item["stock_quantity"], 2)
            cell(f"${item['price']}", 3)
            cell(item["barcode"], 4)

            # ✏️ EDIT
            ctk.CTkButton(
                self.table,
                text="✏️",
                width=40,
                command=lambda i=item: self.open_edit_modal(i)
            ).grid(row=r, column=5, padx=6)

            # 🗑 DELETE
            ctk.CTkButton(
                self.table,
                text="🗑",
                width=40,
                fg_color="#d11a2a",
                hover_color="#a10f1c",
                command=lambda i=item["id"]: self.delete_item(i)
            ).grid(row=r, column=6, padx=6)

    # ================= Search =================
    def on_search(self, *_):
        q = self.search_var.get().lower()
        if not q:
            self.render(self.all_items)
            return

        self.render([
            i for i in self.all_items
            if q in i["drug_name"].lower()
            or q in i["barcode"]
        ])

    # ================= Actions =================
    def delete_item(self, item_id):
        InventoryService.delete_item(item_id)
        self.load_items()

    # ================= Edit Modal =================
    def open_edit_modal(self, item):
        modal = ctk.CTkToplevel(self.parent)
        modal.title("Edit Inventory Item")
        modal.geometry("400x350")
        modal.grab_set()

        fields = {}

        def add_field(label, value):
            ctk.CTkLabel(modal, text=label).pack(pady=(10, 0))
            e = ctk.CTkEntry(modal)
            e.insert(0, value)
            e.pack(fill="x", padx=20)
            fields[label] = e

        add_field("Drug Name", item["drug_name"])
        add_field("Stock Quantity", item["stock_quantity"])
        add_field("Price", item["price"])
        add_field("Barcode", item["barcode"])

        def save():
            payload = {
                "drug_name": fields["Drug Name"].get(),
                "stock_quantity": int(fields["Stock Quantity"].get()),
                "price": float(fields["Price"].get()),
                "barcode": fields["Barcode"].get(),
            }
            InventoryService.patch_item(item["id"], payload)
            modal.destroy()
            self.load_items()

        ctk.CTkButton(modal, text="Save Changes", command=save).pack(pady=20)
