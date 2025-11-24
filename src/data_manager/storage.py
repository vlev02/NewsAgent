"""SQLite storage backend for data manager

Implements CRUD operations with cascade delete support.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from .models import RequestModel, ResponseItem, DataModelType


class SQLiteBackend:
    """SQLite database backend with cascade support"""

    def __init__(self, db_path: str, timeout: float = 5.0, check_same_thread: bool = False):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file (absolute or relative to project root)
            timeout: Connection timeout in seconds
            check_same_thread: Allow multi-threaded access
        """
        # Resolve path: if absolute, use as-is; otherwise relative to project root
        db_path_obj = Path(db_path)
        if db_path_obj.is_absolute():
            self.db_path = db_path_obj
        else:
            project_root = Path(__file__).parent.parent.parent
            self.db_path = project_root / db_path

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.timeout = timeout
        self.check_same_thread = check_same_thread

        # Initialize database
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with JSON support"""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=self.timeout,
            check_same_thread=self.check_same_thread
        )
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # RequestModel table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_models (
                request_id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                url TEXT,
                method TEXT,
                headers TEXT,
                body TEXT,
                raw_response TEXT,
                http_status INTEGER,
                response_type TEXT,
                execution_time_ms INTEGER,
                success BOOLEAN,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # ResponseItem table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS response_items (
                item_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                title TEXT,
                content TEXT,
                source_url TEXT,
                source_name TEXT,
                category TEXT,
                key_entities TEXT,
                relevance_score REAL,
                significance TEXT,
                agent_metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (request_id) REFERENCES request_models(request_id)
            )
        """)

        # Create indices for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_request_agent ON request_models(agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_response_request ON response_items(request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_response_agent ON response_items(agent_name)")

        conn.commit()
        conn.close()

    def insert_request(self, request: RequestModel) -> str:
        """Insert RequestModel and return request_id"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Handle None timestamps
        timestamp = request.timestamp.isoformat() if request.timestamp else datetime.now().isoformat()
        created_at = request.created_at.isoformat() if request.created_at else datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO request_models
            (request_id, agent_name, timestamp, url, method, headers, body,
             raw_response, http_status, response_type, execution_time_ms, success, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.request_id,
            request.agent_name,
            timestamp,
            request.url,
            request.method,
            json.dumps(request.headers),
            json.dumps(request.body),
            json.dumps(request.raw_response) if request.raw_response else None,
            request.http_status,
            request.response_type,
            request.execution_time_ms,
            request.success,
            request.error_message,
            created_at
        ))

        conn.commit()
        conn.close()
        return request.request_id

    def insert_response_item(self, item: ResponseItem) -> str:
        """Insert ResponseItem and return item_id"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Handle None timestamps
        timestamp = item.timestamp.isoformat() if item.timestamp else datetime.now().isoformat()
        created_at = item.created_at.isoformat() if item.created_at else datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO response_items
            (item_id, request_id, agent_name, timestamp, title, content, source_url,
             source_name, category, key_entities, relevance_score, significance,
             agent_metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.item_id,
            item.request_id,
            item.agent_name,
            timestamp,
            item.title,
            item.content,
            item.source_url,
            item.source_name,
            item.category,
            json.dumps(item.key_entities),
            item.relevance_score,
            item.significance,
            json.dumps(item.agent_metadata),
            created_at
        ))

        conn.commit()
        conn.close()
        return item.item_id

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve RequestModel by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM request_models WHERE request_id = ?", (request_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._deserialize_request(dict(row))

    def get_response_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve ResponseItem by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM response_items WHERE item_id = ?", (item_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._deserialize_response_item(dict(row))

    def list_requests(self, agent_name: Optional[str] = None, limit: int = 100) -> List[str]:
        """List request IDs, optionally filtered by agent"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if agent_name:
            cursor.execute(
                "SELECT request_id FROM request_models WHERE agent_name = ? ORDER BY created_at DESC LIMIT ?",
                (agent_name, limit)
            )
        else:
            cursor.execute(
                "SELECT request_id FROM request_models ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )

        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]

    def list_response_items(self, request_id: Optional[str] = None, limit: int = 100) -> List[str]:
        """List response item IDs, optionally filtered by request_id"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if request_id:
            cursor.execute(
                "SELECT item_id FROM response_items WHERE request_id = ? ORDER BY created_at DESC LIMIT ?",
                (request_id, limit)
            )
        else:
            cursor.execute(
                "SELECT item_id FROM response_items ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )

        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]

    def get_stats(self, model_type: str) -> Dict[str, Any]:
        """Get statistics for a model type"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if model_type == DataModelType.REQUEST.value:
            table = "request_models"
        elif model_type == DataModelType.RESPONSE_ITEM.value:
            table = "response_items"
        else:
            return {}

        cursor.execute(f"SELECT COUNT(*) as total FROM {table}")
        total = cursor.fetchone()[0]

        cursor.execute(f"SELECT agent_name, COUNT(*) as count FROM {table} GROUP BY agent_name")
        by_agent = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "total": total,
            "by_agent": by_agent
        }

    @staticmethod
    def _deserialize_request(row: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize database row to request dict"""
        return {
            "request_id": row["request_id"],
            "agent_name": row["agent_name"],
            "timestamp": row["timestamp"],
            "url": row["url"],
            "method": row["method"],
            "headers": json.loads(row["headers"]) if row["headers"] else {},
            "body": json.loads(row["body"]) if row["body"] else {},
            "raw_response": json.loads(row["raw_response"]) if row["raw_response"] else None,
            "http_status": row["http_status"],
            "response_type": row.get("response_type", "cached_response"),
            "execution_time_ms": row["execution_time_ms"],
            "success": row["success"],
            "error_message": row["error_message"],
            "created_at": row["created_at"]
        }

    @staticmethod
    def _deserialize_response_item(row: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize database row to response item dict"""
        return {
            "item_id": row["item_id"],
            "request_id": row["request_id"],
            "agent_name": row["agent_name"],
            "timestamp": row["timestamp"],
            "title": row["title"],
            "content": row["content"],
            "source_url": row["source_url"],
            "source_name": row["source_name"],
            "category": row["category"],
            "key_entities": json.loads(row["key_entities"]) if row["key_entities"] else [],
            "relevance_score": row["relevance_score"],
            "significance": row["significance"],
            "agent_metadata": json.loads(row["agent_metadata"]) if row["agent_metadata"] else {},
            "created_at": row["created_at"]
        }

    # Delete operations
    # =========================================================================

    def delete_response_item(self, item_id: str) -> bool:
        """Delete a response item by ID

        Args:
            item_id: Response item ID

        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM response_items WHERE item_id = ?", (item_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_request(self, request_id: str, cascade: bool = True) -> int:
        """Delete a request and optionally cascade to response items

        Args:
            request_id: Request ID
            cascade: If True, delete associated response items

        Returns:
            Total number of records deleted
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            deleted_count = 0

            if cascade:
                cursor.execute("DELETE FROM response_items WHERE request_id = ?", (request_id,))
                deleted_count += cursor.rowcount

            # Delete the request
            cursor.execute("DELETE FROM request_models WHERE request_id = ?", (request_id,))
            deleted_count += cursor.rowcount

            conn.commit()
            return deleted_count
        finally:
            conn.close()

    def delete_all(self) -> int:
        """Delete all records from all tables

        Returns:
            Total number of records deleted
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Delete in order to avoid foreign key constraint issues
            cursor.execute("DELETE FROM response_items")
            response_count = cursor.rowcount

            cursor.execute("DELETE FROM request_models")
            request_count = cursor.rowcount

            conn.commit()
            return response_count + request_count
        finally:
            conn.close()
