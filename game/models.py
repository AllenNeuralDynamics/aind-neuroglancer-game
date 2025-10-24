"""Models for the game app"""

from datetime import datetime
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

    def __init__(
        self,
        label: str,
        description: str,
        disabled: bool = False,
        link: Optional[str] = None,
        is_learning_mode: bool = False,
    ):
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

    def __init__(
        self, label: str, allowed_pages: List[Page], allowed_game_modes: List[GameMode]
    ):
        self.label = label
        self.allowed_pages = allowed_pages
        self.allowed_game_modes = allowed_game_modes

    @property
    def allowed_links(self) -> List[str]:
        """List of all allowed links for this user role"""
        page_links = [page.link for page in self.allowed_pages]
        mode_links = [
            mode.link for mode in self.allowed_game_modes if mode.link is not None
        ]
        return page_links + mode_links


class User:
    """Class to represent a user"""

    username: str
    email: str
    role: str
    join_date: Optional[datetime]

    def __init__(
        self,
        username: str,
        email: str,
        role: str,
        join_date: Optional[datetime] = None,
    ):
        self.username = username
        self.email = email
        self.role = role
        self.join_date = join_date

    def to_dynamodb_item(self) -> dict:
        """Convert user to dictionary representation"""
        return {
            # do not change the partion and sort key names
            "PartitionKey": self.username,
            "SortKey": "PROFILE",
            # other attributes
            "email": self.email,
            "role": self.role,
            "join_date": self.join_date.isoformat() if self.join_date else None,
        }
    
    @staticmethod
    def from_dynamodb_item(user_data: dict) -> "User":
        """Create a User object from a DynamoDB item"""

        join_date = user_data.get("join_date")
        if join_date:
            join_date = datetime.fromisoformat(join_date)
        return User(
            username=user_data.get("PartitionKey", ""),
            email=user_data.get("email", ""),
            role=user_data.get("role", ""),
            join_date=join_date,
        )
