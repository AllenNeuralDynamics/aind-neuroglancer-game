"""Utility clients for interacting with DynamoDB."""

from typing import Any, Optional

import boto3
from boto3.dynamodb.conditions import Key
from config import Constants
from models import GameSession, User


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

    def query_items(
        self,
        key_condition_expression: Any,
        filter_expression: Optional[Any] = None,
        select: Optional[str] = None,
        projection_expression: Optional[str] = None,
    ) -> dict:
        """Query items from a DynamoDB table using a key condition expression
        and optional filter expression.
        """
        params = {
            "KeyConditionExpression": key_condition_expression,
        }
        if filter_expression:
            params["FilterExpression"] = filter_expression
        if select:
            params["Select"] = select
        if projection_expression:
            params["ProjectionExpression"] = projection_expression
        response = self._table.query(**params)
        return response


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

    def upsert_user(self, user: User) -> User:
        """Add or update a user in the database."""
        user_data = user.to_dynamodb_item()
        print(f"Saving user data to dynamodb: {user_data}")
        self.db_client.put_item(user_data)
        return user


class GameSessionManager:
    """Manages game sessions in DynamoDB."""

    def __init__(self, db_client: DynamoDbClient):
        self.db_client = db_client

    def get_session(self, username: str, session_id: str) -> Optional[GameSession]:
        """Retrieve game session data by session ID."""
        # NOTE: key is a dictionary that must contain the partion and sort keys
        key = {"PartitionKey": username, "SortKey": session_id}
        session_data = self.db_client.get_item(key)
        print(f"Retrieved game session data from dynamodb: {session_data}")
        return GameSession.from_dynamodb_item(session_data) if session_data else None

    def upsert_session(self, session: GameSession) -> GameSession:
        """Add or update a game session in the database."""
        session_data = session.to_dynamodb_item()
        print(f"Saving session data to dynamodb: {session_data}")
        self.db_client.put_item(session_data)
        return session

    def count_sessions_for_user(self, username: str) -> int:
        """Count the number of sessions for a given user in the database."""
        response = self.db_client.query_items(
            key_condition_expression=Key("PartitionKey").eq(username)
            & Key("SortKey").begins_with("SESSION"),
            select="COUNT",
        )
        return response.get("Count", 0)

    def get_total_annotations_for_user(self, username: str) -> int:
        """Get the total number of annotations made by a user across all sessions."""
        response = self.db_client.query_items(
            key_condition_expression=Key("PartitionKey").eq(username)
            & Key("SortKey").begins_with("SESSION"),
            projection_expression="total_annotations",
        )
        items = response.get("Items", [])
        total_annotations = sum(int(item.get("total_annotations", 0)) for item in items)
        return total_annotations

def initialize_db_managers() -> tuple[UserManager, GameSessionManager]:
    """Initialize and return database managers"""
    db_client = DynamoDbClient()
    user_manager = UserManager(db_client=db_client)
    game_session_manager = GameSessionManager(db_client=db_client)
    return user_manager, game_session_manager
