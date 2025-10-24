"""Utility clients for interacting with DynamoDB."""

from typing import Optional

import boto3
from config import Constants
from models import User


class DynamoDbClient:
    """Client for interacting with DynamoDB."""

    def __init__(self):
        # Use dynamoDB resource which has higher level abstraction than client
        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(Constants.DYNAMODB_TABLE.value)

    def get_item(self, key: dict) -> Optional[dict]:
        """
        Retrieve an item from a DynamoDB table given the primary key(s),
        e.g. {"PartitionKey": "value", "SortKey": "value"}
        """
        response = self._table.get_item(Key=key)
        return response.get("Item")

    def put_item(self, item: dict) -> None:
        """Put an item into a DynamoDB table."""
        self._table.put_item(Item=item)


class UserManager:
    """Manages user data in DynamoDB."""

    def __init__(self, db_client: DynamoDbClient):
        self.db_client = db_client

    def get_user(self, username: str) -> User | None:
        """Retrieve user data by user ID."""
        # NOTE: key is a dictionary that must contain the partion and sort keys
        key = {"PartitionKey": username, "SortKey": "PROFILE"}
        user_data = self.db_client.get_item(key)
        print(f"Retrieved user data from dynamodb: {user_data}")
        return User.from_dynamodb_item(user_data) if user_data else None

    def create_user(self, user: User) -> User:
        """Create a new user in the database."""
        user_data = user.to_dynamodb_item()
        print(f"Saving user data to dynamodb: {user_data}")
        self.db_client.put_item(user_data)
        return user


class GameSessionManager:
    """Manages game sessions in DynamoDB."""

    def __init__(self, db_client: DynamoDbClient):
        self.db_client = db_client

    def get_session(self, session_id: str) -> dict | None:
        """Retrieve game session data by session ID."""
        key = {"session_id": session_id}
        return self.db_client.get_item(key)

    def create_session(self, session_data: dict) -> None:
        """Create a new game session in the database."""
        self.db_client.put_item(Constants.DYNAMODB_TABLE.value, session_data)


def initialize_db_managers() -> tuple[UserManager, GameSessionManager]:
    """Initialize and return database managers"""
    db_client = DynamoDbClient()
    user_manager = UserManager(db_client=db_client)
    game_session_manager = GameSessionManager(db_client=db_client)
    return user_manager, game_session_manager
