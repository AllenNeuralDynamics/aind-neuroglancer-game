"""Models for the game app"""

from typing import List


class Page:
    """Class to represent a page in the app"""

    link: str
    label: str
    icon: str

    def __init__(self, link: str, label: str, icon: str):
        self.link = link
        self.label = label
        self.icon = icon


class UserRole:
    """Class to represent a user role in the app"""

    label: str
    allowed_pages: List[Page]

    def __init__(self, label: str, allowed_pages: List[Page]):
        self.label = label
        self.allowed_pages = allowed_pages