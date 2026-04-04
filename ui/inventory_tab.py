import customtkinter as ctk
from services.inventory_service import InventoryService


class InventoryTab:
    def __init__(self, parent):
        self.parent = parent
        self.all_items = []

        # ── Header ────────────────────────────────────────────────────────────
        # Contains the title on the left and search box on the right
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="Inventory",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(side="left")

        # Search variable — trace is added later after all methods are ready
        self.search_var = ctk.StringVar()

        ctk.CTkEntry(
            header,
            width=350,
            placeholder_text="Search inventory...",
            textvariable=self.search_var
        ).pack(side="right")

        # ── Table ─────────────────────────────────────────────────────────────
        # Scrollable frame that holds the column headers and item rows
        self.table = ctk.CTkScrollableFrame(parent)
        self.table.pack(fill="both", expand=True, padx=20, pady=10)

        self.headers = ["ID", "Drug", "Qty", "Price", "Barcode", "Edit", "Delete"]

        # Render column headers in row 0
        for col, h in enumerate(self.headers):
            ctk.CTkLabel(
                self.table,
                text=h,
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=col, padx=10, pady=6, sticky="ew")

        # Make all columns expand evenly
        for col in range(len(self.headers)):
            self.table.grid_columnconfigure(col, weight=1)

        # Now that all methods exist, attach the search listener
        self.search_var.trace_add("write", self.on_search)

        # Load inventory data — errors are handled gracefully inside load_items
        self.load_items()

    # ── Data ──────────────────────────────────────────────────────────────────

    def load_items(self):
        """
        Fetch all inventory items from the API and render them.
        If the service is unreachable, show an error message instead of crashing.
        """
        try:
            self.all_items = InventoryService.list_items()
            self.render(self.all_items)
        except Exception as e:
            # Display the error inside the table area so the app stays open
            ctk.CTkLabel(
                self.table,
                text=f"Could not load inventory: {e}",
                text_color="red"
            ).grid(row=1, column=0, columnspan=7, pady=20)

    def render(self, items):
        """
        Render a list of inventory items into the table.
        Clears all existing rows first, then rebuilds from scratch.
        """
        # Remove all rows except the header (row 0)
        for widget in self.table.winfo_children():
            if int(widget.grid_info()["row"]) > 0:
                widget.destroy()

        for r, item in enumerate(items, start=1):
            # Alternate row background colours for readability
            bg = "#2b2b2b" if r % 2 == 0 else "#242424"

            def cell(text, c):
                """Helper to create a single table cell."""
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

            # Edit button — opens a modal to edit the item
            ctk.CTkButton(
                self.table,
                text="✏️",
                width=40,
                command=lambda i=item: self.open_edit_modal(i)
            ).grid(row=r, column=5, padx=6)

            # Delete button — deletes the item and refreshes the table
            ctk.CTkButton(
                self.table,
                text="🗑",
                width=40,
                fg_color="#d11a2a",
                hover_color="#a10f1c",
                command=lambda i=item["id"]: self.delete_item(i)
            ).grid(row=r, column=6, padx=6)

    # ── Search ────────────────────────────────────────────────────────────────

    def on_search(self, *_):
        """
        Called every time the search box changes.
        Filters the already-loaded items by drug name or barcode.
        """
        q = self.search_var.get().lower()

        if not q:
            # Empty search — show everything
            self.render(self.all_items)
            return

        filtered = [
            i for i in self.all_items
            if q in i["drug_name"].lower() or q in i["barcode"]
        ]
        self.render(filtered)

    # ── Actions ───────────────────────────────────────────────────────────────

    def delete_item(self, item_id):
        """Delete an item by ID and refresh the table."""
        try:
            InventoryService.delete_item(item_id)
            self.load_items()
        except Exception as e:
            print(f"Failed to delete item {item_id}: {e}")

    # ── Edit Modal ────────────────────────────────────────────────────────────

    def open_edit_modal(self, item):
        """
        Opens a popup window to edit an inventory item.
        Pre-fills all fields with the current values.
        """
        modal = ctk.CTkToplevel(self.parent)
        modal.title("Edit Inventory Item")
        modal.geometry("400x350")
        modal.grab_set()  # block interaction with the main window while open

        fields = {}

        def add_field(label, value):
            """Helper to add a labelled input field to the modal."""
            ctk.CTkLabel(modal, text=label).pack(pady=(10, 0))
            entry = ctk.CTkEntry(modal)
            entry.insert(0, value)
            entry.pack(fill="x", padx=20)
            fields[label] = entry

        add_field("Drug Name", item["drug_name"])
        add_field("Stock Quantity", item["stock_quantity"])
        add_field("Price", item["price"])
        add_field("Barcode", item["barcode"])

        def save():
            """Read the fields, send a PATCH request, and close the modal."""
            try:
                payload = {
                    "drug_name": fields["Drug Name"].get(),
                    "stock_quantity": int(fields["Stock Quantity"].get()),
                    "price": float(fields["Price"].get()),
                    "barcode": fields["Barcode"].get(),
                }
                InventoryService.patch_item(item["id"], payload)
                modal.destroy()
                self.load_items()
            except Exception as e:
                print(f"Failed to save item: {e}")

        ctk.CTkButton(modal, text="Save Changes", command=save).pack(pady=20)