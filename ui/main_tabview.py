import customtkinter as ctk

from ui.inventory_tab import InventoryTab
from ui.account_tab import AccountTab
from ui.tasks_tab import TasksTab
from ui.metrics_tab import MetricsTab
from ui.forecast_tab import ForecastTab

class MainTabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Create tabs
        self.add("Inventory")
        self.add("Account")
        self.add("Tasks")
        self.add("Metrics")
        self.add("Forecast")  

        # Load each tab into its frame
        InventoryTab(self.tab("Inventory"))
        AccountTab(self.tab("Account"))
        TasksTab(self.tab("Tasks"))
        MetricsTab(self.tab("Metrics"))
        ForecastTab(self.tab("Forecast"))