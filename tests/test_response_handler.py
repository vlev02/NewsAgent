#!/usr/bin/env python3
"""
Focused tests for the fake_response_handler decorator.

These tests spin up a fake filesystem through tempfile + a stub API class to
validate cache miss/hit behavior without touching the real NewsAgent data.
"""

import json
import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from src.dataclasses import QueryRequest
from src.decorators import fake_response_handler
import src.decorators.response_handler as response_handler_module
from src.debug_config import DebugConfig
from src.utils.fake_response_manager import FakeResponseManager

manager_module = import_module("src.utils.fake_response_manager")


FAKE_AGENT_NAME = "FAKE"
FAKE_URL = "https://api.fake.test"
FAKE_METHOD = "POST"
FAKE_DESCRIPTION = "default"


class TestFakeResponseHandlerDecorator(unittest.TestCase):
    """Test fake_response_handler behavior with a fake API and filesystem."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fake_manager = FakeResponseManager(base_dir=self.temp_dir.name)

        # Preserve global state so other tests remain unaffected.
        self._original_manager_module = manager_module.fake_response_manager
        self._original_decorator_manager = response_handler_module.fake_response_manager
        manager_module.fake_response_manager = self.fake_manager
        response_handler_module.fake_response_manager = self.fake_manager

        self._debug_snapshot = {
            "DEBUG": DebugConfig.DEBUG,
            "fake_response_enabled": DebugConfig.fake_response_enabled,
            "fake_response_update": DebugConfig.fake_response_update,
            "fake_response_interact": DebugConfig.fake_response_interact,
            "_skip": DebugConfig._skip_interaction_for_session,
        }

        DebugConfig.DEBUG = False
        DebugConfig.fake_response_enabled = True
        DebugConfig.fake_response_update = True
        DebugConfig.fake_response_interact = False
        DebugConfig._skip_interaction_for_session = False

    def tearDown(self):
        manager_module.fake_response_manager = self._original_manager_module
        response_handler_module.fake_response_manager = self._original_decorator_manager

        DebugConfig.DEBUG = self._debug_snapshot["DEBUG"]
        DebugConfig.fake_response_enabled = self._debug_snapshot["fake_response_enabled"]
        DebugConfig.fake_response_update = self._debug_snapshot["fake_response_update"]
        DebugConfig.fake_response_interact = self._debug_snapshot["fake_response_interact"]
        DebugConfig._skip_interaction_for_session = self._debug_snapshot["_skip"]

        self.temp_dir.cleanup()

    def _build_fake_agent(self):
        """Create a stub agent whose API call is decorated for caching tests."""

        class FakeAgent:
            def __init__(self):
                self.call_count = 0
                self.config = type(
                    "Config",
                    (),
                    {"agent_name": FAKE_AGENT_NAME, "api_endpoint": FAKE_URL},
                )()

            @fake_response_handler(
                agent_name=FAKE_AGENT_NAME,
                url=FAKE_URL,
                method=FAKE_METHOD,
                description=FAKE_DESCRIPTION,
            )
            def submit_request(self, query):
                self.call_count += 1
                return {
                    "response": f"call-{self.call_count}",
                    "query_id": query.query_id,
                }

        return FakeAgent()

    def _make_query(self) -> QueryRequest:
        return QueryRequest(
            query_fields=["ai"],
            query_topics=["agents"],
            source_agents=[FAKE_AGENT_NAME],
        )

    def test_cache_miss_persists_response_to_fake_fs(self):
        """Cache miss should call the fake API and write a cache file."""
        agent = self._build_fake_agent()
        query = self._make_query()

        result = agent.submit_request(query)
        self.assertEqual(agent.call_count, 1)
        self.assertEqual(result["response"], "call-1")

        hash_value = self.fake_manager.generate_hash(FAKE_URL, FAKE_METHOD, FAKE_DESCRIPTION)
        response_path = Path(self.temp_dir.name) / FAKE_AGENT_NAME.lower() / f"{hash_value}.json"
        self.assertTrue(response_path.exists(), "Cache file should exist in the fake filesystem")

        with open(response_path, "r", encoding="utf-8") as f:
            cached_payload = json.load(f)

        self.assertIn("response_body", cached_payload)
        self.assertEqual(cached_payload["response_body"], result)

    def test_cached_response_skips_real_api_call(self):
        """Cache hit should skip the fake API call and return cached data."""
        agent = self._build_fake_agent()
        query = self._make_query()

        first_result = agent.submit_request(query)
        self.assertEqual(agent.call_count, 1)

        cached_result = agent.submit_request(query)
        self.assertEqual(
            agent.call_count,
            1,
            "Second call should use the cached response instead of hitting the API",
        )
        self.assertIn("response_body", cached_result)
        self.assertEqual(cached_result["response_body"], first_result)

    def test_disabling_fake_response_bypasses_cache(self):
        """Turning off fake responses should always call the real API logic."""
        agent = self._build_fake_agent()
        query = self._make_query()

        agent.submit_request(query)
        self.assertEqual(agent.call_count, 1)

        DebugConfig.fake_response_enabled = False
        real_result = agent.submit_request(query)

        self.assertEqual(agent.call_count, 2, "Real API should run when fake responses are disabled")
        self.assertNotIn("response_body", real_result)
        self.assertEqual(real_result["response"], "call-2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
