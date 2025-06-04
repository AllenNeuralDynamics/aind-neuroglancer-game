"""Models for the game app"""

from typing import List, Optional


class Page:
    """Class to represent a page in the app"""

    link: str
    label: str
    icon: str

    def __init__(self, link: str, label: str, icon: str):
        self.link = link
        self.label = label
        self.icon = icon


class GameMode:
    """Class to represent a game or learning mode in the app"""

    label: str
    description: str
    disabled: bool
    link: Optional[str]
    is_learning_mode: bool

    def __init__(self, label: str, description: str, disabled: bool = False, link: Optional[str] = None, is_learning_mode: bool = False):
        self.label = label
        self.description = description
        self.disabled = disabled
        self.link = link
        self.is_learning_mode = is_learning_mode


class UserRole:
    """Class to represent a user role in the app"""

    label: str
    allowed_pages: List[Page]
    allowed_game_modes: List[GameMode]

    def __init__(self, label: str, allowed_pages: List[Page], allowed_game_modes: List[GameMode]):
        self.label = label
        self.allowed_pages = allowed_pages
        self.allowed_game_modes = allowed_game_modes

    @property
    def allowed_links(self) -> List[str]:
        """List of all allowed links for this user role"""
        page_links = [page.link for page in self.allowed_pages]
        mode_links = [mode.link for mode in self.allowed_game_modes if mode.link is not None]
        return page_links + mode_links