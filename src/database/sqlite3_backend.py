"""SQLite3 implementation of DatabaseBackend"""

import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from src.dataclasses import SearchItem, QueryRequest, QueryResponse
from .backend import DatabaseBackend


class SQLite3Backend(DatabaseBackend):
    """
    SQLite3 implementation of DatabaseBackend.

    Stores SearchItem, QueryRequest, and QueryResponse independently
    without cascade relationships.
    """

    def __init__(self, db_path: str = "newsagent.db"):
        """Initialize SQLite3 backend with database path"""
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Create/connect to SQLite database and initialize schema"""
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def disconnect(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def _initialize_schema(self) -> None:
        """Create tables if they don't exist"""
        cursor = self.connection.cursor()

        # Queries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                query_id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                query_fields TEXT NOT NULL,
                query_topics TEXT NOT NULL,
                source_agents TEXT NOT NULL,
                days_back INTEGER DEFAULT 7,
                time_filter TEXT DEFAULT 'oneWeek',
                max_results INTEGER DEFAULT 10,
                min_relevance_score REAL DEFAULT 0.0,
                include_ai_summary BOOLEAN DEFAULT 1,
                include_raw_response BOOLEAN DEFAULT 0,
                exclude_duplicates BOOLEAN DEFAULT 1,
                language TEXT DEFAULT 'zh',
                api_specific_params TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Responses table (NO CASCADE to queries)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                response_id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                query_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                items_count INTEGER DEFAULT 0,
                total_estimated INTEGER,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                raw_response TEXT,
                execution_time_ms INTEGER DEFAULT 0,
                tokens_used INTEGER,
                status TEXT DEFAULT 'completed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indices for responses
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_responses_query_id
            ON responses(query_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_responses_agent_name
            ON responses(agent_name)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_responses_timestamp
            ON responses(timestamp)
        ''')

        # Items table (NO CASCADE to responses)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_url TEXT UNIQUE NOT NULL,
                source_name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                category TEXT,
                key_entities TEXT,
                relevance_score REAL,
                significance TEXT,
                metadata TEXT,
                query_id TEXT,
                topic_tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indices for items
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_items_source_type
            ON items(source_type)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_items_query_id
            ON items(query_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_items_timestamp
            ON items(timestamp)
        ''')

        # Response_Items junction table (NO CASCADE)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS response_items (
                response_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                position INTEGER,
                PRIMARY KEY (response_id, item_id)
            )
        ''')

        # Create indices for response_items
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_response_items_response_id
            ON response_items(response_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_response_items_item_id
            ON response_items(item_id)
        ''')

        self.connection.commit()

    # ==================== QUERY OPERATIONS ====================

    def save_query(self, query: QueryRequest) -> str:
        """Save QueryRequest to database"""
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO queries (
                query_id, timestamp, query_fields, query_topics, source_agents,
                days_back, time_filter, max_results, min_relevance_score,
                include_ai_summary, include_raw_response, exclude_duplicates,
                language, api_specific_params
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            query.query_id,
            query.timestamp.isoformat(),
            json.dumps(query.query_fields),
            json.dumps(query.query_topics),
            json.dumps(query.source_agents),
            query.days_back,
            query.time_filter,
            query.max_results,
            query.min_relevance_score,
            query.include_ai_summary,
            query.include_raw_response,
            query.exclude_duplicates,
            query.language,
            json.dumps(query.api_specific_params) if query.api_specific_params else None
        ))
        self.connection.commit()
        return query.query_id

    def load_query(self, query_id: str) -> Optional[QueryRequest]:
        """Load QueryRequest by ID"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM queries WHERE query_id = ?', (query_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_query_request(row)

    def list_queries(self, limit: int = 100, offset: int = 0) -> List[QueryRequest]:
        """List all queries with pagination"""
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT * FROM queries ORDER BY timestamp DESC LIMIT ? OFFSET ?',
            (limit, offset)
        )
        return [self._row_to_query_request(row) for row in cursor.fetchall()]

    def search_queries(self,
                      agent_name: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> List[QueryRequest]:
        """Search queries by filters"""
        query = 'SELECT * FROM queries WHERE 1=1'
        params = []

        if agent_name:
            query += ' AND source_agents LIKE ?'
            params.append(f'%"{agent_name}"%')

        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date.isoformat())

        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date.isoformat())

        query += ' ORDER BY timestamp DESC'

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return [self._row_to_query_request(row) for row in cursor.fetchall()]

    # ==================== RESPONSE OPERATIONS ====================

    def save_response(self, response: QueryResponse) -> str:
        """Save QueryResponse and associated items"""
        cursor = self.connection.cursor()

        # Save response
        cursor.execute('''
            INSERT OR REPLACE INTO responses (
                response_id, agent_name, query_id, timestamp, items_count,
                total_estimated, success, error_message, raw_response,
                execution_time_ms, tokens_used, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            response.response_id,
            response.agent_name,
            response.query_id,
            response.timestamp.isoformat(),
            len(response.items),
            response.total_estimated,
            response.success,
            response.error_message,
            json.dumps(response.raw_response) if response.raw_response else None,
            response.execution_time_ms,
            response.tokens_used,
            response.status
        ))

        # Save items and junction records
        for position, item in enumerate(response.items):
            self.save_item(item)
            cursor.execute('''
                INSERT OR IGNORE INTO response_items (response_id, item_id, position)
                VALUES (?, ?, ?)
            ''', (response.response_id, item.id, position))

        self.connection.commit()
        return response.response_id

    def load_response(self, response_id: str) -> Optional[QueryResponse]:
        """Load QueryResponse by ID with items"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM responses WHERE response_id = ?', (response_id,))
        row = cursor.fetchone()

        if not row:
            return None

        # Load items
        cursor.execute('''
            SELECT i.* FROM items i
            JOIN response_items ri ON i.item_id = ri.item_id
            WHERE ri.response_id = ?
            ORDER BY ri.position
        ''', (response_id,))

        items = [self._row_to_item(r) for r in cursor.fetchall()]

        return self._row_to_query_response(row, items)

    def list_responses(self,
                      query_id: Optional[str] = None,
                      agent_name: Optional[str] = None,
                      limit: int = 100) -> List[QueryResponse]:
        """List responses with optional filtering"""
        query = 'SELECT * FROM responses WHERE 1=1'
        params = []

        if query_id:
            query += ' AND query_id = ?'
            params.append(query_id)

        if agent_name:
            query += ' AND agent_name = ?'
            params.append(agent_name)

        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        responses = []
        for row in cursor.fetchall():
            response = self.load_response(row['response_id'])
            if response:
                responses.append(response)

        return responses

    # ==================== ITEM OPERATIONS ====================

    def save_item(self, item: SearchItem) -> str:
        """Save SearchItem to database"""
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO items (
                item_id, title, content, source_url, source_name, source_type,
                timestamp, category, key_entities, relevance_score, significance,
                metadata, query_id, topic_tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.id,
            item.title,
            item.content,
            item.source_url,
            item.source_name,
            item.source_type,
            item.timestamp.isoformat(),
            item.category,
            json.dumps(item.key_entities) if item.key_entities else None,
            item.relevance_score,
            item.significance,
            json.dumps(item.metadata) if item.metadata else None,
            item.query_id,
            json.dumps(item.topic_tags) if item.topic_tags else None
        ))
        self.connection.commit()
        return item.id

    def save_items_batch(self, items: List[SearchItem]) -> List[str]:
        """Save multiple items efficiently"""
        cursor = self.connection.cursor()
        for item in items:
            self.save_item(item)
        return [item.id for item in items]

    def load_item(self, item_id: str) -> Optional[SearchItem]:
        """Load SearchItem by ID"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM items WHERE item_id = ?', (item_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_item(row)

    def search_items(self,
                    title_contains: Optional[str] = None,
                    source_type: Optional[str] = None,
                    query_id: Optional[str] = None,
                    date_range: Optional[Tuple[datetime, datetime]] = None,
                    limit: int = 100) -> List[SearchItem]:
        """Search items with multiple filters"""
        query = 'SELECT * FROM items WHERE 1=1'
        params = []

        if title_contains:
            query += ' AND title LIKE ?'
            params.append(f'%{title_contains}%')

        if source_type:
            query += ' AND source_type = ?'
            params.append(source_type)

        if query_id:
            query += ' AND query_id = ?'
            params.append(query_id)

        if date_range:
            start_date, end_date = date_range
            query += ' AND timestamp >= ? AND timestamp <= ?'
            params.extend([start_date.isoformat(), end_date.isoformat()])

        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return [self._row_to_item(row) for row in cursor.fetchall()]

    def deduplicate_items(self, items: List[SearchItem],
                         strategy: str = "url") -> List[SearchItem]:
        """Remove duplicate items based on strategy"""
        if strategy == "url":
            seen_urls = set()
            unique = []
            for item in items:
                if item.source_url not in seen_urls:
                    seen_urls.add(item.source_url)
                    unique.append(item)
            return unique

        elif strategy == "title":
            seen_titles = set()
            unique = []
            for item in items:
                if item.title not in seen_titles:
                    seen_titles.add(item.title)
                    unique.append(item)
            return unique

        elif strategy == "content_hash":
            seen_hashes = set()
            unique = []
            for item in items:
                content_hash = hashlib.md5(item.content.encode()).hexdigest()
                if content_hash not in seen_hashes:
                    seen_hashes.add(content_hash)
                    unique.append(item)
            return unique

        return items

    # ==================== STATISTICS ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        cursor = self.connection.cursor()

        stats = {}

        cursor.execute('SELECT COUNT(*) as count FROM queries')
        stats['total_queries'] = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM responses')
        stats['total_responses'] = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM items')
        stats['total_items'] = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(DISTINCT source_type) as count FROM items')
        stats['unique_sources'] = cursor.fetchone()['count']

        cursor.execute('''
            SELECT source_type, COUNT(*) as count FROM items
            GROUP BY source_type ORDER BY count DESC
        ''')
        stats['items_by_source'] = {row['source_type']: row['count'] for row in cursor.fetchall()}

        cursor.execute('''
            SELECT agent_name, COUNT(*) as count FROM responses
            GROUP BY agent_name ORDER BY count DESC
        ''')
        stats['responses_by_agent'] = {row['agent_name']: row['count'] for row in cursor.fetchall()}

        return stats

    def cleanup(self, days_old: int = 30) -> int:
        """Delete old records"""
        cursor = self.connection.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()

        cursor.execute('DELETE FROM items WHERE created_at < ?', (cutoff_date,))
        cursor.execute('DELETE FROM responses WHERE created_at < ?', (cutoff_date,))
        cursor.execute('DELETE FROM queries WHERE created_at < ?', (cutoff_date,))

        deleted = cursor.rowcount
        self.connection.commit()
        return deleted

    # ==================== HELPER METHODS ====================

    def _row_to_query_request(self, row) -> QueryRequest:
        """Convert database row to QueryRequest"""
        return QueryRequest(
            query_id=row['query_id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            query_fields=json.loads(row['query_fields']),
            query_topics=json.loads(row['query_topics']),
            source_agents=json.loads(row['source_agents']),
            days_back=row['days_back'],
            time_filter=row['time_filter'],
            max_results=row['max_results'],
            min_relevance_score=row['min_relevance_score'],
            include_ai_summary=bool(row['include_ai_summary']),
            include_raw_response=bool(row['include_raw_response']),
            exclude_duplicates=bool(row['exclude_duplicates']),
            language=row['language'],
            api_specific_params=json.loads(row['api_specific_params']) if row['api_specific_params'] else {}
        )

    def _row_to_query_response(self, row, items: List[SearchItem]) -> QueryResponse:
        """Convert database row to QueryResponse"""
        return QueryResponse(
            response_id=row['response_id'],
            agent_name=row['agent_name'],
            query_id=row['query_id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            items=items,
            total_estimated=row['total_estimated'],
            success=bool(row['success']),
            error_message=row['error_message'],
            raw_response=json.loads(row['raw_response']) if row['raw_response'] else None,
            execution_time_ms=row['execution_time_ms'],
            tokens_used=row['tokens_used'],
            status=row['status']
        )

    def _row_to_item(self, row) -> SearchItem:
        """Convert database row to SearchItem"""
        return SearchItem(
            id=row['item_id'],
            title=row['title'],
            content=row['content'],
            source_url=row['source_url'],
            source_name=row['source_name'],
            source_type=row['source_type'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            category=row['category'],
            key_entities=json.loads(row['key_entities']) if row['key_entities'] else None,
            relevance_score=row['relevance_score'],
            significance=row['significance'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            query_id=row['query_id'],
            topic_tags=json.loads(row['topic_tags']) if row['topic_tags'] else []
        )
