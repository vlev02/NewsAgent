"""Abstract database backend interface"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from src.dataclasses import SearchItem, QueryRequest, QueryResponse


class DatabaseBackend(ABC):
    """
    Abstract interface for database persistence.

    Implementations should handle storage and retrieval of SearchItem,
    QueryRequest, and QueryResponse objects independently without
    cascade relationships between them.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection and initialize schema"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass

    # ==================== QUERY OPERATIONS ====================

    @abstractmethod
    def save_query(self, query: QueryRequest) -> str:
        """
        Save QueryRequest to database.

        Args:
            query: QueryRequest object to save

        Returns:
            query_id (same as input query.query_id)
        """
        pass

    @abstractmethod
    def load_query(self, query_id: str) -> Optional[QueryRequest]:
        """
        Load QueryRequest by ID.

        Args:
            query_id: UUID of the query

        Returns:
            QueryRequest object or None if not found
        """
        pass

    @abstractmethod
    def list_queries(self, limit: int = 100, offset: int = 0) -> List[QueryRequest]:
        """
        List all queries with pagination.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of QueryRequest objects
        """
        pass

    @abstractmethod
    def search_queries(self,
                      agent_name: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> List[QueryRequest]:
        """
        Search queries by filters.

        Args:
            agent_name: Filter by source agent name
            start_date: Filter by start timestamp
            end_date: Filter by end timestamp

        Returns:
            List of matching QueryRequest objects
        """
        pass

    # ==================== RESPONSE OPERATIONS ====================

    @abstractmethod
    def save_response(self, response: QueryResponse) -> str:
        """
        Save QueryResponse to database.

        Independently saves response metadata and associated items.
        Does NOT create cascade relationship to query.

        Args:
            response: QueryResponse object to save

        Returns:
            response_id
        """
        pass

    @abstractmethod
    def load_response(self, response_id: str) -> Optional[QueryResponse]:
        """
        Load QueryResponse by ID with associated items.

        Args:
            response_id: UUID of the response

        Returns:
            QueryResponse object with items populated, or None
        """
        pass

    @abstractmethod
    def list_responses(self,
                      query_id: Optional[str] = None,
                      agent_name: Optional[str] = None,
                      limit: int = 100) -> List[QueryResponse]:
        """
        List responses with optional filtering.

        Args:
            query_id: Filter by query ID (text match, no constraint)
            agent_name: Filter by agent name
            limit: Maximum number of results

        Returns:
            List of QueryResponse objects
        """
        pass

    # ==================== ITEM OPERATIONS ====================

    @abstractmethod
    def save_item(self, item: SearchItem) -> str:
        """
        Save SearchItem to database.

        Args:
            item: SearchItem object to save

        Returns:
            item_id
        """
        pass

    @abstractmethod
    def save_items_batch(self, items: List[SearchItem]) -> List[str]:
        """
        Save multiple items efficiently.

        Args:
            items: List of SearchItem objects

        Returns:
            List of item_ids
        """
        pass

    @abstractmethod
    def load_item(self, item_id: str) -> Optional[SearchItem]:
        """
        Load SearchItem by ID.

        Args:
            item_id: UUID of the item

        Returns:
            SearchItem object or None
        """
        pass

    @abstractmethod
    def search_items(self,
                    title_contains: Optional[str] = None,
                    source_type: Optional[str] = None,
                    query_id: Optional[str] = None,
                    date_range: Optional[Tuple[datetime, datetime]] = None,
                    limit: int = 100) -> List[SearchItem]:
        """
        Search items with multiple filters.

        Args:
            title_contains: Search in title field
            source_type: Filter by source type (XUNFEI, BOCHA, etc)
            query_id: Filter by query_id (text match, no constraint)
            date_range: Filter by timestamp range (start, end)
            limit: Maximum number of results

        Returns:
            List of matching SearchItem objects
        """
        pass

    @abstractmethod
    def deduplicate_items(self, items: List[SearchItem],
                         strategy: str = "url") -> List[SearchItem]:
        """
        Remove duplicate items based on strategy.

        Args:
            items: List of SearchItem objects
            strategy: "url" (default) | "title" | "content_hash"

        Returns:
            List of unique items
        """
        pass

    # ==================== STATISTICS ====================

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dict with counts and distributions
        """
        pass

    @abstractmethod
    def cleanup(self, days_old: int = 30) -> int:
        """
        Delete records older than days_old.

        Args:
            days_old: Age threshold in days

        Returns:
            Number of records deleted
        """
        pass
