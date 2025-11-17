"""
Fake Response Manager

Handles storage, retrieval, and management of fake API responses.
Uses MD5 hashing of (url, method, description) as file identifier.

Each response is stored as:
  data/fake_response/{agent}/{md5_hash}.json
  data/fake_response/{agent}/{md5_hash}.metadata.json
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache

from src.debug_config import DebugConfig
from src.utils.debug_logger import DebugLogger

logger = DebugLogger(__name__)


class FakeResponseManager:
    """Manages fake API responses with MD5-based file naming."""

    def __init__(self, base_dir: str = "data/fake_response"):
        """
        Initialize the fake response manager.

        Args:
            base_dir: Base directory for storing fake responses
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}  # In-memory cache of metadata

    @staticmethod
    def generate_hash(url: str, method: str, description: str = "default") -> str:
        """
        Generate MD5 hash for (url, method, description) tuple.

        Args:
            url: API endpoint URL
            method: HTTP method (GET, POST, etc.)
            description: Additional description for uniqueness

        Returns:
            MD5 hash string (first 16 chars for brevity)
        """
        combined = f"{url}|{method}|{description}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _ensure_agent_dir(self, agent_name: str) -> Path:
        """Ensure agent-specific directory exists."""
        agent_dir = self.base_dir / agent_name.lower()
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

    def _get_response_path(self, agent_name: str, md5_hash: str) -> Path:
        """Get file path for response."""
        return self._ensure_agent_dir(agent_name) / f"{md5_hash}.json"

    def _get_metadata_path(self, agent_name: str, md5_hash: str) -> Path:
        """Get file path for metadata."""
        return self._ensure_agent_dir(agent_name) / f"{md5_hash}.metadata.json"

    def get_response(
        self,
        agent_name: str,
        url: str,
        method: str,
        description: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response.

        Args:
            agent_name: Name of the agent (BOCHA, XUNFEI, etc.)
            url: API endpoint URL
            method: HTTP method
            description: Description for this specific request

        Returns:
            Response dict if found, None otherwise
        """
        md5_hash = self.generate_hash(url, method, description)
        response_path = self._get_response_path(agent_name, md5_hash)

        if not response_path.exists():
            if DebugConfig.log_fake_response_misses:
                logger.debug(f"Cache MISS: {agent_name}/{md5_hash}.json")
            return None

        try:
            with open(response_path, 'r', encoding='utf-8') as f:
                response = json.load(f)

            # Update metadata usage count
            self._update_metadata_usage(agent_name, md5_hash)

            if DebugConfig.log_fake_response_hits:
                logger.debug(f"Cache HIT: {agent_name}/{md5_hash}.json")

            return response
        except Exception as e:
            logger.error(f"Failed to load response {response_path}: {e}")
            return None

    def save_response(
        self,
        agent_name: str,
        url: str,
        method: str,
        description: str,
        request_body: Dict[str, Any],
        response_body: Dict[str, Any],
        notes: str = ""
    ) -> bool:
        """
        Save a new fake response.

        Args:
            agent_name: Name of the agent
            url: API endpoint URL
            method: HTTP method
            description: Description for this specific request
            request_body: The request payload sent
            response_body: The response received
            notes: Optional notes about this response

        Returns:
            True if successful, False otherwise
        """
        md5_hash = self.generate_hash(url, method, description)

        # Check if already exists
        if self._get_response_path(agent_name, md5_hash).exists():
            logger.warning(
                f"Response already exists: {agent_name}/{md5_hash}.json. "
                "Use update_response to replace."
            )
            return False

        try:
            # Create response file
            response_data = {
                "url": url,
                "method": method,
                "description": description,
                "timestamp_created": datetime.now().isoformat(),
                "timestamp_updated": datetime.now().isoformat(),
                "request_body": request_body,
                "response_body": response_body
            }

            response_path = self._get_response_path(agent_name, md5_hash)
            with open(response_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)

            # Create metadata file
            metadata = {
                "md5_hash": md5_hash,
                "agent": agent_name,
                "url": url,
                "method": method,
                "description": description,
                "usage_count": 0,
                "created": datetime.now().isoformat(),
                "last_used": None,
                "notes": notes
            }

            metadata_path = self._get_metadata_path(agent_name, md5_hash)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            if DebugConfig.log_api_calls:
                logger.info(f"Saved response: {agent_name}/{md5_hash}.json")

            return True
        except Exception as e:
            logger.error(f"Failed to save response: {e}")
            return False

    def update_response(
        self,
        agent_name: str,
        url: str,
        method: str,
        description: str,
        request_body: Dict[str, Any],
        response_body: Dict[str, Any]
    ) -> bool:
        """
        Update an existing cached response (replace specific file).

        Args:
            agent_name: Name of the agent
            url: API endpoint URL
            method: HTTP method
            description: Description for this specific request
            request_body: The request payload sent
            response_body: The new response received

        Returns:
            True if successful, False otherwise
        """
        md5_hash = self.generate_hash(url, method, description)

        try:
            # Update response file
            response_data = {
                "url": url,
                "method": method,
                "description": description,
                "timestamp_created": datetime.now().isoformat(),
                "timestamp_updated": datetime.now().isoformat(),
                "request_body": request_body,
                "response_body": response_body
            }

            response_path = self._get_response_path(agent_name, md5_hash)
            with open(response_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)

            # Update metadata
            metadata_path = self._get_metadata_path(agent_name, md5_hash)
            metadata = {
                "md5_hash": md5_hash,
                "agent": agent_name,
                "url": url,
                "method": method,
                "description": description,
                "usage_count": 0,
                "created": datetime.now().isoformat(),
                "last_used": None,
                "notes": "Updated"
            }

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            if DebugConfig.log_api_calls:
                logger.info(f"Updated response: {agent_name}/{md5_hash}.json")

            return True
        except Exception as e:
            logger.error(f"Failed to update response: {e}")
            return False

    def delete_response(self, agent_name: str, md5_hash: str) -> bool:
        """
        Delete a cached response.

        Args:
            agent_name: Name of the agent
            md5_hash: MD5 hash of the response to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            response_path = self._get_response_path(agent_name, md5_hash)
            metadata_path = self._get_metadata_path(agent_name, md5_hash)

            if response_path.exists():
                response_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()

            logger.info(f"Deleted response: {agent_name}/{md5_hash}.json")
            return True
        except Exception as e:
            logger.error(f"Failed to delete response: {e}")
            return False

    def response_exists(
        self,
        agent_name: str,
        url: str,
        method: str,
        description: str = "default"
    ) -> bool:
        """
        Check if a response exists.

        Args:
            agent_name: Name of the agent
            url: API endpoint URL
            method: HTTP method
            description: Description for this specific request

        Returns:
            True if response exists, False otherwise
        """
        md5_hash = self.generate_hash(url, method, description)
        return self._get_response_path(agent_name, md5_hash).exists()

    def list_responses(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        List all cached responses for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            List of metadata dictionaries
        """
        agent_dir = self._ensure_agent_dir(agent_name)
        responses = []

        for metadata_file in agent_dir.glob("*.metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                responses.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to load metadata {metadata_file}: {e}")

        return sorted(responses, key=lambda x: x.get('created', ''), reverse=True)

    def get_metadata(self, agent_name: str, md5_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific response.

        Args:
            agent_name: Name of the agent
            md5_hash: MD5 hash of the response

        Returns:
            Metadata dict if found, None otherwise
        """
        metadata_path = self._get_metadata_path(agent_name, md5_hash)

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata {metadata_path}: {e}")
            return None

    def _update_metadata_usage(self, agent_name: str, md5_hash: str) -> bool:
        """
        Update metadata when a cached response is used.

        Args:
            agent_name: Name of the agent
            md5_hash: MD5 hash of the response

        Returns:
            True if successful, False otherwise
        """
        metadata = self.get_metadata(agent_name, md5_hash)
        if not metadata:
            return False

        metadata["usage_count"] = metadata.get("usage_count", 0) + 1
        metadata["last_used"] = datetime.now().isoformat()

        try:
            metadata_path = self._get_metadata_path(agent_name, md5_hash)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False

    def get_statistics(self, agent_name: str) -> Dict[str, Any]:
        """
        Get statistics for an agent's cached responses.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary with statistics
        """
        responses = self.list_responses(agent_name)

        if not responses:
            return {
                "agent": agent_name,
                "total_cached": 0,
                "total_usage": 0,
                "most_used": None
            }

        total_usage = sum(r.get("usage_count", 0) for r in responses)
        most_used = max(responses, key=lambda x: x.get("usage_count", 0)) if responses else None

        return {
            "agent": agent_name,
            "total_cached": len(responses),
            "total_usage": total_usage,
            "average_usage": total_usage / len(responses) if responses else 0,
            "most_used": most_used
        }


# Global instance for convenience
fake_response_manager = FakeResponseManager()
