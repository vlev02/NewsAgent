#!/usr/bin/env python3
"""
Test script to verify scheduler components work correctly.

Unit tests for Scheduler, SchedulerConfig, and action modules.
"""

import unittest
from pathlib import Path

from src.scheduler import Scheduler
from src.scheduler.config import SchedulerConfig, get_agent_configs
from src.scheduler.interactive import (
    print_header, print_section, print_success, print_error
)
from src.scheduler.actions import (
    ExploreAction, SubmitQueryAction, ExportAction,
    StatsAction, SettingsAction
)
from src.database import SQLite3Backend, DatabaseManager


class TestSchedulerImports(unittest.TestCase):
    """Test that all scheduler modules can be imported"""

    def test_scheduler_import(self):
        """Test importing Scheduler"""
        self.assertIsNotNone(Scheduler)

    def test_scheduler_config_import(self):
        """Test importing SchedulerConfig"""
        self.assertIsNotNone(SchedulerConfig)

    def test_agent_configs_function_import(self):
        """Test importing get_agent_configs function"""
        self.assertIsNotNone(get_agent_configs)

    def test_interactive_imports(self):
        """Test importing interactive functions"""
        self.assertIsNotNone(print_header)
        self.assertIsNotNone(print_section)
        self.assertIsNotNone(print_success)
        self.assertIsNotNone(print_error)

    def test_actions_import(self):
        """Test importing action classes"""
        self.assertIsNotNone(ExploreAction)
        self.assertIsNotNone(SubmitQueryAction)
        self.assertIsNotNone(ExportAction)
        self.assertIsNotNone(StatsAction)
        self.assertIsNotNone(SettingsAction)


class TestSchedulerConfiguration(unittest.TestCase):
    """Test scheduler configuration"""

    def test_config_from_env(self):
        """Test loading configuration from environment"""
        config = SchedulerConfig.from_env()
        self.assertIsNotNone(config)

    def test_config_has_database_path(self):
        """Test that configuration has database path"""
        config = SchedulerConfig.from_env()
        self.assertIsNotNone(config.database_path)
        self.assertTrue(len(config.database_path) > 0)

    def test_get_agent_configs_returns_list(self):
        """Test that get_agent_configs returns a dict"""
        agents_config = get_agent_configs()
        # get_agent_configs returns a dict, not a list
        self.assertIsInstance(agents_config, dict)

    def test_get_agent_configs_count(self):
        """Test that all agents are configured"""
        agents_config = get_agent_configs()
        self.assertEqual(len(agents_config), 6)

    def test_config_is_dict(self):
        """Test that configuration object is a SchedulerConfig"""
        config = SchedulerConfig.from_env()
        # SchedulerConfig is a dataclass, not a dict
        self.assertIsNotNone(config)
        self.assertTrue(hasattr(config, 'database_path'))


class TestDatabaseConnection(unittest.TestCase):
    """Test database connection and operations"""

    def setUp(self):
        """Set up in-memory database for testing"""
        self.db = DatabaseManager(SQLite3Backend(":memory:"))
        self.db.connect()

    def tearDown(self):
        """Clean up database"""
        try:
            self.db.disconnect()
        except Exception:
            pass

    def test_database_connection(self):
        """Test database connection"""
        self.assertIsNotNone(self.db)

    def test_database_get_stats(self):
        """Test database statistics"""
        stats = self.db.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_queries', stats)
        self.assertIn('total_items', stats)

    def test_database_stats_values(self):
        """Test that stats have correct types"""
        stats = self.db.get_stats()
        self.assertIsInstance(stats['total_queries'], int)
        self.assertIsInstance(stats['total_items'], int)

    def test_initial_stats_are_zero(self):
        """Test that initial stats are zero"""
        stats = self.db.get_stats()
        self.assertEqual(stats['total_queries'], 0)
        self.assertEqual(stats['total_items'], 0)


class TestSchedulerInitialization(unittest.TestCase):
    """Test scheduler initialization"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DatabaseManager(SQLite3Backend(":memory:"))
        self.db.connect()
        self.config = SchedulerConfig.from_env()
        self.agents_config = get_agent_configs()

    def tearDown(self):
        """Clean up"""
        try:
            self.db.disconnect()
        except Exception:
            pass

    def test_scheduler_initialization(self):
        """Test scheduler initialization"""
        scheduler = Scheduler(self.config, self.agents_config)
        self.assertIsNotNone(scheduler)

    def test_scheduler_has_actions(self):
        """Test that scheduler has actions"""
        scheduler = Scheduler(self.config, self.agents_config)
        self.assertTrue(hasattr(scheduler, 'actions'))
        self.assertGreater(len(scheduler.actions), 0)

    def test_scheduler_actions_count(self):
        """Test that scheduler has 5 actions"""
        scheduler = Scheduler(self.config, self.agents_config)
        # Should have all 5 actions
        self.assertEqual(len(scheduler.actions), 5)

    def test_scheduler_actions_have_names(self):
        """Test that all actions have names"""
        scheduler = Scheduler(self.config, self.agents_config)
        for action in scheduler.actions:
            self.assertTrue(hasattr(action, 'name'))
            self.assertTrue(len(action.name) > 0)

    def test_scheduler_actions_have_descriptions(self):
        """Test that all actions have descriptions"""
        scheduler = Scheduler(self.config, self.agents_config)
        for action in scheduler.actions:
            self.assertTrue(hasattr(action, 'description'))
            self.assertTrue(len(action.description) > 0)

    def test_scheduler_cleanup(self):
        """Test scheduler cleanup"""
        scheduler = Scheduler(self.config, self.agents_config)
        # Should not raise exception
        scheduler.cleanup()


class TestActionInstantiation(unittest.TestCase):
    """Test that all actions can be instantiated"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DatabaseManager(SQLite3Backend(":memory:"))
        self.db.connect()
        self.agents_config = get_agent_configs()

    def tearDown(self):
        """Clean up"""
        try:
            self.db.disconnect()
        except Exception:
            pass

    def test_explore_action_creation(self):
        """Test ExploreAction instantiation"""
        action = ExploreAction(self.db, self.agents_config)
        self.assertIsNotNone(action)
        # Action name is "Explore Recent Research", not just "Explore"
        self.assertEqual(action.name, "Explore Recent Research")

    def test_submit_query_action_creation(self):
        """Test SubmitQueryAction instantiation"""
        action = SubmitQueryAction(self.db, self.agents_config)
        self.assertIsNotNone(action)
        self.assertEqual(action.name, "Submit Query")

    def test_export_action_creation(self):
        """Test ExportAction instantiation"""
        action = ExportAction(self.db, self.agents_config)
        self.assertIsNotNone(action)
        self.assertEqual(action.name, "Export Results")

    def test_stats_action_creation(self):
        """Test StatsAction instantiation"""
        action = StatsAction(self.db, self.agents_config)
        self.assertIsNotNone(action)
        # Action name is "View Statistics", not just "Statistics"
        self.assertEqual(action.name, "View Statistics")

    def test_settings_action_creation(self):
        """Test SettingsAction instantiation"""
        action = SettingsAction(self.db, self.agents_config)
        self.assertIsNotNone(action)
        self.assertEqual(action.name, "Settings")

    def test_all_actions_creation(self):
        """Test creating all actions"""
        actions = [
            ExploreAction(self.db, self.agents_config),
            SubmitQueryAction(self.db, self.agents_config),
            ExportAction(self.db, self.agents_config),
            StatsAction(self.db, self.agents_config),
            SettingsAction(self.db, self.agents_config),
        ]

        self.assertEqual(len(actions), 5)
        for action in actions:
            self.assertIsNotNone(action)
            self.assertTrue(hasattr(action, 'name'))
            self.assertTrue(hasattr(action, 'description'))


class TestInteractiveFunctions(unittest.TestCase):
    """Test interactive UI functions"""

    def test_print_header_callable(self):
        """Test that print_header is callable"""
        self.assertTrue(callable(print_header))

    def test_print_section_callable(self):
        """Test that print_section is callable"""
        self.assertTrue(callable(print_section))

    def test_print_success_callable(self):
        """Test that print_success is callable"""
        self.assertTrue(callable(print_success))

    def test_print_error_callable(self):
        """Test that print_error is callable"""
        self.assertTrue(callable(print_error))

    def test_print_header_no_error(self):
        """Test that print_header doesn't raise exception"""
        try:
            print_header("Test Header")
        except Exception as e:
            self.fail(f"print_header raised exception: {e}")

    def test_print_section_no_error(self):
        """Test that print_section doesn't raise exception"""
        try:
            # print_section takes 1 argument (title), not 2
            print_section("Test Section")
        except Exception as e:
            self.fail(f"print_section raised exception: {e}")


class TestSchedulerIntegration(unittest.TestCase):
    """Integration tests for scheduler components"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = DatabaseManager(SQLite3Backend(":memory:"))
        self.db.connect()
        self.config = SchedulerConfig.from_env()
        self.agents_config = get_agent_configs()

    def tearDown(self):
        """Clean up"""
        try:
            self.db.disconnect()
        except Exception:
            pass

    def test_full_scheduler_workflow(self):
        """Test complete scheduler workflow"""
        # Create scheduler
        scheduler = Scheduler(self.config, self.agents_config)
        self.assertIsNotNone(scheduler)

        # Verify actions are registered
        self.assertEqual(len(scheduler.actions), 5)

        # Verify each action is callable
        for action in scheduler.actions:
            self.assertTrue(hasattr(action, 'execute'))

        # Cleanup
        scheduler.cleanup()

    def test_database_and_actions_together(self):
        """Test database works with actions"""
        # Create actions with database
        actions = [
            ExploreAction(self.db, self.agents_config),
            SubmitQueryAction(self.db, self.agents_config),
            ExportAction(self.db, self.agents_config),
            StatsAction(self.db, self.agents_config),
            SettingsAction(self.db, self.agents_config),
        ]

        # Verify all actions have access to database
        for action in actions:
            self.assertIsNotNone(action.db)

    def test_agents_config_used_by_actions(self):
        """Test that agents config is accessible through actions"""
        action = SettingsAction(self.db, self.agents_config)
        self.assertIsNotNone(action.agents_config)
        self.assertEqual(len(action.agents_config), 6)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
