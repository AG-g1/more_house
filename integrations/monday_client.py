# integrations/monday_client.py
"""
Monday CRM Integration Client

Monday.com API documentation: https://developer.monday.com/api-reference/docs

This module handles:
- Fetching contract data from Monday boards
- Fetching payment records
- Syncing data between Monday and local database
"""

import os
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

MONDAY_API_URL = "https://api.monday.com/v2"


class MondayClient:
    """
    Client for interacting with Monday.com API.
    """

    def __init__(self):
        self.api_token = os.getenv("MONDAY_API_TOKEN")
        self.contracts_board_id = os.getenv("MONDAY_BOARD_ID_CONTRACTS")
        self.payments_board_id = os.getenv("MONDAY_BOARD_ID_PAYMENTS")

        if not self.api_token:
            logger.warning("MONDAY_API_TOKEN not set. Monday integration disabled.")

    @property
    def headers(self) -> Dict:
        return {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
            "API-Version": "2024-01"
        }

    def _execute_query(self, query: str, variables: Dict = None) -> Dict:
        """Execute a GraphQL query against Monday API."""
        if not self.api_token:
            raise ValueError("Monday API token not configured")

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            MONDAY_API_URL,
            json=payload,
            headers=self.headers
        )

        if response.status_code != 200:
            logger.error(f"Monday API error: {response.status_code} - {response.text}")
            raise Exception(f"Monday API error: {response.status_code}")

        data = response.json()
        if "errors" in data:
            logger.error(f"Monday GraphQL errors: {data['errors']}")
            raise Exception(f"Monday GraphQL error: {data['errors']}")

        return data.get("data", {})

    def get_boards(self) -> List[Dict]:
        """Get list of all boards accessible to the user."""
        query = """
        query {
            boards {
                id
                name
                description
                state
            }
        }
        """
        result = self._execute_query(query)
        return result.get("boards", [])

    def get_board_columns(self, board_id: str) -> List[Dict]:
        """Get column definitions for a board."""
        query = """
        query ($boardId: [ID!]) {
            boards (ids: $boardId) {
                columns {
                    id
                    title
                    type
                    settings_str
                }
            }
        }
        """
        result = self._execute_query(query, {"boardId": [board_id]})
        boards = result.get("boards", [])
        if boards:
            return boards[0].get("columns", [])
        return []

    def get_board_items(
        self,
        board_id: str,
        limit: int = 100,
        cursor: str = None
    ) -> Dict:
        """
        Get items from a board with pagination.

        Returns:
            Dict with 'items' and 'cursor' for next page
        """
        query = """
        query ($boardId: ID!, $limit: Int!, $cursor: String) {
            boards (ids: [$boardId]) {
                items_page (limit: $limit, cursor: $cursor) {
                    cursor
                    items {
                        id
                        name
                        created_at
                        updated_at
                        column_values {
                            id
                            text
                            value
                        }
                    }
                }
            }
        }
        """
        variables = {
            "boardId": board_id,
            "limit": limit
        }
        if cursor:
            variables["cursor"] = cursor

        result = self._execute_query(query, variables)
        boards = result.get("boards", [])
        if boards:
            items_page = boards[0].get("items_page", {})
            return {
                "items": items_page.get("items", []),
                "cursor": items_page.get("cursor")
            }
        return {"items": [], "cursor": None}

    def get_all_board_items(self, board_id: str) -> List[Dict]:
        """Get all items from a board (handles pagination)."""
        all_items = []
        cursor = None

        while True:
            result = self.get_board_items(board_id, limit=100, cursor=cursor)
            items = result.get("items", [])
            all_items.extend(items)

            cursor = result.get("cursor")
            if not cursor or not items:
                break

        return all_items

    def fetch_contracts(self) -> List[Dict]:
        """
        Fetch contract data from the contracts board.
        Maps Monday columns to our contract schema.
        """
        if not self.contracts_board_id:
            logger.warning("MONDAY_BOARD_ID_CONTRACTS not set")
            return []

        items = self.get_all_board_items(self.contracts_board_id)

        # TODO: Map column IDs to our schema based on actual board structure
        # This will need to be customized once we know the exact column names
        contracts = []
        for item in items:
            contract = {
                "monday_id": item["id"],
                "name": item["name"],
                "created_at": item["created_at"],
                "columns": {cv["id"]: cv["text"] for cv in item.get("column_values", [])}
            }
            contracts.append(contract)

        return contracts

    def fetch_payments(self) -> List[Dict]:
        """
        Fetch payment records from the payments board.
        """
        if not self.payments_board_id:
            logger.warning("MONDAY_BOARD_ID_PAYMENTS not set")
            return []

        items = self.get_all_board_items(self.payments_board_id)

        # TODO: Map column IDs to our schema
        payments = []
        for item in items:
            payment = {
                "monday_id": item["id"],
                "name": item["name"],
                "columns": {cv["id"]: cv["text"] for cv in item.get("column_values", [])}
            }
            payments.append(payment)

        return payments


# Convenience functions
def get_monday_client() -> MondayClient:
    """Get a configured Monday client instance."""
    return MondayClient()


def test_connection() -> bool:
    """Test Monday API connection."""
    try:
        client = MondayClient()
        boards = client.get_boards()
        logger.info(f"Monday connection successful. Found {len(boards)} boards.")
        return True
    except Exception as e:
        logger.error(f"Monday connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test the connection
    logging.basicConfig(level=logging.INFO)

    if test_connection():
        client = MondayClient()
        boards = client.get_boards()
        print("\nAvailable boards:")
        for board in boards:
            print(f"  - {board['name']} (ID: {board['id']})")
    else:
        print("Failed to connect to Monday. Check your API token.")
