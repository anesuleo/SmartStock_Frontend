"""
ui/inventory_tab.py

Inventory tab for SmartStock GUI.
Contains two inner tabs:
  - Items: scrollable table with search, edit, delete and barcode scanning
  - Movements: stock movement history with filtering by type and date range
"""

import customtkinter as ctk
from datetime import datetime, date
from services.inventory_service import InventoryService
from services.barcode_service import BarcodeService


class InventoryTab:
    def __init__(self, parent):
        self.parent = parent
        self.all_items = []
        self.all_movements = []
        self.row_widgets = {}  # maps item_id -> (widgets, bg) for highlighting

        # ── Inner tab view ────────────────────────────────────────────────────
        # Two tabs inside the Inventory tab: Items and Movements
        self.tabview = ctk.CTkTabview(parent)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("Items")
        self.tabview.add("Movements")

        self._build_items_tab(self.tabview.tab("Items"))
        self._build_movements_tab(self.tabview.tab("Movements"))

        # ── Barcode service ───────────────────────────────────────────────────
        BarcodeService.register(self._on_barcode_scan)
        BarcodeService.register_status(self._on_scanner_status)

    # ══════════════════════════════════════════════════════════════════════════
    # ITEMS TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_items_tab(self, parent):
        """Build the Items tab with search, scanner status and table."""

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="Inventory Items",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        # Scanner status indicator
        self.scanner_label = ctk.CTkLabel(
            header,
            text="⬤ No Scanner",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        self.scanner_label.pack(side="right", padx=(0, 10))

        # Search box
        self.search_var = ctk.StringVar()
        ctk.CTkEntry(
            header,
            width=300,
            placeholder_text="Search by name or barcode...",
            textvariable=self.search_var
        ).pack(side="right", padx=(0, 10))

        # ── Items table ───────────────────────────────────────────────────────
        self.items_table = ctk.CTkScrollableFrame(parent)
        self.items_table.pack(fill="both", expand=True, padx=20, pady=10)

        headers = ["ID", "Drug", "Qty", "Price", "Barcode", "Edit", "Delete"]
        for col, h in enumerate(headers):
            ctk.CTkLabel(
                self.items_table,
                text=h,
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=col, padx=10, pady=6, sticky="ew")

        for col in range(len(headers)):
            self.items_table.grid_columnconfigure(col, weight=1)

        # Add search trace after everything is initialised
        self.search_var.trace_add("write", self._on_search)

        self.load_items()

    def load_items(self):
        """Fetch all inventory items from the API and render them."""
        try:
            self.all_items = InventoryService.list_items()
            self._render_items(self.all_items)
        except Exception as e:
            ctk.CTkLabel(
                self.items_table,
                text=f"Could not load inventory: {e}",
                text_color="red"
            ).grid(row=1, column=0, columnspan=7, pady=20)

    def _render_items(self, items):
        """
        Rebuild the items table from a list of items.
        Also rebuilds row_widgets map used for barcode scan highlighting.
        """
        # Clear all rows except header
        for widget in self.items_table.winfo_children():
            if int(widget.grid_info()["row"]) > 0:
                widget.destroy()

        self.row_widgets = {}

        for r, item in enumerate(items, start=1):
            bg = "#2b2b2b" if r % 2 == 0 else "#242424"
            widgets = []

            def cell(text, c, item_bg=bg):
                lbl = ctk.CTkLabel(
                    self.items_table,
                    text=text,
                    fg_color=item_bg,
                    corner_radius=6
                )
                lbl.grid(row=r, column=c, padx=6, pady=4, sticky="ew")
                widgets.append(lbl)
                return lbl

            cell(item["id"], 0)
            cell(item["drug_name"], 1)
            cell(item["stock_quantity"], 2)
            cell(f"${item['price']}", 3)
            cell(item["barcode"], 4)

            edit_btn = ctk.CTkButton(
                self.items_table,
                text="✏️",
                width=40,
                command=lambda i=item: self.open_edit_modal(i)
            )
            edit_btn.grid(row=r, column=5, padx=6)
            widgets.append(edit_btn)

            del_btn = ctk.CTkButton(
                self.items_table,
                text="🗑",
                width=40,
                fg_color="#d11a2a",
                hover_color="#a10f1c",
                command=lambda i=item["id"]: self._delete_item(i)
            )
            del_btn.grid(row=r, column=6, padx=6)
            widgets.append(del_btn)

            self.row_widgets[item["id"]] = (widgets, bg)

    def _on_search(self, *_):
        """Filter the items table as the user types."""
        q = self.search_var.get().lower()
        if not q:
            self._render_items(self.all_items)
            return
        filtered = [
            i for i in self.all_items
            if q in i["drug_name"].lower() or q in i["barcode"]
        ]
        self._render_items(filtered)

    def _delete_item(self, item_id):
        """Delete an item and refresh the table."""
        try:
            InventoryService.delete_item(item_id)
            self.load_items()
        except Exception as e:
            print(f"Failed to delete item {item_id}: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # MOVEMENTS TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_movements_tab(self, parent):
        """Build the Movements tab with filters and table."""

        # ── Filter bar ────────────────────────────────────────────────────────
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(10, 5))

        ctk.CTkLabel(
            filter_frame,
            text="Stock Movements",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        # Refresh button
        ctk.CTkButton(
            filter_frame,
            text="Load",
            width=70,
            command=self.load_movements
        ).pack(side="right", padx=4)

        # Movement type filter
        self.movement_type_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            filter_frame,
            values=["All", "IN", "OUT"],
            variable=self.movement_type_var,
            width=100,
            command=lambda _: self._apply_movement_filters()
        ).pack(side="right", padx=6)

        ctk.CTkLabel(filter_frame, text="Type:").pack(side="right")

        # Date range — To
        self.date_to_var = ctk.StringVar(
            value=date.today().strftime("%Y-%m-%d")
        )
        ctk.CTkEntry(
            filter_frame,
            width=110,
            textvariable=self.date_to_var,
            placeholder_text="To YYYY-MM-DD"
        ).pack(side="right", padx=(4, 0))
        ctk.CTkLabel(filter_frame, text="To:").pack(side="right", padx=(8, 0))

        # Date range — From
        self.date_from_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            filter_frame,
            width=110,
            textvariable=self.date_from_var,
            placeholder_text="From YYYY-MM-DD"
        ).pack(side="right", padx=(4, 0))
        ctk.CTkLabel(filter_frame, text="From:").pack(side="right", padx=(8, 0))

        # Search by drug name
        self.movement_search_var = ctk.StringVar()
        self.movement_search_var.trace_add("write", lambda *_: self._apply_movement_filters())
        ctk.CTkEntry(
            filter_frame,
            width=200,
            placeholder_text="Search by drug name...",
            textvariable=self.movement_search_var
        ).pack(side="right", padx=(0, 10))

        # Apply filters button for date range
        ctk.CTkButton(
            filter_frame,
            text="Apply",
            width=70,
            command=self._apply_movement_filters
        ).pack(side="right", padx=4)

        # ── Movements table ───────────────────────────────────────────────────
        self.movements_table = ctk.CTkScrollableFrame(parent)
        self.movements_table.pack(fill="both", expand=True, padx=20, pady=10)

        mov_headers = ["ID", "Item ID", "Drug Name", "Type", "Qty", "Date"]
        for col, h in enumerate(mov_headers):
            ctk.CTkLabel(
                self.movements_table,
                text=h,
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=col, padx=10, pady=6, sticky="ew")

        for col in range(len(mov_headers)):
            self.movements_table.grid_columnconfigure(col, weight=1)

    def load_movements(self):
        """Fetch all movements from the API and render them."""
        try:
            self.all_movements = InventoryService.list_movements()
            self._apply_movement_filters()
        except Exception as e:
            ctk.CTkLabel(
                self.movements_table,
                text=f"Could not load movements: {e}",
                text_color="red"
            ).grid(row=1, column=0, columnspan=6, pady=20)

    def _apply_movement_filters(self):
        """
        Apply all active filters to the movements list and re-render.
        Filters: drug name search, movement type, date range.
        """
        filtered = self.all_movements

        # Filter by drug name — look up item name from loaded items
        q = self.movement_search_var.get().lower()
        if q:
            # Build a quick lookup of item_id -> drug_name
            name_map = {str(i["id"]): i["drug_name"].lower() for i in self.all_items}
            filtered = [
                m for m in filtered
                if q in name_map.get(str(m["inventory_id"]), "")
            ]

        # Filter by movement type
        movement_type = self.movement_type_var.get()
        if movement_type != "All":
            filtered = [m for m in filtered if m["movement_type"] == movement_type]

        # Filter by date range
        date_from = self.date_from_var.get().strip()
        date_to = self.date_to_var.get().strip()

        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
                filtered = [
                    m for m in filtered
                    if datetime.strptime(m["movement_date"], "%Y-%m-%d").date() >= from_date
                ]
            except ValueError:
                pass  # ignore invalid date format

        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
                filtered = [
                    m for m in filtered
                    if datetime.strptime(m["movement_date"], "%Y-%m-%d").date() <= to_date
                ]
            except ValueError:
                pass

        self._render_movements(filtered)

    def _render_movements(self, movements):
        """Render a list of movements into the movements table."""
        # Clear all rows except header
        for widget in self.movements_table.winfo_children():
            if int(widget.grid_info()["row"]) > 0:
                widget.destroy()

        # Build item name lookup
        name_map = {str(i["id"]): i["drug_name"] for i in self.all_items}

        for r, m in enumerate(movements, start=1):
            bg = "#2b2b2b" if r % 2 == 0 else "#242424"

            # Colour code movement type — green for IN, red for OUT
            type_color = "#00d4aa" if m["movement_type"] == "IN" else "#f87171"

            def cell(text, c, colour=None):
                lbl = ctk.CTkLabel(
                    self.movements_table,
                    text=text,
                    fg_color=bg,
                    corner_radius=6,
                    text_color=colour if colour else "white"
                )
                lbl.grid(row=r, column=c, padx=6, pady=4, sticky="ew")

            cell(m["id"], 0)
            cell(m["inventory_id"], 1)
            cell(name_map.get(str(m["inventory_id"]), "Unknown"), 2)
            cell(m["movement_type"], 3, type_color)
            cell(m["quantity"], 4)
            cell(m["movement_date"], 5)

    # ══════════════════════════════════════════════════════════════════════════
    # BARCODE SCANNING
    # ══════════════════════════════════════════════════════════════════════════

    def _on_barcode_scan(self, barcode: str):
        """Called by BarcodeService on a background thread — schedule UI update."""
        self.parent.after(0, lambda: self._handle_scan(barcode))

    def _handle_scan(self, barcode: str):
        """
        Handle a scanned barcode on the Items tab.
        Highlights the matching row or opens the assign modal.
        """
        match = next(
            (item for item in self.all_items if item["barcode"] == barcode),
            None
        )
        if match:
            # Switch to the Items tab and highlight the row
            self.tabview.set("Items")
            self._highlight_item(match["id"])
        else:
            self.open_assign_barcode_modal(barcode)

    def _highlight_item(self, item_id: int):
        """Highlight a row green for 2 seconds then restore original colour."""
        if item_id not in self.row_widgets:
            return
        widgets, original_bg = self.row_widgets[item_id]
        for widget in widgets:
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(fg_color="#00d4aa")
        self.parent.after(
            2000,
            lambda: self._restore_highlight(item_id, original_bg)
        )

    def _restore_highlight(self, item_id: int, original_bg: str):
        """Restore a highlighted row to its original colour."""
        if item_id not in self.row_widgets:
            return
        widgets, _ = self.row_widgets[item_id]
        for widget in widgets:
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(fg_color=original_bg)

    def _on_scanner_status(self, connected: bool):
        """Update the scanner status label when connection state changes."""
        self.parent.after(0, lambda: self.scanner_label.configure(
            text="⬤ Scanner Connected" if connected else "⬤ No Scanner",
            text_color="#00d4aa" if connected else "gray"
        ))

    # ══════════════════════════════════════════════════════════════════════════
    # MODALS
    # ══════════════════════════════════════════════════════════════════════════

    def open_edit_modal(self, item):
        """Open a modal to edit an existing inventory item."""
        modal = ctk.CTkToplevel(self.parent)
        modal.title("Edit Inventory Item")
        modal.geometry("400x350")
        modal.grab_set()

        fields = {}

        def add_field(label, value):
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

    def open_assign_barcode_modal(self, barcode: str):
        """
        Opens when an unrecognised barcode is scanned.
        Lets the user assign the barcode to an existing inventory item.
        """
        modal = ctk.CTkToplevel(self.parent)
        modal.title("Assign Barcode")
        modal.geometry("420x280")
        modal.grab_set()

        ctk.CTkLabel(
            modal,
            text="Unrecognised Barcode",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            modal,
            text=f"Scanned: {barcode}",
            text_color="gray"
        ).pack(pady=(0, 16))

        ctk.CTkLabel(modal, text="Assign to item:").pack()

        item_options = [f"{i['id']}: {i['drug_name']}" for i in self.all_items]

        if not item_options:
            ctk.CTkLabel(modal, text="No items available.", text_color="red").pack()
            return

        selected_var = ctk.StringVar(value=item_options[0])
        ctk.CTkOptionMenu(
            modal,
            values=item_options,
            variable=selected_var,
            width=300
        ).pack(pady=10)

        def assign():
            try:
                item_id = int(selected_var.get().split(":")[0])
                InventoryService.patch_item(item_id, {"barcode": barcode})
                modal.destroy()
                self.load_items()
            except Exception as e:
                print(f"Failed to assign barcode: {e}")

        ctk.CTkButton(
            modal,
            text="Assign Barcode",
            command=assign
        ).pack(pady=10)

        ctk.CTkButton(
            modal,
            text="Cancel",
            fg_color="transparent",
            border_width=1,
            command=modal.destroy
        ).pack()