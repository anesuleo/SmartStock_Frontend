import customtkinter as ctk
from ui.login_screen import LoginScreen
from ui.main_tabview import MainTabView

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SmartStock")
        self.geometry("1200x800")

        # show login screen first
        self.show_login()

    def show_login(self):
        self.login_screen = LoginScreen(self, self.on_login_success)
        self.login_screen.pack(fill="both", expand=True)

    def on_login_success(self, username):
        # remove login screen
        self.login_screen.destroy()

        # Show main tabview
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        tabs = MainTabView(self)
        tabs.grid(row=0, column=0, sticky="nsew")

        print("Logged in as:", username)
