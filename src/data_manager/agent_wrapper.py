"""Agent wrapper for DataManager integration

Provides a bridge between agents and the independent DataManager.
Agents inherit from this to automatically support data persistence.

Parsers (Case-Specific Extractors):
- parse_request: Extract RequestModel data from agent state
- parse_response_items: Extract ResponseItem list from API response
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class AgentDataWrapper:
    """
    Mixin class for agents to support DataManager integration.

    Provides parser methods that convert agent state into DataManager data values.

    Agents must have:
    - NAME: str (agent identifier)
    - api_endpoint: str
    - request_body: Dict or property that returns Dict (prepared request)
    - get_header_dict(): Dict (auth headers)

    Optional: override parse_* methods for custom parsing logic.
    """

    # Must be implemented by agent subclass
    NAME: str = ""
    api_endpoint: str = ""

    def get_header_dict(self) -> Dict[str, str]:
        """Must be implemented by agent subclass"""
        raise NotImplementedError("Subclass must implement get_header_dict()")

    # =========================================================================
    # Parsers (Case-Specific Extractors)
    # =========================================================================

    def parse_request(
        self,
        method: str = "POST",
        raw_response: Optional[Dict[str, Any]] = None,
        http_status: int = 0,
        execution_time_ms: int = 0,
        success: bool = True,
        error_message: Optional[str] = None,
        response_type: str = "real_call"
    ) -> Dict[str, Any]:
        """
        Extract RequestModel data from agent state.

        This parser captures the complete raw API request and response.
        Called AFTER the API request is made to include the response.

        Args:
            method: HTTP method (default: POST)
            raw_response: Raw API response dict
            http_status: HTTP status code from API
            execution_time_ms: Time taken for API call
            success: Whether API call succeeded
            error_message: Error message if failed
            response_type: "real_call" (fresh API) or "cached_response" (from cache)

        Returns:
            dict with RequestModel data_value:
            {
                'agent_name': str,
                'url': str,
                'method': str,
                'headers': Dict,
                'body': Dict,
                'raw_response': Optional[Dict],
                'http_status': int,
                'response_type': str,
                'execution_time_ms': int,
                'success': bool,
                'error_message': Optional[str]
            }
        """
        return {
            'agent_name': self.NAME,
            'url': self.api_endpoint,
            'method': method,
            'headers': self.get_header_dict(),
            'body': self.request_body.copy(),
            'raw_response': raw_response,
            'http_status': http_status,
            'response_type': response_type,
            'execution_time_ms': execution_time_ms,
            'success': success,
            'error_message': error_message
        }

    def parse_response_items(
        self,
        raw_response: Dict[str, Any],
        item_parser: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract ResponseItem list from raw API response.

        This parser converts a raw API response into a list of normalized
        search result items. Must be implemented by subclass or provided
        via item_parser callback.

        Args:
            raw_response: Raw API response dict
            item_parser: Optional callable(item_dict) -> ResponseItem data_value
                        If not provided, calls self._parse_response_item()

        Returns:
            List of dicts, each with ResponseItem data_value:
            [{
                'agent_name': str,
                'title': str,
                'content': str,
                'source_url': str,
                'source_name': str,
                'category': Optional[str],
                'key_entities': List[str],
                'relevance_score': Optional[float],
                'significance': Optional[str],
                'agent_metadata': Dict
            }, ...]
        """
        if not raw_response:
            return []

        parser = self._get_agent_specific_response_parser()
        if parser:
            parsed = parser(raw_response) or []
            if item_parser:
                result = []
                for item in parsed:
                    normalized = item_parser(item)
                    if normalized:
                        result.append(normalized)
                return result
            return [item for item in parsed if item]

        return self._legacy_parse_response_items(raw_response, item_parser)

    def _legacy_parse_response_items(
        self,
        raw_response: Dict[str, Any],
        item_parser: Optional[callable]
    ) -> List[Dict[str, Any]]:
        """Fallback path that relies on subclass overrides."""
        items: List[Dict[str, Any]] = []
        response_items = self._extract_response_items(raw_response)

        for item_data in response_items:
            parsed = item_parser(item_data) if item_parser else self._parse_response_item(item_data)
            if parsed:
                items.append(parsed)

        return items

    # =========================================================================
    # Internal Extraction Methods (override in subclasses for custom logic)
    # =========================================================================

    def _extract_response_items(self, raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract items list from raw API response.

        Default implementation returns empty list.
        Override in agent subclass to extract items from agent-specific response format.

        Example (BOCHA):
            return raw_response.get('webPages', [])

        Example (XUNFEI):
            return raw_response.get('choices', [])
        """
        return []

    def _parse_response_item(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single item from agent's response format to ResponseItem data_value.

        Default implementation returns None (no items parsed).
        Override in agent subclass with agent-specific parsing logic.

        Example (BOCHA):
            return {
                'title': item_data.get('name'),
                'content': item_data.get('snippet'),
                'source_url': item_data.get('url'),
                'source_name': 'BOCHA',
                'agent_metadata': item_data
            }

        Example (XUNFEI):
            content = item_data.get('message', {}).get('content', '')
            return {
                'title': content[:100],
                'content': content,
                'source_url': '',
                'source_name': 'XUNFEI',
                'agent_metadata': item_data
            }
        """
        return None

    # =========================================================================
    # Agent-specific dispatchers
    # =========================================================================

    def _get_agent_specific_response_parser(self):
        """Return agent-specific parser if implemented."""
        if not self.NAME:
            return None
        method_name = f"_parse_{self.NAME.lower()}_response_items"
        return getattr(self, method_name, None)

    # -- BOCHA ----------------------------------------------------------------
    def _parse_bocha_response_items(self, raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Bocha web search response structure into ResponseItems."""
        if not isinstance(raw_response, dict):
            return []

        payload = raw_response
        if isinstance(payload.get("response"), dict):
            payload = payload["response"]
        if isinstance(payload.get("data"), dict):
            payload = payload["data"]

        entries: List[Dict[str, Any]] = []
        candidates = [
            payload.get("webPages"),
            payload.get("news"),
            payload.get("videos"),
            payload.get("value"),
            payload.get("items"),
            payload.get("results"),
        ]

        for section in candidates:
            if isinstance(section, dict):
                for key in ("value", "items", "results"):
                    values = section.get(key)
                    if isinstance(values, list):
                        entries.extend([entry for entry in values if isinstance(entry, dict)])
                        break
            elif isinstance(section, list):
                entries.extend([entry for entry in section if isinstance(entry, dict)])

        items: List[Dict[str, Any]] = []
        for entry in entries:
            title = entry.get("name") or entry.get("title") or entry.get("summary") or entry.get("snippet") or entry.get("url")
            content = entry.get("summary") or entry.get("snippet") or entry.get("description") or ""
            source_url = entry.get("url") or entry.get("sourceUrl") or entry.get("origin_url") or ""

            if not any([title, content, source_url]):
                continue

            timestamp = entry.get("datePublished") or entry.get("dateLastCrawled")
            if isinstance(timestamp, str):
                ts_value = timestamp.replace("Z", "+00:00")
                try:
                    timestamp = datetime.fromisoformat(ts_value)
                except ValueError:
                    timestamp = None
            else:
                timestamp = None

            entities: List[str] = []
            for key in ("contractedEntities", "entities", "relatedEntities"):
                value = entry.get(key)
                if not isinstance(value, list):
                    continue
                for item in value:
                    if isinstance(item, dict):
                        name = item.get("name") or item.get("text")
                        if name and name not in entities:
                            entities.append(name)
                    elif isinstance(item, str) and item not in entities:
                        entities.append(item)

            item = {
                "agent_name": self.NAME,
                "title": title or "BOCHA Result",
                "content": content,
                "source_url": source_url,
                "source_name": entry.get("siteName") or self.NAME,
                "category": entry.get("category"),
                "key_entities": entities,
                "relevance_score": entry.get("score") or entry.get("rank"),
                "significance": None,
                "agent_metadata": entry,
            }
            if timestamp:
                item["timestamp"] = timestamp
            items.append(item)

        return items

    # -- HUNYUAN --------------------------------------------------------------
    def _parse_hunyuan_response_items(self, raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        news_items = self._extract_news_items_from_choices(raw_response)
        normalized: List[Dict[str, Any]] = []
        for item in news_items:
            normalized_item = self._normalize_structured_news_item(item, default_source="HUNYUAN")
            if normalized_item:
                normalized.append(normalized_item)
        return normalized

    # -- XUNFEI ---------------------------------------------------------------
    def _parse_xunfei_response_items(self, raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        news_items = self._extract_news_items_from_choices(raw_response)
        normalized: List[Dict[str, Any]] = []
        for item in news_items:
            normalized_item = self._normalize_structured_news_item(item, default_source="XUNFEI")
            if normalized_item:
                normalized.append(normalized_item)
        return normalized

    # -- META -----------------------------------------------------------------
    def _parse_meta_response_items(self, raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        payload = self._unwrap_response_payload(raw_response)
        webpages = payload.get("webpages", [])
        items: List[Dict[str, Any]] = []

        for page in webpages:
            if not isinstance(page, dict):
                continue
            title = page.get("title") or page.get("name") or page.get("link")
            content = page.get("content") or page.get("snippet") or ""
            source_url = page.get("link") or page.get("url") or ""
            if not any([title, content, source_url]):
                continue
            timestamp = self._safe_parse_datetime(page.get("date"))

            item = {
                "agent_name": self.NAME,
                "title": title or "META Result",
                "content": content,
                "source_url": source_url,
                "source_name": page.get("website") or "Meta Search",
                "category": None,
                "key_entities": [],
                "relevance_score": page.get("score"),
                "significance": None,
                "agent_metadata": page,
            }
            if timestamp:
                item["timestamp"] = timestamp
            items.append(item)
        return items

    # -- QIANFAN --------------------------------------------------------------
    def _parse_qianfan_response_items(self, raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        payload = self._unwrap_response_payload(raw_response)
        references = payload.get("references", [])
        items: List[Dict[str, Any]] = []

        for ref in references:
            if not isinstance(ref, dict):
                continue
            title = ref.get("title") or ref.get("website") or "QIANFAN Result"
            content = ref.get("content") or ""
            source_url = ref.get("url") or ""
            if not any([title, content, source_url]):
                continue
            timestamp = self._safe_parse_datetime(ref.get("date"))

            item = {
                "agent_name": self.NAME,
                "title": title,
                "content": content,
                "source_url": source_url,
                "source_name": ref.get("website") or ref.get("type") or "Qianfan",
                "category": "web",
                "key_entities": [],
                "relevance_score": None,
                "significance": None,
                "agent_metadata": ref,
            }
            if timestamp:
                item["timestamp"] = timestamp
            items.append(item)

        if items:
            return items

        # Fallback: create single record from assistant message content
        content = self._extract_first_message_content(raw_response)
        if content:
            return [{
                "agent_name": self.NAME,
                "title": "Qianfan Report",
                "content": content,
                "source_url": "",
                "source_name": "Qianfan",
                "category": None,
                "key_entities": [],
                "relevance_score": None,
                "significance": None,
                "agent_metadata": payload,
            }]
        return []

    # =========================================================================
    # Helpers
    # =========================================================================

    def _unwrap_response_payload(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """Return the main payload dict regardless of nesting."""
        payload = raw_response if isinstance(raw_response, dict) else {}
        if isinstance(payload.get("response"), dict):
            payload = payload["response"]
        return payload if isinstance(payload, dict) else {}

    def _extract_choices(self, raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        payload = self._unwrap_response_payload(raw_response)
        choices = payload.get("choices")
        if isinstance(choices, list):
            return [choice for choice in choices if isinstance(choice, dict)]
        return []

    def _extract_first_message_content(self, raw_response: Dict[str, Any]) -> Optional[str]:
        for choice in self._extract_choices(raw_response):
            message = choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    stripped = content.strip()
                    if stripped:
                        return stripped
        return None

    def _extract_news_items_from_choices(self, raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        news_items: List[Dict[str, Any]] = []
        for choice in self._extract_choices(raw_response):
            message = choice.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            data = self._extract_json_from_content(content)
            if data and isinstance(data.get("news_items"), list):
                for item in data["news_items"]:
                    if isinstance(item, dict):
                        news_items.append(item)
        return news_items

    def _extract_json_from_content(self, content: Optional[str]) -> Optional[Dict[str, Any]]:
        if not isinstance(content, str):
            return None
        text = content.strip()
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        block = match.group(1) if match else text
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            return None

    def _normalize_structured_news_item(self, entry: Dict[str, Any], default_source: str) -> Dict[str, Any]:
        title = entry.get("title") or entry.get("summary") or entry.get("content")
        content = entry.get("content") or entry.get("summary") or ""
        source_url = entry.get("source_link") or entry.get("source_url") or ""
        if not any([title, content, source_url]):
            return {}
        timestamp = self._safe_parse_datetime(entry.get("timestamp"))

        item = {
            "agent_name": self.NAME,
            "title": title or f"{default_source} Result",
            "content": content,
            "source_url": source_url,
            "source_name": entry.get("source_type") or default_source,
            "category": entry.get("category"),
            "key_entities": entry.get("key_entities") or [],
            "relevance_score": None,
            "significance": entry.get("significance"),
            "agent_metadata": entry,
        }
        if timestamp:
            item["timestamp"] = timestamp
        return item

    def _safe_parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value or not isinstance(value, str):
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        cleaned = cleaned.replace("Z", "+00:00")
        # Handle date-only by appending time
        if re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned):
            cleaned = f"{cleaned}T00:00:00"
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            return None
