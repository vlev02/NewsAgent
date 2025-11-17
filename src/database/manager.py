"""Database manager facade providing high-level API"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from src.dataclasses import SearchItem, QueryRequest, QueryResponse
from .backend import DatabaseBackend


class DatabaseManager:
    """
    High-level database manager with backend abstraction.

    Provides a unified interface regardless of the underlying database
    implementation (SQLite3, PostgreSQL, etc).

    Usage:
        with DatabaseManager(SQLite3Backend("newsagent.db")) as db:
            db.save_query(query)
            db.save_response(response)
            results = db.search_items(source_type="XUNFEI")
    """

    def __init__(self, backend: DatabaseBackend):
        """Initialize with a database backend"""
        self.backend = backend

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def connect(self) -> None:
        """Connect to database"""
        self.backend.connect()

    def disconnect(self) -> None:
        """Disconnect from database"""
        self.backend.disconnect()

    # ==================== QUERY OPERATIONS ====================

    def save_query(self, query: QueryRequest) -> str:
        """Save a query request"""
        return self.backend.save_query(query)

    def load_query(self, query_id: str) -> Optional[QueryRequest]:
        """Load a query by ID"""
        return self.backend.load_query(query_id)

    def list_queries(self, limit: int = 100, offset: int = 0) -> List[QueryRequest]:
        """List all queries"""
        return self.backend.list_queries(limit, offset)

    def search_queries(self,
                      agent_name: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> List[QueryRequest]:
        """Search queries by filters"""
        return self.backend.search_queries(agent_name, start_date, end_date)

    # ==================== RESPONSE OPERATIONS ====================

    def save_response(self, response: QueryResponse) -> str:
        """Save a response"""
        return self.backend.save_response(response)

    def load_response(self, response_id: str) -> Optional[QueryResponse]:
        """Load a response by ID"""
        return self.backend.load_response(response_id)

    def list_responses(self,
                      query_id: Optional[str] = None,
                      agent_name: Optional[str] = None,
                      limit: int = 100) -> List[QueryResponse]:
        """List responses with optional filtering"""
        return self.backend.list_responses(query_id, agent_name, limit)

    # ==================== ITEM OPERATIONS ====================

    def save_item(self, item: SearchItem) -> str:
        """Save a search item"""
        return self.backend.save_item(item)

    def save_items_batch(self, items: List[SearchItem]) -> List[str]:
        """Save multiple items efficiently"""
        return self.backend.save_items_batch(items)

    def load_item(self, item_id: str) -> Optional[SearchItem]:
        """Load an item by ID"""
        return self.backend.load_item(item_id)

    def search_items(self,
                    title_contains: Optional[str] = None,
                    source_type: Optional[str] = None,
                    query_id: Optional[str] = None,
                    date_range: Optional[Tuple[datetime, datetime]] = None,
                    limit: int = 100) -> List[SearchItem]:
        """Search items with filters"""
        return self.backend.search_items(
            title_contains, source_type, query_id, date_range, limit
        )

    def deduplicate_items(self, items: List[SearchItem],
                         strategy: str = "url") -> List[SearchItem]:
        """Remove duplicate items"""
        return self.backend.deduplicate_items(items, strategy)

    # ==================== STATISTICS ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.backend.get_stats()

    def cleanup(self, days_old: int = 30) -> int:
        """Clean up old records"""
        return self.backend.cleanup(days_old)

    # ==================== CONVENIENCE METHODS ====================

    def get_latest_responses(self, limit: int = 10) -> List[QueryResponse]:
        """Get most recent responses"""
        return self.list_responses(limit=limit)

    def get_responses_for_query(self, query_id: str) -> List[QueryResponse]:
        """Get all responses for a specific query"""
        return self.list_responses(query_id=query_id)

    def get_items_by_source(self, source_type: str, limit: int = 100) -> List[SearchItem]:
        """Get items from a specific source"""
        return self.search_items(source_type=source_type, limit=limit)

    def get_items_for_query(self, query_id: str) -> List[SearchItem]:
        """Get all items associated with a query"""
        return self.search_items(query_id=query_id)

    def get_recent_items(self, days: int = 7, limit: int = 100) -> List[SearchItem]:
        """Get items from the last N days"""
        now = datetime.now()
        start = datetime.fromtimestamp(now.timestamp() - (days * 86400))
        return self.search_items(date_range=(start, now), limit=limit)

    def print_stats(self) -> None:
        """Print formatted database statistics"""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60)
        print(f"Total Queries: {stats['total_queries']}")
        print(f"Total Responses: {stats['total_responses']}")
        print(f"Total Items: {stats['total_items']}")
        print(f"Unique Sources: {stats['unique_sources']}")

        if stats.get('items_by_source'):
            print("\nItems by Source:")
            for source, count in stats['items_by_source'].items():
                print(f"  {source}: {count}")

        if stats.get('responses_by_agent'):
            print("\nResponses by Agent:")
            for agent, count in stats['responses_by_agent'].items():
                print(f"  {agent}: {count}")
        print("="*60 + "\n")
