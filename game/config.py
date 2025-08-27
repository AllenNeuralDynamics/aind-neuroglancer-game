"""Module to define configurations for the app, including user roles and pages."""
import os
from enum import Enum

from models import GameMode, Page, UserRole


class Constants(Enum):
    """Constants used in the app"""

    APP_NAME = "AIND Neuroglancer Game"

    NEUROGLANCER_IP = "0.0.0.0"  # or public IP of the machine for sharable display
    NEUROGLANCER_PORT = 8080  # unused port number
    NEUROGLANCER_VIEWER_HOST = os.getenv("VIEWER_URL_HOST", "localhost")

    GAME_STATUS_REFRESH_EVERY = 1  # seconds


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


class GameModes(Enum):
    """Possible game modes in the app"""

    SINGLE_PLAYER = GameMode(
        label="Single Player",
        description="Explore a brain and challenge yourself to create annotations on your own.",
        link="pages/game_single_player.py",
    )
    MULTIPLAYER = GameMode(
        label="Multiplayer",
        description="Compete with others in real-time annotation battles.",
        disabled=True,
    )
    DAILY_CHALLENGE = GameMode(
        label="Daily Challenge",
        description="Play a unique challenge every day and climb the leaderboard.",
        disabled=True,
    )
    STREAK = GameMode(
        label="Streak",
        description="Make as many annotations as you can in a row without making a mistake.",
        disabled=True,
    )
    TRAINING = GameMode(
        label="Training",
        description="Practice your annotation skills with guided exercises.",
        disabled=True,
        is_learning_mode=True,
    )
    TUTORIAL = GameMode(
        label="Tutorial",
        description="Learn the basics of neuroglancer and annotation techniques.",
        disabled=True,
        is_learning_mode=True,
    )


_ALL_ALLOWED_GAME_MODES = [
    GameModes.SINGLE_PLAYER.value,
]


class UserRoles(Enum):
    """Possible user roles in the app"""

    GUEST = UserRole(
        label="guest",
        allowed_pages=_GUEST_PAGES,
        allowed_game_modes=_ALL_ALLOWED_GAME_MODES,
    )
    USER = UserRole(
        label="user",
        allowed_pages=_USER_PAGES,
        allowed_game_modes=_ALL_ALLOWED_GAME_MODES,
    )
    ADMIN = UserRole(
        label="admin",
        allowed_pages=_ADMIN_PAGES,
        allowed_game_modes=_ALL_ALLOWED_GAME_MODES,
    )
