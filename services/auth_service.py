import requests
from typing import Optional

# Base URL of the authentication microservice
AUTH_BASE_URL = "http://localhost:8001"


class AuthService:
    # Stored in memory after a successful login, cleared on logout
    _token: Optional[str] = None
    _username: Optional[str] = None
    _role: Optional[str] = None

    # ── Login ─────────────────────────────────────────────────────────────────

    @classmethod
    def login(cls, username: str, password: str) -> dict:
        """
        Send login credentials to the auth service.
        Stores the returned token in memory on success.
        Raises requests.HTTPError on failed login.
        """
        res = requests.post(
            f"{AUTH_BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
            timeout=5,
        )
        # Raises an exception if the status code is 4xx or 5xx
        res.raise_for_status()

        data = res.json()
        cls._store_session(data)
        return data

    # ── Logout ────────────────────────────────────────────────────────────────

    @classmethod
    def logout(cls) -> None:
        """
        Invalidate the current session on the auth service,
        then clear the token from memory.
        """
        if cls._token:
            try:
                requests.post(
                    f"{AUTH_BASE_URL}/api/auth/logout",
                    params={"token": cls._token},
                    timeout=5,
                )
            except requests.RequestException:
                # If the request fails, still clear local state
                pass
        cls._clear_session()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @classmethod
    def is_logged_in(cls) -> bool:
        """Returns True if there is an active session token in memory."""
        return cls._token is not None

    @classmethod
    def current_user(cls) -> Optional[str]:
        """Returns the username of the currently logged in user."""
        return cls._username

    @classmethod
    def current_role(cls) -> Optional[str]:
        """Returns the role of the currently logged in user."""
        return cls._role

    @classmethod
    def get_token(cls) -> Optional[str]:
        """Returns the current session token."""
        return cls._token

    @classmethod
    def _store_session(cls, data: dict) -> None:
        """Save session data to memory after a successful login."""
        cls._token = data["token"]
        cls._username = data["username"]
        cls._role = data["role"]

    @classmethod
    def _clear_session(cls) -> None:
        """Clear all session data from memory."""
        cls._token = None
        cls._username = None
        cls._role = None