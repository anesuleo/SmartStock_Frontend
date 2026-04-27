import customtkinter as ctk
import threading

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.inventory_service import InventoryService

# ── Colour palette (matches forecast_tab.py) ────────────────────────
BG      = "#0f1117"
PANEL   = "#1a1d27"
ACCENT  = "#00d4aa"
ACCENT2 = "#7c6af7"
TEXT    = "#e8eaf0"
SUBTEXT = "#6b7280"
DANGER  = "#f87171"
WARNING = "#fbbf24"

LOW_STOCK_THRESHOLD = 50


class MetricsTab:
    def __init__(self, parent):
        self.parent = parent
        self.canvas_widget = None

        parent.configure(fg_color=BG)

        # ── Top bar ─────────────────────────────────────────────────
        topbar = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=12, height=70)
        topbar.pack(fill="x", padx=20, pady=(20, 0))
        topbar.pack_propagate(False)

        ctk.CTkLabel(
            topbar,
            text="Inventory Metrics",
            font=ctk.CTkFont(family="Courier New", size=22, weight="bold"),
            text_color=ACCENT
        ).pack(side="left", padx=20, pady=15)

        self.refresh_btn = ctk.CTkButton(
            topbar,
            text="Refresh",
            width=120, height=36,
            fg_color=ACCENT, hover_color="#00b894",
            text_color="#000000",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            command=self.load_threaded
        )
        self.refresh_btn.pack(side="right", padx=15, pady=15)

        # ── Summary cards row ────────────────────────────────────────
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=(14, 0))

        self.card_items     = self._make_card(cards_frame, "Total Items",    "—", ACCENT)
        self.card_stock     = self._make_card(cards_frame, "Total Stock",    "—", ACCENT2)
        self.card_value     = self._make_card(cards_frame, "Portfolio Value","—", WARNING)
        self.card_low_stock = self._make_card(cards_frame, "Low Stock Items","—", DANGER)

        for card in (self.card_items, self.card_stock, self.card_value, self.card_low_stock):
            card.pack(side="left", expand=True, fill="x", padx=6)

        # ── Chart area ───────────────────────────────────────────────
        self.chart_frame = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=12)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=14)

        self.placeholder = ctk.CTkLabel(
            self.chart_frame,
            text="Click  Refresh  to load inventory charts",
            font=ctk.CTkFont(family="Courier New", size=14),
            text_color=SUBTEXT
        )
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # ── Status bar ───────────────────────────────────────────────
        self.status_var = ctk.StringVar(value="Ready")
        ctk.CTkLabel(
            parent, textvariable=self.status_var,
            text_color=SUBTEXT, font=ctk.CTkFont(size=11)
        ).pack(pady=(0, 8))

    # ── Card factory ─────────────────────────────────────────────────
    def _make_card(self, parent, title, value, accent):
        frame = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=10)
        ctk.CTkLabel(frame, text=title, text_color=SUBTEXT,
                     font=ctk.CTkFont(size=11)).pack(pady=(12, 2))
        val_label = ctk.CTkLabel(frame, text=value, text_color=accent,
                                 font=ctk.CTkFont(family="Courier New", size=22, weight="bold"))
        val_label.pack(pady=(0, 12))
        frame._val_label = val_label
        return frame

    def _update_card(self, card, value, color=None):
        card._val_label.configure(text=value)
        if color:
            card._val_label.configure(text_color=color)

    # ── Load logic ───────────────────────────────────────────────────
    def load_threaded(self):
        self.refresh_btn.configure(state="disabled", text="Loading...")
        self.status_var.set("Fetching inventory data…")
        threading.Thread(target=self._fetch_and_draw, daemon=True).start()

    def _fetch_and_draw(self):
        try:
            items = InventoryService.list_items()
            self.parent.after(0, lambda: self._draw_dashboard(items))
        except Exception as e:
            self.parent.after(0, lambda: self.status_var.set(
                f"✗  Could not reach inventory service: {e}"))
        finally:
            self.parent.after(0, lambda: self.refresh_btn.configure(
                state="normal", text="Refresh"))

    # ── Chart drawing ────────────────────────────────────────────────
    def _draw_dashboard(self, items):
        if not items:
            self.status_var.set("No inventory data found.")
            return

        names     = [i["drug_name"]      for i in items]
        quantities= [i["stock_quantity"] for i in items]
        prices    = [float(i["price"])   for i in items]
        values    = [q * p for q, p in zip(quantities, prices)]
        low_items = [i for i in items if i["stock_quantity"] < LOW_STOCK_THRESHOLD]

        # ── Summary cards ────────────────────────────────────────────
        total_items = len(items)
        total_stock = sum(quantities)
        total_value = sum(values)
        low_count   = len(low_items)

        self._update_card(self.card_items,     str(total_items))
        self._update_card(self.card_stock,     f"{total_stock:,} units")
        self._update_card(self.card_value,     f"${total_value:,.2f}")
        self._update_card(
            self.card_low_stock,
            str(low_count),
            DANGER if low_count > 0 else ACCENT
        )

        # ── Sort helpers for top-N ────────────────────────────────────
        top_n = 10
        by_qty   = sorted(zip(quantities, names), reverse=True)[:top_n]
        by_value = sorted(zip(values,    names), reverse=True)[:top_n]

        qty_vals,   qty_names   = zip(*by_qty)   if by_qty   else ([], [])
        val_vals,   val_names   = zip(*by_value) if by_value else ([], [])

        low_names = [i["drug_name"]      for i in low_items]
        low_qtys  = [i["stock_quantity"] for i in low_items]

        # ── Build 2×2 figure ─────────────────────────────────────────
        fig, axes = plt.subplots(2, 2, figsize=(13, 7), facecolor=BG)
        fig.subplots_adjust(hspace=0.48, wspace=0.38)

        ax1, ax2, ax3, ax4 = axes.flat

        # ── Chart 1: Top items by stock quantity (horizontal bar) ────
        self._style_ax(ax1)
        bars1 = ax1.barh(list(qty_names), list(qty_vals),
                         color=ACCENT, height=0.6)
        ax1.invert_yaxis()
        ax1.set_title("Top Items by Stock Quantity",
                      color=TEXT, fontsize=11, fontweight="bold",
                      fontfamily="monospace", pad=10)
        ax1.set_xlabel("Units", color=SUBTEXT, fontsize=9)
        self._bar_labels(ax1, bars1, ACCENT, fmt="{:.0f}")

        # ── Chart 2: Top items by stock value (horizontal bar) ───────
        self._style_ax(ax2)
        bars2 = ax2.barh(list(val_names), list(val_vals),
                         color=ACCENT2, height=0.6)
        ax2.invert_yaxis()
        ax2.set_title("Top Items by Stock Value",
                      color=TEXT, fontsize=11, fontweight="bold",
                      fontfamily="monospace", pad=10)
        ax2.set_xlabel("Value ($)", color=SUBTEXT, fontsize=9)
        self._bar_labels(ax2, bars2, ACCENT2, fmt="${:.0f}")

        # ── Chart 3: Low stock items ──────────────────────────────────
        self._style_ax(ax3)
        if low_names:
            bar_colors = [DANGER if q == 0 else WARNING for q in low_qtys]
            bars3 = ax3.bar(low_names, low_qtys, color=bar_colors, width=0.6)
            ax3.set_title(
                f"Low Stock Items  (<{LOW_STOCK_THRESHOLD} units)",
                color=TEXT, fontsize=11, fontweight="bold",
                fontfamily="monospace", pad=10
            )
            ax3.set_ylabel("Units", color=SUBTEXT, fontsize=9)
            plt.setp(ax3.xaxis.get_majorticklabels(),
                     rotation=30, ha="right", color=SUBTEXT, fontsize=8)
            self._bar_labels(ax3, bars3, WARNING, fmt="{:.0f}", vertical=True)
        else:
            ax3.text(0.5, 0.5, "All items sufficiently stocked",
                     ha="center", va="center", color=ACCENT,
                     fontsize=10, fontfamily="monospace",
                     transform=ax3.transAxes)
            ax3.set_title(
                f"Low Stock Items  (<{LOW_STOCK_THRESHOLD} units)",
                color=TEXT, fontsize=11, fontweight="bold",
                fontfamily="monospace", pad=10
            )

        # ── Chart 4: Price distribution (sorted bar) ─────────────────
        self._style_ax(ax4)
        sorted_pairs = sorted(zip(prices, names))
        s_prices, s_names = zip(*sorted_pairs) if sorted_pairs else ([], [])
        norm_prices = [p / max(s_prices) for p in s_prices] if s_prices else []
        bar_cols = [
            plt.cm.RdYlGn(v * 0.8 + 0.1) for v in norm_prices
        ]
        bars4 = ax4.bar(list(s_names), list(s_prices),
                        color=bar_cols, width=0.6)
        ax4.set_title("Price per Item",
                      color=TEXT, fontsize=11, fontweight="bold",
                      fontfamily="monospace", pad=10)
        ax4.set_ylabel("Price ($)", color=SUBTEXT, fontsize=9)
        plt.setp(ax4.xaxis.get_majorticklabels(),
                 rotation=30, ha="right", color=SUBTEXT, fontsize=8)
        self._bar_labels(ax4, bars4, TEXT, fmt="${:.2f}", vertical=True)

        # ── Embed in CTk ─────────────────────────────────────────────
        if self.canvas_widget:
            self.canvas_widget.get_tk_widget().destroy()

        self.placeholder.place_forget()

        self.canvas_widget = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas_widget.draw()
        self.canvas_widget.get_tk_widget().pack(fill="both", expand=True,
                                                padx=8, pady=8)
        plt.close(fig)

        self.status_var.set(
            f"✓  {total_items} items loaded  ·  "
            f"Total stock: {total_stock:,} units  ·  "
            f"Portfolio value: ${total_value:,.2f}  ·  "
            f"Low stock: {low_count}"
        )

    # ── Helpers ──────────────────────────────────────────────────────
    def _style_ax(self, ax):
        ax.set_facecolor(PANEL)
        ax.grid(axis="both", color="#2a2d3a", linewidth=0.6, linestyle="--")
        for spine in ax.spines.values():
            spine.set_color("#2a2d3a")
        ax.tick_params(colors=SUBTEXT, labelsize=8)
        ax.xaxis.label.set_color(SUBTEXT)
        ax.yaxis.label.set_color(SUBTEXT)

    def _bar_labels(self, ax, bars, color, fmt="{:.0f}", vertical=False):
        for bar in bars:
            if vertical:
                w = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    w + max(b.get_height() for b in bars) * 0.02,
                    fmt.format(w),
                    ha="center", va="bottom",
                    color=color, fontsize=7, fontweight="bold"
                )
            else:
                w = bar.get_width()
                ax.text(
                    w + max(b.get_width() for b in bars) * 0.02,
                    bar.get_y() + bar.get_height() / 2,
                    fmt.format(w),
                    ha="left", va="center",
                    color=color, fontsize=7, fontweight="bold"
                )
