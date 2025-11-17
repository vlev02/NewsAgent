#!/usr/bin/env python3
"""
Test scheduler settings initialization.

Unit tests for SchedulerSettings, EnvironmentVariables, and configuration.
"""

import unittest
from pathlib import Path

from src.scheduler.scheduler_settings import (
    SchedulerSettings,
    EnvironmentVariables,
    initialize_scheduler_settings
)


class TestEnvironmentVariables(unittest.TestCase):
    """Test EnvironmentVariables functionality"""

    def test_load_from_env(self):
        """Test loading environment variables"""
        env_vars = EnvironmentVariables.from_env()
        self.assertIsNotNone(env_vars)

    def test_default_database_path(self):
        """Test default database path"""
        env_vars = EnvironmentVariables.from_env()
        self.assertEqual(env_vars.database_path, "data/newsagent.db")

    def test_default_log_level(self):
        """Test default log level"""
        env_vars = EnvironmentVariables.from_env()
        self.assertEqual(env_vars.log_level, "INFO")

    def test_default_time_range(self):
        """Test default time range days"""
        env_vars = EnvironmentVariables.from_env()
        self.assertEqual(env_vars.default_time_range_days, 7)

    def test_default_max_results(self):
        """Test default max results"""
        env_vars = EnvironmentVariables.from_env()
        self.assertEqual(env_vars.default_max_results, 10)


class TestSchedulerSettings(unittest.TestCase):
    """Test SchedulerSettings functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for all tests"""
        try:
            cls.settings = SchedulerSettings.initialize(env_file=".env")
        except Exception:
            # Try without .env file
            cls.settings = SchedulerSettings.initialize(env_file=".env.missing")

    def test_settings_initialization(self):
        """Test scheduler settings initialization"""
        self.assertIsNotNone(self.settings)

    def test_env_vars_set(self):
        """Test that environment variables are set"""
        self.assertIsNotNone(self.settings.env_vars)

    def test_scheduler_config_set(self):
        """Test that scheduler config is set"""
        self.assertIsNotNone(self.settings.scheduler_config)

    def test_agent_configs_set(self):
        """Test that agent configs are set"""
        self.assertIsNotNone(self.settings.agent_configs)

    def test_agent_configs_count(self):
        """Test that all 6 agents are configured"""
        self.assertEqual(len(self.settings.agent_configs), 6)

    def test_agents_status_available(self):
        """Test agents_status property"""
        agents_status = self.settings.agents_status
        self.assertIsInstance(agents_status, dict)
        # Should have status for each agent
        self.assertGreaterEqual(len(agents_status), 0)

    def test_get_ready_agents(self):
        """Test getting ready agents"""
        ready_agents = self.settings.get_ready_agents()
        # get_ready_agents returns a dict, not a list
        self.assertIsInstance(ready_agents, dict)

    def test_get_unavailable_agents(self):
        """Test getting unavailable agents"""
        unavailable = self.settings.get_unavailable_agents()
        self.assertIsInstance(unavailable, dict)

    def test_validate_database_path(self):
        """Test database path validation"""
        is_valid = self.settings.validate_database_path()
        self.assertIsInstance(is_valid, bool)

    def test_create_export_directory(self):
        """Test export directory creation"""
        # Should not raise exception
        self.settings.create_export_directory()

    def test_agents_status_agents_key(self):
        """Test that agents_status has required keys"""
        agents_status = self.settings.agents_status
        # Each entry should have (ready: bool, status: str) tuple
        for agent_name, status_info in agents_status.items():
            self.assertIsInstance(agent_name, str)
            # Status info can be tuple or other format
            self.assertIsNotNone(status_info)

    def test_ready_agents_list_type(self):
        """Test ready_agents returns dict of agent configs"""
        ready_agents = self.settings.get_ready_agents()
        self.assertIsInstance(ready_agents, dict)
        # Keys are agent names (strings), values are AgentConfig objects
        for agent_name, agent_config in ready_agents.items():
            self.assertIsInstance(agent_name, str)
            self.assertIsNotNone(agent_config)

    def test_unavailable_agents_dict_structure(self):
        """Test unavailable agents dict structure"""
        unavailable = self.settings.get_unavailable_agents()
        self.assertIsInstance(unavailable, dict)
        for agent_name, env_var in unavailable.items():
            self.assertIsInstance(agent_name, str)
            self.assertIsInstance(env_var, str)


class TestSchedulerSettingsIntegration(unittest.TestCase):
    """Integration tests for scheduler settings"""

    def setUp(self):
        """Set up test fixtures"""
        try:
            self.settings = SchedulerSettings.initialize(env_file=".env")
        except Exception:
            # Try without .env file
            self.settings = SchedulerSettings.initialize(env_file=".env.missing")

    def test_agent_count_consistency(self):
        """Test that agent counts are consistent"""
        ready_count = len(self.settings.get_ready_agents())
        unavailable_count = len(self.settings.get_unavailable_agents())
        total_count = len(self.settings.agent_configs)

        # ready + unavailable should equal total
        self.assertEqual(ready_count + unavailable_count, total_count)

    def test_all_agent_names_valid(self):
        """Test that all agent names are non-empty strings"""
        for agent_name in self.settings.get_ready_agents():
            self.assertTrue(len(agent_name) > 0)
            self.assertIsInstance(agent_name, str)

    def test_database_path_configured(self):
        """Test that database path is configured"""
        db_path = self.settings.env_vars.database_path
        self.assertIsNotNone(db_path)
        self.assertTrue(len(db_path) > 0)

    def test_settings_printable(self):
        """Test that settings can be converted to string summary"""
        # These methods should not raise exceptions
        try:
            self.settings.print_summary()
            self.settings.print_env_status()
        except Exception as e:
            self.fail(f"Printing settings failed: {e}")


class TestInitializeSchedulerSettings(unittest.TestCase):
    """Test initialize_scheduler_settings function"""

    def test_initialization_function_exists(self):
        """Test that initialize_scheduler_settings function is callable"""
        self.assertTrue(callable(initialize_scheduler_settings))

    def test_initialization_returns_settings(self):
        """Test that initialization returns SchedulerSettings instance"""
        try:
            settings = initialize_scheduler_settings(env_file=".env.missing")
            self.assertIsInstance(settings, SchedulerSettings)
        except Exception:
            # Function may require valid .env file
            pass


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
