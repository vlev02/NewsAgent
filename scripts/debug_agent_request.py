#!/usr/bin/env python3
"""
Unified debug script for all agents - single file with integrated base class.

This script provides a single entry point for testing any agent with cache verification.
It automatically adapts to the selected agent's schema and configuration.

Features:
- Dynamic agent selection from existing schemas
- Schema-driven request body building via InteractiveFieldCollector
- Real-time request body preview and modification loop
- Unified workflow for all agents
- Cache verification and fake response handling

Step 2 Workflow (Configure Request Parameters):
┌─────────────────────────────────────────────────────┐
│ 1. Report current request body                       │
│    (initialized by schema defaults if not exist)     │
├─────────────────────────────────────────────────────┤
│ 2. Check whether to update                           │
│    ├─ No → Break and confirm                         │
│    └─ Yes → Continue to step 3                       │
├─────────────────────────────────────────────────────┤
│ 3. Interact to update                                │
│    (InteractiveFieldCollector guides user)           │
├─────────────────────────────────────────────────────┤
│ 4. Go back to step 1 (loop continues)                │
└─────────────────────────────────────────────────────┘

Usage:
    python scripts/debug_agent_request.py
"""

from pathlib import Path
import sys
import json
import time
from typing import Dict, Any, Optional, Union
from abc import ABC, abstractmethod

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.path_manager import PathManager
from src.utils.field_collector import FieldCollector, InteractiveFieldCollector
from src.debug_config import DebugConfig
from src.dataclasses.config import AGENT_CONFIGS
from src.decorators import handle_api_request

# Conditional imports for agent schema classes
# Only import schema classes for agents that are implemented
SCHEMA_REGISTRY = {}

try:
    from src.agents.agent_bocha import BochaRequestSchema
    SCHEMA_REGISTRY["BOCHA"] = BochaRequestSchema
except ImportError:
    pass

try:
    from src.agents.agent_xunfei import XunfeiRequestSchema
    SCHEMA_REGISTRY["XUNFEI"] = XunfeiRequestSchema
except ImportError:
    pass

try:
    from src.agents.agent_hunyuan import HunyuanRequestSchema
    SCHEMA_REGISTRY["HUNYUAN"] = HunyuanRequestSchema
except ImportError:
    pass

try:
    from src.agents.agent_qianfan import QianfanRequestSchema
    SCHEMA_REGISTRY["QIANFAN"] = QianfanRequestSchema
except ImportError:
    pass

try:
    from src.agents.agent_meta import MetaRequestSchema
    SCHEMA_REGISTRY["META"] = MetaRequestSchema
except ImportError:
    pass

try:
    from src.agents.agent_twitter import TwitterRequestSchema
    SCHEMA_REGISTRY["TWITTER"] = TwitterRequestSchema
except ImportError:
    pass

def get_schema(agent_name: str):
    """Get RequestSchema class for an agent."""
    if agent_name not in SCHEMA_REGISTRY:
        available = ", ".join(SCHEMA_REGISTRY.keys())
        raise KeyError(
            f"No schema found for agent '{agent_name}'. "
            f"Available agents: {available}"
        )
    return SCHEMA_REGISTRY[agent_name]

def get_all_schemas():
    """Get all registered schemas."""
    return SCHEMA_REGISTRY.copy()


# ==============================================================================
# COLOR UTILITIES
# ==============================================================================

class Color:
    """ANSI color codes for terminal output"""
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Reset
    RESET = "\033[0m"

    @staticmethod
    def bold(text):
        return f"{Color.BOLD}{text}{Color.RESET}"

    @staticmethod
    def cyan(text):
        return f"{Color.CYAN}{text}{Color.RESET}"

    @staticmethod
    def green(text):
        return f"{Color.GREEN}{text}{Color.RESET}"

    @staticmethod
    def yellow(text):
        return f"{Color.YELLOW}{text}{Color.RESET}"

    @staticmethod
    def red(text):
        return f"{Color.RED}{text}{Color.RESET}"

    @staticmethod
    def blue(text):
        return f"{Color.BLUE}{text}{Color.RESET}"

    @staticmethod
    def dim(text):
        return f"{Color.DIM}{text}{Color.RESET}"


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def clear_page():
    """Clear the terminal screen"""
    import os
    os.system('clear' if os.name == 'posix' else 'cls')


def print_section(title: str):
    """Print a section header"""
    print()
    separator = Color.cyan("=" * 100)
    print(separator)
    print(f" {Color.bold(Color.yellow(title))}")
    print(separator)


def print_header(title: str):
    """Print a main header"""
    print("\n")
    print(Color.bold(Color.cyan("╔" + "═" * 98 + "╗")))
    print(Color.bold(Color.cyan("║")) + f" {Color.yellow(Color.bold(title)):<94} " + Color.bold(Color.cyan("║")))
    print(Color.bold(Color.cyan("╚" + "═" * 98 + "╝")))


# ==============================================================================
# UNIFIED DEBUG AGENT CLASS (consolidated with base class)
# ==============================================================================

class DebugAgentScript(ABC):
    """
    Unified debug script that works with any agent.

    Automatically adapts to the selected agent's schema and configuration.
    Uses InteractiveFieldCollector to guide users through building request bodies.

    Provides common functionality for:
    - Parameter configuration with modification loops
    - Request preview and confirmation
    - Cache verification
    - Retry/modify/finish logic
    """

    # Cache verification settings (same for all agents)
    VERIFY_CACHE_UPDATE = True
    CACHE_UPDATE_TIMEOUT_SECONDS = 3
    VERIFY_CACHE_MODIFICATION = True
    CACHE_MOD_TIMEOUT_SECONDS = 3

    def __init__(self, agent_name: str):
        """Initialize unified debug script for the given agent.

        Args:
            agent_name: Name of the agent (e.g., "BOCHA", "META", "XUNFEI")
        """
        self.agent_name = agent_name
        self.config = AGENT_CONFIGS.get(agent_name)
        if not self.config:
            raise ValueError(f"Agent {agent_name} not found in AGENT_CONFIGS")

        # Get schema for this agent
        self.schema_class = get_schema(agent_name)
        self.schema_name = self.schema_class.__name__.replace("RequestSchema", "")

        # Initialize params with default request body and default configs
        default_body = FieldCollector.get_default_body(self.schema_class)
        self.params = self.get_default_configs().copy()
        self.params["request_body"] = default_body

    # ==============================================================================
    # ABSTRACT METHODS - Must be implemented by subclass
    # ==============================================================================

    @abstractmethod
    def get_default_configs(self) -> Dict[str, Any]:
        """Return default configuration parameters for this agent."""
        pass

    @abstractmethod
    def build_query_from_params(self, params: Dict[str, Any]) -> Union[str, Dict]:
        """Convert parameters to agent-specific query format."""
        pass

    @abstractmethod
    def submit_request(self, query: Union[str, Dict], params: Dict[str, Any]) -> Optional[Dict]:
        """Execute the actual API call."""
        pass

    # ==============================================================================
    # COMMON METHODS - Reusable across all agents
    # ==============================================================================

    def build_request_params(self) -> None:
        """
        Build request parameters with loop for review and modification.

        Updates self.params directly with modifications.

        Workflow:
        1. Report current request body from self.params
        2. Check whether to update - break if not
        3. Interact to update (changes take effect on self.params)
        4. Go back to step 1
        """
        print_section("Step 2: Configure Request Parameters")

        # Get the current body from self.params
        body = self.params["request_body"]

        # Create collector for interactive form (reusable across modifications)
        collector = InteractiveFieldCollector(self.schema_class)

        # Loop for request body review and modification
        while True:
            # Step 1: Report current request body
            print_section("Current Request Body")
            table = FieldCollector.generate_table(self.schema_class, body)
            print(table)

            print(Color.cyan("JSON REQUEST BODY:"))
            print(json.dumps(body, indent=2, ensure_ascii=False))
            print()

            # Step 2: Check whether to update - break if not
            modify = input(f"Update request body? {Color.blue('(y/[n])')} ").strip().lower() or 'n'
            if modify != "y":
                # User confirmed - exit loop
                print("✓ Request body confirmed")
                print()
                break

            # Step 3: Interact to update (updates body in-place)
            print()
            print(Color.cyan("Enter new values (changes will take effect):"))
            print()
            # Pass current body so existing values are shown as defaults
            updated_body = collector.build_request_body(body)
            # Update body with any changes
            body.update(updated_body)
            print()
            print(f"✓ Request body updated. Current state:")
            print()

            # Step 4: Go back to step 1 (implicit - while loop continues)

        # self.params is already updated since body is a reference to self.params["request_body"]

    def display_complete_request_report(self):
        """Display complete request report with all details"""
        print_section("Step 3: Complete Request Report")

        print(Color.cyan("REQUEST DETAILS:"))
        print()

        # API endpoint and method
        print(Color.cyan("API Configuration:"))
        api_endpoint = self.config.api_endpoint if self.config else "[NOT_CONFIGURED]"
        agent_type = self.config.agent_type if self.config else "[NOT_CONFIGURED]"
        print(f"  Endpoint: {Color.yellow(api_endpoint)}")
        print(f"  Agent Type: {Color.yellow(agent_type)}")
        print()

        # Request body
        request_body = self.params.get("request_body", {})
        print(Color.cyan("Request Body (from schema):"))
        table = FieldCollector.generate_table(self.schema_class, request_body)
        print(table)

        # Display current fake response flag states
        print(Color.cyan("Current Fake Response Flags (from DebugConfig):"))
        print(f"  enabled:  {Color.yellow(str(DebugConfig.fake_response_enabled))}")
        print(f"  update:   {Color.yellow(str(DebugConfig.fake_response_update))}")
        print(f"  interact: {Color.yellow(str(DebugConfig.fake_response_interact))}")
        print()

    def display_and_configure_flags(self):
        """Display fake response flags and allow user to modify them - with modification loop"""
        while True:
            print_section("Step 4: Fake Response Configuration")

            print(Color.cyan("Current Settings:"))
            print(f"  enabled:  {Color.yellow(str(DebugConfig.fake_response_enabled))}")
            print(f"  update:   {Color.yellow(str(DebugConfig.fake_response_update))}")
            print(f"  interact: {Color.yellow(str(DebugConfig.fake_response_interact))}")
            print()

            change_flags = input(f"Change any settings? {Color.blue('(y/[n])')} ").strip().lower() or 'n'

            if change_flags == 'y':
                print("\nEnter new values (press Enter to keep current):")
                print()

                # Helper to show correct default based on current value
                def get_prompt(name: str, current: bool) -> str:
                    prompt_text = "([t]/f)" if current else "(t/[f])"
                    return f"  {name} {Color.dim(f'[current: {current}]')} {Color.blue(prompt_text)}: "

                enabled_input = input(get_prompt("enabled", DebugConfig.fake_response_enabled)).strip().lower()
                if enabled_input:
                    if enabled_input in ['true', 't', '1', 'yes', 'y']:
                        DebugConfig.fake_response_enabled = True
                    elif enabled_input in ['false', 'f', '0', 'no', 'n']:
                        DebugConfig.fake_response_enabled = False
                    else:
                        print(f"⚠ Invalid input, keeping current: {DebugConfig.fake_response_enabled}")

                update_input = input(get_prompt("update", DebugConfig.fake_response_update)).strip().lower()
                if update_input:
                    if update_input in ['true', 't', '1', 'yes', 'y']:
                        DebugConfig.fake_response_update = True
                    elif update_input in ['false', 'f', '0', 'no', 'n']:
                        DebugConfig.fake_response_update = False
                    else:
                        print(f"⚠ Invalid input, keeping current: {DebugConfig.fake_response_update}")

                interact_input = input(get_prompt("interact", DebugConfig.fake_response_interact)).strip().lower()
                if interact_input:
                    if interact_input in ['true', 't', '1', 'yes', 'y']:
                        DebugConfig.fake_response_interact = True
                    elif interact_input in ['false', 'f', '0', 'no', 'n']:
                        DebugConfig.fake_response_interact = False
                    else:
                        print(f"⚠ Invalid input, keeping current: {DebugConfig.fake_response_interact}")

                print()
                print("✓ Settings updated")
                print()
                # Loop continues to show updated values
            else:
                # User confirmed - exit loop
                print()
                print("✓ Settings confirmed")
                print()
                break

    def confirm_submission(self) -> bool:
        """Display final config using schema-based information and ask for confirmation"""
        print_section("Step 5: Final Submission Confirmation")

        # Get the request body from self.params (built by InteractiveFieldCollector)
        request_body = self.params.get("request_body", {})

        # Display API REQUEST PARAMETERS first (before the body)
        print(Color.cyan("API REQUEST PARAMETERS:"))
        print(f"  agent:  {Color.yellow(self.agent_name)}")
        api_endpoint = self.config.api_endpoint if self.config else "[NOT_CONFIGURED]"
        print(f"  url:    {Color.yellow(api_endpoint)}")
        print(f"  method: {Color.yellow('POST')}")
        print()

        # Display headers
        api_key = self.config.api_key
        if not api_key:
            try:
                settings = SchedulerSettings.initialize()
                ready_agents = settings.get_ready_agents()
                agent_config = ready_agents.get(self.agent_name)
                if agent_config:
                    api_key = agent_config.api_key
            except Exception:
                api_key = None

        headers = {
            "Authorization": f"Bearer {api_key}" if api_key else "Bearer [API_KEY_NOT_FOUND]",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        print(Color.cyan("headers:"))
        print(json.dumps(headers, indent=2, ensure_ascii=False))
        print()

        # Display request body as raw JSON
        print(Color.cyan("request_body:"))
        print(json.dumps(request_body, indent=2, ensure_ascii=False))
        print()

        # Display request body table
        print(Color.cyan("REQUEST BODY (table):"))
        table = FieldCollector.generate_table(self.schema_class, request_body)
        print(table)
        print()

        # Display fake response configuration
        print(Color.cyan("Fake Response Configuration:"))
        print(f"  enabled:  {Color.yellow(str(DebugConfig.fake_response_enabled))}")
        print(f"  update:   {Color.yellow(str(DebugConfig.fake_response_update))}")
        print(f"  interact: {Color.yellow(str(DebugConfig.fake_response_interact))}")
        print()

        # Ask for confirmation with default highlighted
        while True:
            response = input(f"Submit request? {Color.blue('([y]/n)')} ").strip().lower() or 'y'
            if response in ["y", "n"]:
                return response == "y"
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
        """Verify that cache file was updated within timeout."""
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
        """Verify that cache file was modified on re-submit."""
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
        """Find the cache file for this agent (excluding .metadata.json files)"""
        cache_dir = PathManager.get_agent_cache_dir(self.agent_name)
        if not cache_dir.exists():
            return None

        # Get the most recently modified cache file (exclude .metadata.json files)
        cache_files = [f for f in cache_dir.glob("*.json") if not f.name.endswith(".metadata.json")]
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

            # Display response body content
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                print("Response Body (brief):")

                # Extract response body from cache structure (stored at top level with metadata)
                response_body = cache_data.get('response_body')

                if response_body is None:
                    print(f"  No response body found")
                # Handle list responses
                elif isinstance(response_body, list):
                    print(f"  Type: list")
                    print(f"  Length: {len(response_body)}")
                # Handle dict responses
                elif isinstance(response_body, dict):
                    keys = list(response_body.keys())
                    print(f"  Type: dict")
                    print(f"  Keys: {keys}")
                else:
                    print(f"  Type: {type(response_body).__name__}")
                print()
            except Exception as e:
                print(f"⚠ Could not read response content: {e}")
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
        params_initialized = False
        while True:
            # Step 2: Configure parameters (skip if retrying with same params)
            if not params_initialized:
                clear_page()
                self.build_request_params()
                params_initialized = True

            # Step 3: Display complete request report
            clear_page()
            self.display_complete_request_report()

            # Step 4: Display and configure fake response flags
            clear_page()
            self.display_and_configure_flags()

            # Step 5: Confirm and submit
            clear_page()
            if not self.confirm_submission():
                print("\n⚠ Request cancelled")
                return

            # Step 6: Submit request
            clear_page()
            query = self.build_query_from_params(self.params)
            raw_response = self.submit_request(query, self.params)

            if raw_response is None:
                continue

            # Step 7: Find and display response
            clear_page()
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
                        params_initialized = False
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
                # Retry with same params (don't reset, loop back directly)
                continue
            elif choice == 'm':
                # Modify - reset params_initialized to trigger parameter configuration on next loop
                params_initialized = False
                continue
            else:
                # Finish
                break

        print("\n✓ Debug script completed")


# ==============================================================================
# UNIFIED DEBUG SCRIPT IMPLEMENTATION
# ==============================================================================

class UnifiedDebugScript(DebugAgentScript):
    """Concrete implementation of unified debug script for all agents."""

    def get_default_configs(self) -> Dict[str, Any]:
        """Return default configuration parameters."""
        return {
            "language": "zh",
            "include_raw_response": True,
        }

    def build_query_from_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert parameters to API request format."""
        # Get the request body from InteractiveFieldCollector
        request_body = params.get("request_body", {})
        return request_body

    def submit_request(self, query: Dict[str, Any], params: Dict[str, Any]) -> Optional[Dict]:
        """Execute the API call using centralized handle_api_request()."""
        try:
            # Get API key from environment
            settings = SchedulerSettings.initialize()
            ready_agents = settings.get_ready_agents()
            agent_config = ready_agents.get(self.agent_name)

            if not agent_config or not agent_config.api_key:
                print(f"❌ {self.agent_name} API key not configured")
                return None

            print(f"\n📡 Submitting request to {self.agent_name} API...")
            print()

            # Build request headers
            headers = {
                "Authorization": f"Bearer {agent_config.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            # Ensure DEBUG is enabled for fake response handling
            DebugConfig.DEBUG = True

            # Use centralized request handler
            raw_response = handle_api_request(
                agent_name=self.agent_name,
                url=self.config.api_endpoint,
                method="POST",
                description=f"{self.agent_name.lower()}_search",
                json_body=query,
                headers=headers,
                timeout=120,
                query_request=None,
            )

            if raw_response:
                print("✓ API call successful")
                if isinstance(raw_response, dict):
                    print(f"  Response keys: {list(raw_response.keys())}")
                return raw_response
            else:
                print("❌ API call returned empty response")
                return None

        except Exception as e:
            print(f"❌ Error during API call: {e}")
            import traceback
            traceback.print_exc()
            return None


# ==============================================================================
# AGENT SELECTION AND MAIN ENTRY POINT
# ==============================================================================

def select_agent() -> str:
    """Let user select an agent from available schemas."""
    all_schemas = get_all_schemas()
    agent_names = sorted(all_schemas.keys())

    print("\nAvailable agents:")
    for i, name in enumerate(agent_names, 1):
        print(f"  {i}. {name}")
    print()

    while True:
        choice = input("Select agent (number): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(agent_names):
                selected = agent_names[idx]
                print(f"✓ Selected: {selected}\n")
                return selected
            else:
                print("⚠ Invalid selection")
        except ValueError:
            print("⚠ Please enter a number")


def main():
    """Main entry point"""
    try:
        # Print header
        print_header("UNIFIED AGENT DEBUG SCRIPT")

        # Let user select agent
        agent_name = select_agent()

        # Create and run debug script
        script = UnifiedDebugScript(agent_name)
        script.run()

    except KeyboardInterrupt:
        print("\n\n⚠ Script interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
