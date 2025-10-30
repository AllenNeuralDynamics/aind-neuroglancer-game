"""Models for the game app"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4


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


class GameSession:
    """Class to represent a game session"""

    session_id: str
    username: str
    status: str
    # game options (configured by user)
    game_mode: str
    num_rounds: int
    time_per_round: int
    # game stats
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    total_annotations: Optional[int]
    s3_location: Optional[str]

    def __init__(
        self,
        username: str,
        game_mode: str,
        num_rounds: int,
        time_per_round: int,
        status: str = "not_started",
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        total_annotations: Optional[int] = None,
        s3_location: Optional[str] = None,
    ):
        """Initialize a GameSession instance"""

        self.username = username
        self.game_mode = game_mode
        self.num_rounds = num_rounds
        self.time_per_round = time_per_round
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.total_annotations = total_annotations
        self.s3_location = s3_location

        if session_id:
            self.session_id = session_id
        else:
            self.session_id = "SESSION_" + uuid4().hex

    def start_game(self):
        """Mark the game session as started"""
        self.status = "active"
        self.start_time = datetime.now()
        self.total_annotations = 0

    def update_total_annotations(self, total_annotations: int):
        """Update the total number of annotations made in the game session"""
        self.total_annotations = total_annotations

    def end_game(self, total_annotations: int):
        """Mark the game session as ended"""
        self.status = "completed"
        self.end_time = datetime.now()
        self.total_annotations = total_annotations

    def abandon_game(self):
        """Mark the game session as abandoned"""
        self.status = "abandoned"
        self.end_time = datetime.now()

    def to_dynamodb_item(self) -> dict:
        """Convert user to dictionary representation"""
        return {
            # do not change the partion and sort key names
            "PartitionKey": self.username,
            "SortKey": self.session_id,
            # other attributes
            "status": self.status,
            "game_mode": self.game_mode,
            "num_rounds": self.num_rounds,
            "time_per_round": self.time_per_round,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_annotations": self.total_annotations,
            "s3_location": self.s3_location,
        }

    @staticmethod
    def from_dynamodb_item(session_data: dict) -> "GameSession":
        """Create a GameSession object from a DynamoDB item"""

        start_time = session_data.get("start_time")
        if start_time:
            start_time = datetime.fromisoformat(start_time)
        end_time = session_data.get("end_time")
        if end_time:
            end_time = datetime.fromisoformat(end_time)
        session = GameSession(
            username=session_data.get("PartitionKey", ""),
            game_mode=session_data.get("game_mode", ""),
            num_rounds=session_data.get("num_rounds", 0),
            time_per_round=session_data.get("time_per_round", 0),
            status=session_data.get("status", ""),
            session_id=session_data.get("SortKey", ""),
            start_time=start_time,
            end_time=end_time,
            total_annotations=session_data.get("total_annotations"),
            s3_location=session_data.get("s3_location"),
        )
        return session
