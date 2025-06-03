"""Module to define configurations for the app, including user roles and pages."""
from enum import Enum

from models import Page, UserRole


class Constants(Enum):
    """Constants used in the app"""

    APP_NAME = "AIND Neuroglancer Game"


class Pages(Enum):
    LOGIN = Page(link="streamlit_app.py", label="Log in", icon=":material/login:")
    ACCOUNT = Page(
        link="pages/account.py", label="Account", icon=":material/account_circle:"
    )
    ADMIN = Page(
        link="pages/admin.py", label="Admin", icon=":material/manage_accounts:"
    )
    DEMO = Page(link="pages/demo.py", label="Demo", icon=":material/star:")
    HOME = Page(link="pages/home.py", label="Home", icon=":material/home:")
    LEADERBOARD = Page(
        link="pages/leaderboard.py", label="Leaderboard", icon=":material/leaderboard:"
    )


_GUEST_PAGES = [Pages.HOME.value, Pages.DEMO.value]
_USER_PAGES = [
    *_GUEST_PAGES,
    Pages.LEADERBOARD.value,
    Pages.ACCOUNT.value,
]
_ADMIN_PAGES = [
    *_USER_PAGES,
    Pages.ADMIN.value,
]


class UserRoles(Enum):
    """Possible user roles in the app"""

    GUEST = UserRole(label="guest", allowed_pages=_GUEST_PAGES)
    USER = UserRole(label="user", allowed_pages=_USER_PAGES)
    ADMIN = UserRole(label="admin", allowed_pages=_ADMIN_PAGES)