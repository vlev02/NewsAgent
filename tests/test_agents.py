"""
Test suite for NewsAgent agents.

Tests all agent implementations including:
- Agent discovery and initialization
- Request body generation
- Header construction
- API key management
- HTTP request configuration
"""

import os
import sys
import unittest
from pathlib import Path

# Disable proxy for tests
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agents import get_agent_manager
from src.utils.simu_request import SimuRequest


class TestAgentDiscovery(unittest.TestCase):
    """Test agent auto-discovery and initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = get_agent_manager()
        self.marketplace = self.manager.agent_marketplace

    def test_agents_discovered(self):
        """Test that all agents are auto-discovered."""
        self.assertGreater(len(self.marketplace), 0, "No agents discovered")

    def test_all_agents_have_valid_types(self):
        """Test that all discovered agents have valid types."""
        valid_types = {'LLM_SEARCH', 'REST_API', 'SOCIAL_MEDIA'}

        for agent_name, agent_type in self.marketplace.items():
            self.assertIn(
                agent_type, valid_types,
                f"{agent_name} has invalid type: {agent_type}"
            )

    def test_agent_names_are_strings(self):
        """Test that all agent names are valid strings."""
        for agent_name in self.marketplace.keys():
            self.assertIsInstance(agent_name, str)
            self.assertGreater(len(agent_name), 0)


class TestAgentConfiguration(unittest.TestCase):
    """Test agent configuration loading and setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = get_agent_manager()
        self.marketplace = self.manager.agent_marketplace
        self.agent_names = sorted(self.marketplace.keys())

    def test_all_agent_configs_load(self):
        """Test that configuration loads for all discovered agents."""
        for agent_name in self.agent_names:
            with self.subTest(agent=agent_name):
                config = self.manager.get_agent_config(agent_name)
                self.assertIsNotNone(config)
                self.assertEqual(config.agent_name, agent_name)

    def test_all_agent_configs_have_endpoints(self):
        """Test that all agents have valid API endpoints."""
        for agent_name in self.agent_names:
            with self.subTest(agent=agent_name):
                config = self.manager.get_agent_config(agent_name)
                self.assertIsNotNone(config.api_endpoint)
                self.assertTrue(
                    config.api_endpoint.startswith('https://'),
                    f"{agent_name} endpoint must be HTTPS"
                )

    def test_all_agent_configs_have_types(self):
        """Test that all agents have valid types in configuration."""
        valid_types = {'LLM_SEARCH', 'REST_API', 'SOCIAL_MEDIA'}
        for agent_name in self.agent_names:
            with self.subTest(agent=agent_name):
                config = self.manager.get_agent_config(agent_name)
                self.assertIn(config.agent_type, valid_types)

    def test_all_agent_configs_have_body_params(self):
        """Test that all agents have request body parameters."""
        for agent_name in self.agent_names:
            with self.subTest(agent=agent_name):
                config = self.manager.get_agent_config(agent_name)
                self.assertIsInstance(config.request_body_params, dict)
                self.assertGreater(len(config.request_body_params), 0)


class TestAgentCreation(unittest.TestCase):
    """Test agent instantiation and initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = get_agent_manager()
        self.marketplace = self.manager.agent_marketplace
        self.agent_names = sorted(self.marketplace.keys())

    def test_create_all_agents(self):
        """Test that all discovered agents can be instantiated."""
        for agent_name in self.agent_names:
            with self.subTest(agent=agent_name):
                agent = self.manager.create_agent(agent_name)
                self.assertIsNotNone(agent)
                self.assertEqual(agent.NAME, agent_name)


class TestRequestBodyGeneration(unittest.TestCase):
    """Test HTTP request body generation for all agents."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = get_agent_manager()
        self.marketplace = self.manager.agent_marketplace
        self.agent_names = sorted(self.marketplace.keys())

    def test_all_agents_generate_request_body(self):
        """Test that all agents generate valid request bodies."""
        for agent_name in self.agent_names:
            with self.subTest(agent=agent_name):
                agent = self.manager.create_agent(agent_name)
                body = agent.request_body
                self.assertIsInstance(body, dict)
                self.assertGreater(len(body), 0)

    def test_llm_agents_have_messages(self):
        """Test that LLM agents include messages in request body."""
        for agent_name in self.agent_names:
            agent_type = self.marketplace[agent_name]
            if agent_type == 'LLM_SEARCH':
                with self.subTest(agent=agent_name):
                    agent = self.manager.create_agent(agent_name)
                    body = agent.request_body
                    self.assertIn('messages', body)
                    self.assertEqual(len(body['messages']), 1)
                    self.assertEqual(body['messages'][0]['role'], 'user')

    def test_rest_api_agents_have_query_params(self):
        """Test that REST_API agents have query parameters."""
        for agent_name in self.agent_names:
            agent_type = self.marketplace[agent_name]
            if agent_type == 'REST_API':
                with self.subTest(agent=agent_name):
                    agent = self.manager.create_agent(agent_name)
                    body = agent.request_body
                    # REST API should have at least one query parameter
                    self.assertGreater(len(body), 0)


class TestHeaderGeneration(unittest.TestCase):
    """Test HTTP header generation for all agents."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = get_agent_manager()
        self.marketplace = self.manager.agent_marketplace
        self.agent_names = sorted(self.marketplace.keys())

    def test_all_agent_headers(self):
        """Test that all agents generate valid authorization headers."""
        for agent_name in self.agent_names:
            with self.subTest(agent=agent_name):
                agent = self.manager.create_agent(agent_name)
                headers = agent.get_header_dict()
                self.assertIsInstance(headers, dict)

                # Check for authorization header (standard or custom)
                has_auth = 'Authorization' in headers or 'X-Appbuilder-Authorization' in headers
                self.assertTrue(has_auth,
                              f"{agent_name} must have Authorization or X-Appbuilder-Authorization header")

    def test_agent_headers_have_bearer_tokens(self):
        """Test that all agent headers contain valid Bearer tokens."""
        for agent_name in self.agent_names:
            with self.subTest(agent=agent_name):
                agent = self.manager.create_agent(agent_name)
                headers = agent.get_header_dict()

                # Find which auth header is used
                auth_header = None
                auth_key = None
                if 'Authorization' in headers:
                    auth_header = headers['Authorization']
                    auth_key = 'Authorization'
                elif 'X-Appbuilder-Authorization' in headers:
                    auth_header = headers['X-Appbuilder-Authorization']
                    auth_key = 'X-Appbuilder-Authorization'

                self.assertIsNotNone(auth_header,
                                   f"{agent_name} must have an authorization header")
                self.assertIsNotNone(auth_key,
                                   f"{agent_name} must have a recognized authorization key")
                self.assertTrue(auth_header.startswith('Bearer '),
                              f"{agent_name} {auth_key} must start with 'Bearer '")


class TestSimuRequest(unittest.TestCase):
    """Test SimuRequest configuration."""

    def test_simu_request_status(self):
        """Test SimuRequest status reporting."""
        status = SimuRequest.status()
        self.assertIsInstance(status, dict)
        self.assertIn('simu_call', status)
        self.assertIn('update_response', status)
        self.assertIn('log_calls', status)
        self.assertIn('persist_dir', status)

    def test_simu_request_has_valid_config(self):
        """Test SimuRequest has valid configuration values."""
        status = SimuRequest.status()
        self.assertIn(status['simu_call'], [0, 1])
        self.assertIn(status['update_response'], [0, 1])
        self.assertIn(status['log_calls'], [0, 1])
        self.assertIsNotNone(status['persist_dir'])


class TestEnvironmentLoading(unittest.TestCase):
    """Test environment variable loading."""

    def test_env_variables_loaded(self):
        """Test that API keys are available from environment."""
        # At least one API key should be loaded
        api_keys_found = []
        for key in ['BOCHA_API_KEY', 'META_API_KEY', 'XUNFEI_APPID', 'XUNFEI_APIKey',
                    'HUNYUAN_SECRET_ID', 'HUNYUAN_SECRET_KEY', 'QIANFAN_ACCESS_KEY',
                    'QIANFAN_SECRET_KEY']:
            if os.environ.get(key):
                api_keys_found.append(key)

        self.assertGreater(len(api_keys_found), 0,
                          "No API keys found in environment")

    def test_proxy_disabled(self):
        """Test that proxy environment variables are disabled."""
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in proxy_vars:
            self.assertIsNone(os.environ.get(var),
                            f"Proxy variable {var} should be disabled")


if __name__ == '__main__':
    unittest.main(verbosity=2)
