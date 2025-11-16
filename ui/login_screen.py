import customtkinter as ctk

class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_login_callback):
        super().__init__(master)

        self.on_login_callback = on_login_callback

        # Create a 3x3 grid: center content goes in (1,1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)

        # Centered container frame (the actual login box)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=1, sticky="nsew")

        # Title
        title = ctk.CTkLabel(
            container,
            text="SmartStock Login",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(0, 20))

        # Username
        self.username_entry = ctk.CTkEntry(
            container,
            placeholder_text="Username",
            width=300
        )
        self.username_entry.pack(pady=10)

        # Password
        self.password_entry = ctk.CTkEntry(
            container,
            placeholder_text="Password",
            width=300,
            show="*"
        )
        self.password_entry.pack(pady=10)

        # Login button
        login_btn = ctk.CTkButton(
            container,
            text="Login",
            width=300,
            command=self.handle_login
        )
        login_btn.pack(pady=(10, 10))

        # Message label
        self.message_label = ctk.CTkLabel(container, text="")
        self.message_label.pack(pady=(10, 0))

    def handle_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == "" or password == "":
            self.message_label.configure(text="Please fill in all fields", text_color="red")
            return

        # temporary success
        self.on_login_callback(username)
