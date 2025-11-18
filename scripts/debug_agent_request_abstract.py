#!/usr/bin/env python3
"""
Abstract base class for agent-specific debug scripts.

This module provides reusable components for creating agent-specific debug scripts
with cache verification, parameter configuration, and interactive testing.

It can be inherited by:
- debug_agent_request_bocha.py
- debug_agent_request_meta.py
- debug_agent_request_xunfei.py
- etc.

Usage:
    See debug_agent_request_bocha.py or debug_agent_request_meta.py for implementation examples.
"""

from pathlib import Path
import sys
import json
import time
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.scheduler.scheduler_settings import SchedulerSettings, PathManager
from src.debug_config import DebugConfig
from src.dataclasses import QueryRequest
from src.dataclasses.config import AGENT_CONFIGS


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def print_section(title: str):
    """Print a section header"""
    print()
    print("=" * 100)
    print(f" {title}")
    print("=" * 100)


def print_header(title: str):
    """Print a main header"""
    print("\n")
    print("╔" + "═" * 98 + "╗")
    print(f"║ {title:<96} ║")
    print("╚" + "═" * 98 + "╝")


# ==============================================================================
# ABSTRACT DEBUG AGENT CLASS
# ==============================================================================

class DebugAgentScript(ABC):
    """
    Abstract base class for agent-specific debug scripts.

    Provides common functionality for:
    - Parameter configuration with modification loops
    - Request preview and confirmation
    - Cache verification
    - Retry/modify/finish logic

    Subclasses must implement:
    - get_default_configs(): Return default parameters for this agent
    - build_query_from_params(): Convert params to agent-specific query format
    - submit_request(): Execute the actual API call
    """

    # ==============================================================================
    # CONFIGURATION - Override in subclass
    # ==============================================================================

    VERIFY_CACHE_UPDATE = True
    CACHE_UPDATE_TIMEOUT_SECONDS = 3
    VERIFY_CACHE_MODIFICATION = True
    CACHE_MOD_TIMEOUT_SECONDS = 3

    def __init__(self, agent_name: str):
        """
        Initialize the debug script for a specific agent.

        Args:
            agent_name: Name of the agent (e.g., "BOCHA", "META", "XUNFEI")
        """
        self.agent_name = agent_name
        self.config = AGENT_CONFIGS.get(agent_name)
        if not self.config:
            raise ValueError(f"Agent {agent_name} not found in AGENT_CONFIGS")

    # ==============================================================================
    # ABSTRACT METHODS - Must be implemented by subclass
    # ==============================================================================

    @abstractmethod
    def get_default_configs(self) -> Dict[str, Any]:
        """
        Return default configuration parameters for this agent.

        Returns:
            Dict with keys like: query_fields, query_topics, days_back, max_results, language, etc.
        """
        pass

    @abstractmethod
    def build_query_from_params(self, params: Dict[str, Any]) -> Union[str, Dict]:
        """
        Convert parameters to agent-specific query format.

        Args:
            params: Configuration dictionary from build_request_params()

        Returns:
            Agent-specific query (string for text APIs, dict for structured APIs)
        """
        pass

    @abstractmethod
    def submit_request(self, query: Union[str, Dict], params: Dict[str, Any]) -> Optional[Dict]:
        """
        Execute the actual API call.

        Args:
            query: Query built by build_query_from_params()
            params: Original parameters

        Returns:
            Raw API response or None if failed
        """
        pass

    # ==============================================================================
    # COMMON METHODS - Reusable across all agents
    # ==============================================================================

    def build_request_params(self) -> Dict[str, Any]:
        """Build request parameters with defaults and user customization - with modification loop"""
        params = self.get_default_configs().copy()

        while True:
            print_section("Step 2: Configure Request Parameters")

            print("Current parameters:")
            print(f"  query_fields: {params['query_fields']}")
            print(f"  query_topics: {params['query_topics']}")
            print(f"  days_back: {params['days_back']}")
            print(f"  max_results: {params['max_results']}")
            print(f"  language: {params['language']}")
            print()

            customize = input("Modify parameters? (y/n): ").strip().lower()

            if customize == 'y':
                # Allow customization with defaults shown
                print("\nEnter new values (press Enter to keep current):")

                fields_default = ", ".join(params['query_fields'])
                fields_input = input(f"  query_fields [default: {fields_default}] (comma-separated): ").strip()
                if fields_input:
                    params['query_fields'] = [f.strip() for f in fields_input.split(',')]

                topics_default = ", ".join(params['query_topics'])
                topics_input = input(f"  query_topics [default: {topics_default}] (comma-separated): ").strip()
                if topics_input:
                    params['query_topics'] = [t.strip() for t in topics_input.split(',')]

                days_default = params['days_back']
                days_input = input(f"  days_back [default: {days_default}] (number): ").strip()
                if days_input:
                    try:
                        params['days_back'] = int(days_input)
                    except ValueError:
                        print(f"⚠ Invalid days_back, using current: {params['days_back']}")

                results_default = params['max_results']
                results_input = input(f"  max_results [default: {results_default}] (number): ").strip()
                if results_input:
                    try:
                        params['max_results'] = int(results_input)
                    except ValueError:
                        print(f"⚠ Invalid max_results, using current: {params['max_results']}")

                lang_default = params['language']
                lang_input = input(f"  language [default: {lang_default}] (zh/en): ").strip().lower()
                if lang_input in ['zh', 'en']:
                    params['language'] = lang_input

                print()
                print("✓ Parameters updated")
                print()
                # Loop back to show updated values
            else:
                # User confirmed - exit loop
                print(f"✓ Parameters confirmed")
                print()
                break

        return params

    def display_complete_request_report(self, params: Dict[str, Any]):
        """Display complete request report with all details"""
        print_section("Step 3: Complete Request Report")

        print("REQUEST DETAILS:")
        print()

        # API endpoint and method
        print("API Configuration:")
        print(f"  Endpoint: {self.config.api_endpoint}")
        print(f"  Agent Type: {self.config.agent_type}")
        print()

        # Request parameters
        print("Request Parameters:")
        print(f"  Query Fields: {params.get('query_fields', [])}")
        print(f"  Query Topics: {params.get('query_topics', [])}")
        print(f"  Days Back: {params.get('days_back', 7)}")
        print(f"  Max Results: {params.get('max_results', 5)}")
        print(f"  Language: {params.get('language', 'zh')}")
        print()

        # Display current fake response flag states
        print("Current Fake Response Flags (from DebugConfig):")
        print(f"  fake_response_enabled: {DebugConfig.fake_response_enabled}")
        print(f"  fake_response_update: {DebugConfig.fake_response_update}")
        print(f"  fake_response_interact: {DebugConfig.fake_response_interact}")
        print()

    def display_and_configure_flags(self):
        """Display fake response flags and allow user to modify them - with modification loop"""
        while True:
            print_section("Step 4: Fake Response Flags Configuration")

            print("Current Fake Response Flags:")
            print(f"  fake_response_enabled: {DebugConfig.fake_response_enabled}")
            print(f"    └─ Whether to use cached responses at all")
            print()
            print(f"  fake_response_update: {DebugConfig.fake_response_update}")
            print(f"    └─ Whether to UPDATE cache when enabled=True")
            print()
            print(f"  fake_response_interact: {DebugConfig.fake_response_interact}")
            print(f"    └─ Whether to prompt user for response handling choices")
            print()

            change_flags = input("Change any flags? (y/n): ").strip().lower()

            if change_flags == 'y':
                print("\nEnter new values (press Enter to keep current):")
                print()

                enabled_input = input(f"  fake_response_enabled [current: {DebugConfig.fake_response_enabled}] (true/false): ").strip().lower()
                if enabled_input:
                    if enabled_input in ['true', 't', '1', 'yes', 'y']:
                        DebugConfig.fake_response_enabled = True
                    elif enabled_input in ['false', 'f', '0', 'no', 'n']:
                        DebugConfig.fake_response_enabled = False
                    else:
                        print(f"⚠ Invalid input, keeping current: {DebugConfig.fake_response_enabled}")

                update_input = input(f"  fake_response_update [current: {DebugConfig.fake_response_update}] (true/false): ").strip().lower()
                if update_input:
                    if update_input in ['true', 't', '1', 'yes', 'y']:
                        DebugConfig.fake_response_update = True
                    elif update_input in ['false', 'f', '0', 'no', 'n']:
                        DebugConfig.fake_response_update = False
                    else:
                        print(f"⚠ Invalid input, keeping current: {DebugConfig.fake_response_update}")

                interact_input = input(f"  fake_response_interact [current: {DebugConfig.fake_response_interact}] (true/false): ").strip().lower()
                if interact_input:
                    if interact_input in ['true', 't', '1', 'yes', 'y']:
                        DebugConfig.fake_response_interact = True
                    elif interact_input in ['false', 'f', '0', 'no', 'n']:
                        DebugConfig.fake_response_interact = False
                    else:
                        print(f"⚠ Invalid input, keeping current: {DebugConfig.fake_response_interact}")

                print()
                print("✓ Flags updated")
                print()
                # Loop continues to show updated values
            else:
                # User confirmed - exit loop
                print()
                print("✓ Flags confirmed")
                print()
                break

    def confirm_submission(self, params: Dict[str, Any]) -> bool:
        """Display final config summary with concrete request details and ask user to confirm"""
        print_section("Step 5: Final Submission Confirmation")

        print("FINAL REQUEST CONFIGURATION:")
        print()

        # Agent info
        print("Agent Information:")
        print(f"  Agent Name: {self.agent_name}")
        print(f"  Agent Type: {self.config.agent_type}")
        print()

        # HTTP Request Details
        print("HTTP Request Details:")
        print(f"  Endpoint: {self.config.api_endpoint}")
        print(f"  Method: POST")
        print()

        # Build request to show concrete details
        query = self.build_query_from_params(params)

        print("Request Body:")
        if isinstance(query, dict):
            import json
            print(json.dumps(query, indent=2, ensure_ascii=False))
        else:
            print(f"  Query String: {query}")
        print()

        # Request parameters (human-readable)
        print("Search Parameters:")
        print(f"  Query Fields: {params.get('query_fields', [])}")
        print(f"  Query Topics: {params.get('query_topics', [])}")
        print(f"  Days Back: {params.get('days_back', 7)}")
        print(f"  Max Results: {params.get('max_results', 5)}")
        print(f"  Language: {params.get('language', 'zh')}")
        print()

        # Fake response flags
        print("Fake Response Flags:")
        print(f"  fake_response_enabled: {DebugConfig.fake_response_enabled}")
        print(f"  fake_response_update: {DebugConfig.fake_response_update}")
        print(f"  fake_response_interact: {DebugConfig.fake_response_interact}")
        print()

        while True:
            response = input("Submit request? (y/n): ").strip().lower()
            if response in ['y', 'n']:
                return response == 'y'
            print("Please enter 'y' or 'n'")

    def ask_retry_or_finish(self) -> str:
        """Ask user to retry, modify, or finish"""
        print_section("End of Report")
        print("What would you like to do?")
        print("  (r)etry    - Run the same request again")
        print("  (m)odify   - Modify parameters and flags")
        print("  (f)inish   - Exit the debug script")
        print()

        while True:
            choice = input("Your choice (r/m/f): ").strip().lower()
            if choice in ['r', 'm', 'f']:
                return choice
            print("Please enter 'r', 'm', or 'f'")

    def verify_cache_file_updated(self, cache_file: Path, timeout_seconds: int = 3) -> bool:
        """
        Verify that cache file was updated within timeout.

        Uses timestamp-based verification (st_mtime) instead of file size
        to detect changes, as API responses may be identical size.
        """
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if cache_file.exists():
                # Check if file was modified recently
                file_mtime = cache_file.stat().st_mtime
                current_time = time.time()
                age_seconds = current_time - file_mtime

                # If file was modified within the last 2 seconds, it's fresh
                if age_seconds < 2:
                    print(f"✓ Cache file updated (age: {age_seconds:.1f}s)")
                    return True

            time.sleep(0.5)

        print(f"❌ Cache file was NOT updated within {timeout_seconds} seconds")
        return False

    def verify_cache_modification(self, cache_file: Path, original_mtime: float, timeout_seconds: int = 3) -> bool:
        """
        Verify that cache file was modified on re-submit.

        Checks if the file modification time changed, indicating a fresh API response.
        """
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if cache_file.exists():
                current_mtime = cache_file.stat().st_mtime

                if current_mtime > original_mtime:
                    print(f"✓ Cache file was modified (new mtime: {current_mtime})")
                    return True

            time.sleep(0.5)

        print(f"❌ Cache file was NOT modified within {timeout_seconds} seconds")
        return False

    def find_cache_file(self) -> Optional[Path]:
        """Find the cache file for this agent"""
        cache_dir = PathManager.get_agent_cache_dir(self.agent_name)
        if not cache_dir.exists():
            return None

        # Get the most recently modified cache file
        cache_files = list(cache_dir.glob("*"))
        if not cache_files:
            return None

        return max(cache_files, key=lambda p: p.stat().st_mtime)

    def display_response_summary(self, cache_file: Optional[Path]):
        """Display response summary and cache location"""
        print_section("Step 6: Response Summary")

        if cache_file and cache_file.exists():
            print(f"✓ Cache file found:")
            print(f"  Location: {cache_file}")
            print(f"  Size: {cache_file.stat().st_size} bytes")
            print(f"  Modified: {cache_file.stat().st_mtime}")
            print()
        else:
            print("⚠ Cache file not found")
            print()

    def display_final_summary(self, cache_file: Optional[Path]):
        """Display final summary"""
        print_section("VERIFICATION SUMMARY")

        if cache_file and cache_file.exists():
            print(f"✓ Cache file successfully created/updated")
            print(f"  Location: {cache_file}")
            print(f"  Size: {cache_file.stat().st_size} bytes")
        else:
            print("⚠ Cache file not found or not updated")

        print()

    def run(self):
        """
        Main execution flow for the debug script.

        Workflow:
        1. Configure parameters (with modification loop)
        2. Display complete request report
        3. Configure fake response flags (with modification loop)
        4. Confirm and submit request
        5. Verify cache updates
        6. Display final summary
        7. Retry/modify/finish options
        """
        print_header(f"AGENT DEBUG SCRIPT - {self.agent_name}")

        # Enable debug mode
        DebugConfig.DEBUG = True

        # Main loop for retry/modify
        params = None
        while True:
            # Step 2: Configure parameters (skip if retrying with same params)
            if params is None:
                params = self.build_request_params()

            # Step 3: Display complete request report
            self.display_complete_request_report(params)

            # Step 4: Display and configure fake response flags
            self.display_and_configure_flags()

            # Step 5: Confirm and submit
            if not self.confirm_submission(params):
                print("\n⚠ Request cancelled")
                return

            # Step 6: Submit request
            query = self.build_query_from_params(params)
            raw_response = self.submit_request(query, params)

            if raw_response is None:
                continue

            # Step 7: Find and display response
            cache_file = self.find_cache_file()
            self.display_response_summary(cache_file)

            # Step 8A: Verify cache file was updated
            if self.VERIFY_CACHE_UPDATE and cache_file:
                print_section("Step 7A: Verify Cache File Update")
                cache_updated = self.verify_cache_file_updated(cache_file, self.CACHE_UPDATE_TIMEOUT_SECONDS)
                if not cache_updated:
                    print()
                    print("❌ ERROR: Cache file was NOT updated within the timeout!")
                    print()
                    print("=" * 100)
                    choice = self.ask_retry_or_finish()
                    if choice == 'r':
                        continue
                    elif choice == 'm':
                        params = None
                        continue
                    else:
                        return

            # Final summary
            self.display_final_summary(cache_file)

            # Final status
            print_section("VERIFICATION RESULT")
            if self.VERIFY_CACHE_UPDATE:
                print("✓ Cache verification PASSED")
                print("✓ Fake response caching is working correctly")
            print()
            print("=" * 100)

            # Ask user what to do next
            choice = self.ask_retry_or_finish()
            if choice == 'r':
                # Retry with same params (don't reset params, loop back directly)
                continue
            elif choice == 'm':
                # Modify - reset params to trigger parameter configuration on next loop
                params = None
                continue
            else:
                # Finish
                break

        print("\n✓ Debug script completed")
