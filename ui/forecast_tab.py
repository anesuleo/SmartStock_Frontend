import customtkinter as ctk
import requests
import threading
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe

FORECASTING_URL = "http://localhost:8003"
INVENTORY_URL   = "http://localhost:8002"

# ── Colour palette ──────────────────────────────────────────────────
BG        = "#0f1117"
PANEL     = "#1a1d27"
ACCENT    = "#00d4aa"
ACCENT2   = "#7c6af7"
TEXT      = "#e8eaf0"
SUBTEXT   = "#6b7280"
DANGER    = "#f87171"
WARNING   = "#fbbf24"


class ForecastTab:
    def __init__(self, parent):
        self.parent = parent
        self.canvas_widget = None
        self.current_item_id = None

        parent.configure(fg_color=BG)

        # ── Top bar ─────────────────────────────────────────────────
        topbar = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=12, height=70)
        topbar.pack(fill="x", padx=20, pady=(20, 0))
        topbar.pack_propagate(False)

        ctk.CTkLabel(
            topbar,
            text="Demand Forecast",
            font=ctk.CTkFont(family="Courier New", size=22, weight="bold"),
            text_color=ACCENT
        ).pack(side="left", padx=20, pady=15)

        # Controls on the right
        controls = ctk.CTkFrame(topbar, fg_color="transparent")
        controls.pack(side="right", padx=15, pady=10)

        # Item ID entry
        ctk.CTkLabel(controls, text="Item ID", text_color=SUBTEXT,
                     font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=(0,4))
        self.item_entry = ctk.CTkEntry(
            controls, width=80, height=36,
            placeholder_text="e.g. 1",
            fg_color="#252836", border_color=ACCENT2, text_color=TEXT,
            corner_radius=8
        )
        self.item_entry.grid(row=0, column=1, padx=(0, 12))

        # Horizon selector
        ctk.CTkLabel(controls, text="Horizon", text_color=SUBTEXT,
                     font=ctk.CTkFont(size=11)).grid(row=0, column=2, padx=(0,4))
        self.horizon_var = ctk.StringVar(value="30")
        self.horizon_menu = ctk.CTkOptionMenu(
            controls,
            values=["7", "14", "30", "60", "90"],
            variable=self.horizon_var,
            width=80, height=36,
            fg_color="#252836", button_color=ACCENT2,
            text_color=TEXT, corner_radius=8
        )
        self.horizon_menu.grid(row=0, column=3, padx=(0, 12))

        # Forecast button
        self.forecast_btn = ctk.CTkButton(
            controls,
            text="Run Forecast",
            width=130, height=36,
            fg_color=ACCENT, hover_color="#00b894",
            text_color="#000000",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            command=self.run_forecast_threaded
        )
        self.forecast_btn.grid(row=0, column=4)

        # ── Summary cards row ────────────────────────────────────────
        self.cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=20, pady=(14, 0))

        self.card_total   = self._make_card(self.cards_frame, "Total Predicted",  "—", ACCENT)
        self.card_avg     = self._make_card(self.cards_frame, "Daily Average",    "—", ACCENT2)
        self.card_peak    = self._make_card(self.cards_frame, "Peak Day",         "—", WARNING)
        self.card_reorder = self._make_card(self.cards_frame, "Reorder Alert",    "—", DANGER)

        for card in (self.card_total, self.card_avg, self.card_peak, self.card_reorder):
            card.pack(side="left", expand=True, fill="x", padx=6)

        # ── Chart area ───────────────────────────────────────────────
        self.chart_frame = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=12)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=14)

        self.placeholder = ctk.CTkLabel(
            self.chart_frame,
            text="Enter an Item ID and click  Run Forecast  to visualise demand",
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
        frame._val_label = val_label   # keep reference for updates
        return frame

    def _update_card(self, card, value):
        card._val_label.configure(text=value)

    # ── Forecast logic ───────────────────────────────────────────────
    def run_forecast_threaded(self):
        """Run in a thread so the UI doesn't freeze during the API call."""
        item_id_str = self.item_entry.get().strip()
        if not item_id_str.isdigit():
            self.status_var.set("⚠  Please enter a valid numeric Item ID")
            return

        self.forecast_btn.configure(state="disabled", text="Running...")
        self.status_var.set("Fetching forecast…")
        threading.Thread(target=self._fetch_and_draw, args=(item_id_str,), daemon=True).start()

    def _fetch_and_draw(self, item_id_str: str):
        horizon = int(self.horizon_var.get())
        item_id = int(item_id_str)

        try:
            # 1. Fetch item name for the chart title
            item_name = self._fetch_item_name(item_id)

            # 2. Fetch forecast
            r = requests.get(
                f"{FORECASTING_URL}/forecast/{item_id}",
                params={"horizon": horizon},
                timeout=30
            )
            r.raise_for_status()
            data = r.json()

            # 3. Draw on the main thread
            self.parent.after(0, lambda: self._draw_chart(data, item_name))

        except requests.exceptions.ConnectionError:
            self.parent.after(0, lambda: self.status_var.set(
                "✗  Cannot reach forecasting service — is it running on port 8001?"))
        except requests.exceptions.HTTPError as e:
            msg = e.response.json().get("detail", str(e))
            self.parent.after(0, lambda: self.status_var.set(f"✗  {msg}"))
        except Exception as e:
            self.parent.after(0, lambda: self.status_var.set(f"✗  Unexpected error: {e}"))
        finally:
            self.parent.after(0, lambda: self.forecast_btn.configure(
                state="normal", text="Run Forecast"))

    def _fetch_item_name(self, item_id: int) -> str:
        try:
            r = requests.get(f"{INVENTORY_URL}/api/inventory/{item_id}", timeout=5)
            if r.status_code == 200:
                return r.json().get("drug_name", f"Item {item_id}")
        except Exception:
            pass
        return f"Item {item_id}"

    def _draw_chart(self, data: dict, item_name: str):
        forecast = data["forecast"]
        if not forecast:
            self.status_var.set("No forecast data returned.")
            return

        dates  = [datetime.strptime(f["ds"], "%Y-%m-%d") for f in forecast]
        yhat   = [f["yhat"]        for f in forecast]
        lower  = [f["yhat_lower"]  for f in forecast]
        upper  = [f["yhat_upper"]  for f in forecast]

        # ── Summary card values ──────────────────────────────────────
        total   = sum(yhat)
        avg     = total / len(yhat)
        peak    = max(yhat)
        horizon = data["horizon_days"]

        self._update_card(self.card_total,   f"{total:.0f} units")
        self._update_card(self.card_avg,     f"{avg:.1f} / day")
        self._update_card(self.card_peak,    f"{peak:.1f} units")
        reorder_color = DANGER if total > 100 else WARNING
        self.card_reorder._val_label.configure(
            text="⚠ Reorder Soon" if total > 100 else "✓ OK",
            text_color=reorder_color
        )

        # ── Matplotlib chart ─────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(10, 4.2), facecolor=PANEL)
        ax.set_facecolor(PANEL)

        # Confidence band
        ax.fill_between(dates, lower, upper, color=ACCENT2, alpha=0.18, label="80% Confidence")

        # Main forecast line
        ax.plot(dates, yhat, color=ACCENT, linewidth=2.5,
                label="Predicted Demand", zorder=3)

        # Dots on the line
        ax.scatter(dates, yhat, color=ACCENT, s=28, zorder=4)

        # Peak marker
        peak_idx = yhat.index(peak)
        ax.annotate(
            f"Peak: {peak:.1f}",
            xy=(dates[peak_idx], peak),
            xytext=(10, 12), textcoords="offset points",
            color=WARNING, fontsize=9, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=WARNING, lw=1.2)
        )

        # Grid & spines
        ax.grid(axis="y", color="#2a2d3a", linewidth=0.8, linestyle="--")
        ax.grid(axis="x", color="#2a2d3a", linewidth=0.4, linestyle=":")
        for spine in ax.spines.values():
            spine.set_color("#2a2d3a")

        # Axis formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right",
                 color=SUBTEXT, fontsize=9)
        ax.tick_params(axis="y", colors=SUBTEXT, labelsize=9)
        ax.set_ylabel("Units / Day", color=SUBTEXT, fontsize=10)

        ax.set_title(
            f"{item_name}  —  {horizon}-Day Demand Forecast",
            color=TEXT, fontsize=13, fontweight="bold",
            fontfamily="monospace", pad=14
        )

        ax.legend(facecolor=BG, edgecolor="#2a2d3a",
                  labelcolor=TEXT, fontsize=9)

        plt.tight_layout()

        # ── Embed in CTk ─────────────────────────────────────────────
        if self.canvas_widget:
            self.canvas_widget.get_tk_widget().destroy()

        self.placeholder.place_forget()

        self.canvas_widget = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas_widget.draw()
        self.canvas_widget.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        plt.close(fig)

        self.status_var.set(
            f"✓  Forecast generated for {item_name} "
            f"(Item {data['item_id']})  ·  {horizon} days  ·  "
            f"Total predicted: {total:.0f} units"
        )