
import threading
import customtkinter as ctk
import requests

from services.auth_service import AuthService


class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_login_callback):
        super().__init__(master)

        # Callback fired when login succeeds — switches to the main tab view
        self.on_login_callback = on_login_callback

        # Centre the form using a 3-column, 3-row grid
        self.grid_rowconfigure((0, 2), weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Container holds all the login form widgets
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=1, sticky="nsew")

        # ── Title ─────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            container,
            text="SmartStock",
            font=ctk.CTkFont(size=32, weight="bold"),
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            container,
            text="Pharmacy Inventory System",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack(pady=(0, 24))

        # ── Username field ────────────────────────────────────────────────────
        self.username_entry = ctk.CTkEntry(
            container, placeholder_text="Username", width=300
        )
        self.username_entry.pack(pady=8)

        # ── Password field ────────────────────────────────────────────────────
        self.password_entry = ctk.CTkEntry(
            container, placeholder_text="Password", width=300, show="*"
        )
        self.password_entry.pack(pady=8)

        # Allow pressing Enter to submit the form
        self.password_entry.bind("<Return>", lambda _e: self._handle_login())

        # ── Login button ──────────────────────────────────────────────────────
        self.login_btn = ctk.CTkButton(
            container, text="Login", width=300, command=self._handle_login
        )
        self.login_btn.pack(pady=(12, 4))

        # ── Status message (shown on error) ───────────────────────────────────
        self.message_label = ctk.CTkLabel(container, text="", text_color="red")
        self.message_label.pack(pady=(8, 0))

    # ── Login logic ───────────────────────────────────────────────────────────

    def _handle_login(self):
        """Called when the login button is clicked or Enter is pressed."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        # Basic validation before hitting the network
        if not username or not password:
            self._show_error("Please enter your username and password.")
            return

        self._set_loading(True)

        # Run the network request on a background thread so the UI
        # doesn't freeze while waiting for the server to respond
        threading.Thread(
            target=self._do_login,
            args=(username, password),
            daemon=True,
        ).start()

    def _do_login(self, username: str, password: str):
        """
        Runs on a background thread.
        Calls the auth service and schedules a UI update on the main thread.
        """
        try:
            AuthService.login(username, password)
            # self.after() is used to safely update the UI from a background thread
            self.after(0, self._login_success)

        except requests.HTTPError as e:
            # Handle specific HTTP error codes with helpful messages
            code = e.response.status_code if e.response is not None else 0
            if code == 401:
                self.after(0, self._show_error, "Incorrect username or password.")
            elif code == 403:
                self.after(0, self._show_error, "Account is disabled. Contact admin.")
            else:
                self.after(0, self._show_error, f"Server error ({code}).")

        except requests.ConnectionError:
            self.after(0, self._show_error, "Cannot reach auth service. Is it running?")

        except Exception as exc:
            self.after(0, self._show_error, f"Unexpected error: {exc}")

        finally:
            # Always re-enable the form when the request finishes
            self.after(0, self._set_loading, False)

    def _login_success(self):
        """Called on the main thread after a successful login."""
        self.on_login_callback(AuthService.current_user())

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _show_error(self, msg: str):
        """Display an error message below the login button."""
        self.message_label.configure(text=msg, text_color="red")

    def _set_loading(self, loading: bool):
        """Disable the form while a login request is in progress."""
        state = "disabled" if loading else "normal"
        self.login_btn.configure(
            state=state,
            text="Logging in..." if loading else "Login",
        )
        self.username_entry.configure(state=state)
        self.password_entry.configure(state=state)