import customtkinter 

class MyTabView(customtkinter.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # create tabs
        self.add("Inventory")
        self.add("Account")
        self.add("Tasks")
        self.add("Metrics")
        self.add("Forcast")
        # self.grid(row=0, column=0, sticky="nsew")
        # add widgets on tabs
        self.label = customtkinter.CTkLabel(master=self.tab("Inventory"))
        self.label.grid(row=0, column=0, padx=20, pady=10)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("SmartStock")
        self.geometry("800x800")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tab_view = MyTabView(master=self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")


app = App()
app.mainloop()