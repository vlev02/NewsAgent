#!/usr/bin/env python3
"""
Test Fake Response System

Comprehensive tests for:
- Fake response manager MD5 hashing and file operations
- Response caching and retrieval
- Response updating (single file replacement)
- Decorator functionality
- Debug logging
- User interaction prompts

Unit tests using unittest framework.
"""

import unittest
from pathlib import Path

from src.utils.fake_response_manager import FakeResponseManager, fake_response_manager
from src.debug_config import DebugConfig
from src.utils.debug_logger import DebugLogger
from src.decorators import fake_response_handler
from src.decorators.response_handler import _ask_user_choice, _cache_response


class TestFakeResponseManager(unittest.TestCase):
    """Test FakeResponseManager module functionality"""

    def setUp(self):
        """Set up test fixtures"""
        DebugConfig.DEBUG = False

    def tearDown(self):
        """Clean up after tests"""
        DebugConfig.DEBUG = False

    def test_1_import_fake_response_manager(self):
        """Test 1: Import fake response manager"""
        self.assertIsNotNone(FakeResponseManager)
        self.assertIsNotNone(fake_response_manager)
        self.assertIsNotNone(DebugLogger)

    def test_2_md5_hash_generation_consistency(self):
        """Test 2a: MD5 hash generation produces consistent results"""
        hash1 = FakeResponseManager.generate_hash(
            "https://api.bocha.ai/search",
            "POST",
            "default"
        )
        hash2 = FakeResponseManager.generate_hash(
            "https://api.bocha.ai/search",
            "POST",
            "default"
        )
        self.assertEqual(hash1, hash2, "Same inputs should produce same hash")

    def test_2b_md5_hash_length(self):
        """Test 2b: MD5 hash should be 32 characters"""
        hash_value = FakeResponseManager.generate_hash(
            "https://api.bocha.ai/search",
            "POST",
            "default"
        )
        self.assertEqual(len(hash_value), 32, "MD5 hash should be 32 characters")

    def test_2c_md5_hash_different_descriptions(self):
        """Test 2c: Different descriptions produce different hashes"""
        hash1 = FakeResponseManager.generate_hash(
            "https://api.bocha.ai/search",
            "POST",
            "default"
        )
        hash3 = FakeResponseManager.generate_hash(
            "https://api.bocha.ai/search",
            "POST",
            "custom"
        )
        self.assertNotEqual(hash1, hash3, "Different descriptions should produce different hashes")

    def test_4a_debug_configuration_enable(self):
        """Test 4a: Debug configuration enable"""
        DebugConfig.enable_debug()
        self.assertTrue(DebugConfig.DEBUG)
        self.assertTrue(DebugConfig.fake_response_enabled)

    def test_4b_debug_configuration_disable(self):
        """Test 4b: Debug configuration disable"""
        DebugConfig.enable_debug()
        DebugConfig.disable_debug()
        self.assertFalse(DebugConfig.DEBUG)
        self.assertFalse(DebugConfig.fake_response_enabled)

    def test_4c_debug_configuration_update_mode(self):
        """Test 4c: Debug configuration update mode"""
        DebugConfig.set_update_mode(True)
        self.assertTrue(DebugConfig.fake_response_update)
        DebugConfig.set_update_mode(False)
        self.assertFalse(DebugConfig.fake_response_update)

    def test_5_directory_structure(self):
        """Test 5: Verifying directory structure"""
        fake_response_dir = Path("data/fake_response")
        agents = ["bocha", "xunfei", "hunyuan", "qianfan", "meta", "twitter"]

        for agent in agents:
            agent_dir = fake_response_dir / agent
            self.assertTrue(
                agent_dir.exists(),
                f"{agent} directory should exist at {agent_dir}"
            )

    def test_6_decorator_imports(self):
        """Test 6: Testing decorator imports"""
        self.assertIsNotNone(fake_response_handler)
        self.assertIsNotNone(_ask_user_choice)
        self.assertIsNotNone(_cache_response)

    def test_7_debug_logger(self):
        """Test 7: Testing debug logger"""
        logger = DebugLogger("test_module")
        self.assertIsNotNone(logger)

        # Test that logger respects DEBUG flag
        DebugConfig.DEBUG = False
        # Should not raise exceptions
        logger.info("This should not appear")
        logger.debug("This should not appear")
        logger.warning("This should not appear")
        logger.error("This should not appear")

        # Test with DEBUG enabled
        DebugConfig.DEBUG = True
        # Should not raise exceptions
        logger.info("This is an info message")
        logger.debug("This is a debug message")
        DebugConfig.DEBUG = False


class TestDebugConfig(unittest.TestCase):
    """Test DebugConfig class functionality"""

    def test_enable_debug_method(self):
        """Test enable_debug classmethod"""
        DebugConfig.disable_debug()
        DebugConfig.enable_debug()
        self.assertTrue(DebugConfig.DEBUG)
        self.assertTrue(DebugConfig.fake_response_enabled)
        self.assertTrue(DebugConfig.log_fake_response_hits)

    def test_disable_debug_method(self):
        """Test disable_debug classmethod"""
        DebugConfig.enable_debug()
        DebugConfig.disable_debug()
        self.assertFalse(DebugConfig.DEBUG)
        self.assertFalse(DebugConfig.fake_response_enabled)

    def test_enable_fake_responses(self):
        """Test enable_fake_responses method"""
        DebugConfig.disable_fake_responses()
        DebugConfig.enable_fake_responses()
        self.assertTrue(DebugConfig.fake_response_enabled)

    def test_disable_fake_responses(self):
        """Test disable_fake_responses method"""
        DebugConfig.enable_fake_responses()
        DebugConfig.disable_fake_responses()
        self.assertFalse(DebugConfig.fake_response_enabled)

    def test_enable_interactive(self):
        """Test enable_interactive method"""
        DebugConfig.disable_interactive()
        DebugConfig.enable_interactive()
        self.assertTrue(DebugConfig.fake_response_interact)

    def test_disable_interactive(self):
        """Test disable_interactive method"""
        DebugConfig.enable_interactive()
        DebugConfig.disable_interactive()
        self.assertFalse(DebugConfig.fake_response_interact)

    def test_get_config_summary(self):
        """Test get_config_summary method"""
        summary = DebugConfig.get_config_summary()
        self.assertIsInstance(summary, str)
        self.assertIn("Debug Configuration Summary", summary)
        self.assertIn("DEBUG", summary)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
