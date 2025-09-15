"""Utility clients for interacting with DynamoDB."""

from datetime import datetime

from config import Constants
from models import User


class DynamoDbClient:
    """Client for interacting with DynamoDB."""

    def __init__(self):
        pass

    def get_item(self, table_name: str, key: dict) -> dict | None:
        """Retrieve an item from a DynamoDB table."""
        pass

    def put_item(self, table_name: str, item: dict) -> None:
        """Put an item into a DynamoDB table."""
        pass


class UserManager:
    """Manages user data in DynamoDB."""

    def __init__(self, db_client: DynamoDbClient):
        self.db_client = db_client

    def get_user(self, username: str) -> User | None:
        """Retrieve user data by user ID."""
        user_data = self.db_client.get_item(
            Constants.DYNAMODB_TABLE.value, {"username": username}
        )
        print(f"Retrieved user data from dynamodb: {user_data}")
        if user_data:
            join_date = user_data.get("join_date")
            if join_date:
                join_date = datetime.fromisoformat(join_date)
            return User(
                username=user_data.get("username", ""),
                email=user_data.get("email", ""),
                role=user_data.get("role", ""),
                join_date=join_date,
            )
        return None

    def create_user(self, user: User) -> User:
        """Create a new user in the database."""
        user_data = user.to_dict()
        print(f"Saving user data to dynamodb: {user_data}")
        self.db_client.put_item(Constants.DYNAMODB_TABLE.value, user_data)
        return user


class GameSessionManager:
    """Manages game sessions in DynamoDB."""

    def __init__(self, db_client: DynamoDbClient):
        self.db_client = db_client

    def get_session(self, session_id: str) -> dict | None:
        """Retrieve game session data by session ID."""
        return self.db_client.get_item(
            Constants.DYNAMODB_TABLE.value, {"session_id": session_id}
        )

    def create_session(self, session_data: dict) -> None:
        """Create a new game session in the database."""
        self.db_client.put_item(Constants.DYNAMODB_TABLE.value, session_data)


def initialize_db_managers() -> tuple[UserManager, GameSessionManager]:
    """Initialize and return database managers"""
    db_client = DynamoDbClient()
    user_manager = UserManager(db_client=db_client)
    game_session_manager = GameSessionManager(db_client=db_client)
    return user_manager, game_session_manager
