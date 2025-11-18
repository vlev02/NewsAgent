#!/usr/bin/env python3
"""
Interactive debug script for testing individual agents with cache verification.

This script allows you to:
1. Set global default configurations at the top
2. Select an agent to debug from config/agents.yaml
3. Configure request parameters with template support
4. Preview request before submitting
5. Submit the request with fake response capture enabled
6. View response and cache file location

CACHE VERIFICATION LOGIC:
========================

The script includes two verification steps to ensure fake response caching is working:

**Step 5A: Cache File Update Check**
  - Verifies that the cache file was updated within CACHE_UPDATE_TIMEOUT_SECONDS
  - Checks file modification time to ensure fresh API call was captured
  - If FAILED: Cache file is old, decorator may not be intercepting correctly
  - If PASSED: Cache file exists and was recently updated

**Step 6: Cache Modification on Re-submit Check**
  - Re-submits the same request
  - Monitors if cache file size changes within CACHE_MOD_TIMEOUT_SECONDS
  - If FAILED: Re-submitted request reused old cache instead of updating
  - If PASSED: Cache file was modified with new response data

CONFIGURATION FLAGS (modify at top of file):
=============================================

VERIFY_CACHE_UPDATE: bool (default: True)
  - Enable/disable Step 5A cache update verification

CACHE_UPDATE_TIMEOUT_SECONDS: int (default: 3)
  - How many seconds old the cache file can be to pass verification

VERIFY_CACHE_MODIFICATION: bool (default: True)
  - Enable/disable Step 6 cache modification verification

CACHE_MOD_TIMEOUT_SECONDS: int (default: 3)
  - How many seconds to wait for cache file size change

FAKE RESPONSE DEBUG FLAGS (set in DebugConfig):
===============================================

DebugConfig.fake_response_enabled: bool
  - Whether to use cached responses at all

DebugConfig.fake_response_update: bool
  - Whether to UPDATE cache when fake_response_enabled is True
  - True = Make real API call and update cache
  - False = Use existing cache, don't update

DebugConfig.fake_response_interact: bool
  - Whether to prompt user to save/discard responses

Usage:
    python scripts/debug_agent_request.py
"""

from pathlib import Path
import sys
import json
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.scheduler.scheduler_settings import SchedulerSettings, PathManager
from src.debug_config import DebugConfig
from src.dataclasses import QueryRequest
from src.dataclasses.config import AGENT_CONFIGS
from src.agents.bocha import BochaAgent

# ==============================================================================
# GLOBAL DEFAULT CONFIGS - Modify these to change default behavior
# ==============================================================================

DEFAULT_CONFIGS = {
    "query_fields": ["人工智能"],
    "query_topics": ["大模型"],
    "days_back": 7,
    "max_results": 5,
    "language": "zh",
    "include_ai_summary": True,
    "include_raw_response": True,
}

# ==============================================================================
# FAKE RESPONSE CACHE VERIFICATION FLAGS
# ==============================================================================
# Set these to control cache verification behavior

VERIFY_CACHE_UPDATE = True          # Enable cache update verification
CACHE_UPDATE_TIMEOUT_SECONDS = 3    # Timeout for cache file update check
VERIFY_CACHE_MODIFICATION = True    # Verify cache modification on re-submit
CACHE_MOD_TIMEOUT_SECONDS = 3       # Timeout for cache modification check

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def print_header(title: str):
    """Print formatted header"""
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)
    print()


def print_section(title: str):
    """Print formatted section"""
    print()
    print("-" * 100)
    print(title)
    print("-" * 100)


def get_available_agents() -> Dict[int, str]:
    """Get list of available agents from AGENT_CONFIGS"""
    agents = {}
    for idx, agent_name in enumerate(AGENT_CONFIGS.keys(), 1):
        agents[idx] = agent_name
    return agents


def display_agent_options(agents: Dict[int, str]):
    """Display agent options for selection"""
    print("\nAvailable agents:")
    for idx, agent_name in agents.items():
        config = AGENT_CONFIGS[agent_name]
        print(f"  {idx}. {agent_name:12} - {config.agent_type:15} ({config.api_endpoint[:60]}...)")
    print()


def select_agent() -> str:
    """Interactive agent selection"""
    print_section("Step 1: Select Agent")

    agents = get_available_agents()
    display_agent_options(agents)

    while True:
        try:
            choice = input("Enter agent number: ").strip()
            choice_int = int(choice)
            if choice_int in agents:
                agent_name = agents[choice_int]
                print(f"✓ Selected: {agent_name}")
                return agent_name
            else:
                print(f"❌ Invalid choice. Please select 1-{len(agents)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number")


def build_request_params() -> Dict[str, Any]:
    """Build request parameters with defaults and user customization - with modification loop"""
    params = DEFAULT_CONFIGS.copy()

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


def display_complete_request_report(agent_name: str, params: Dict[str, Any]):
    """Display complete request report with all details and current flag states"""
    print_section("Step 3: Complete Request Report")

    agent_config = AGENT_CONFIGS[agent_name]

    print(f"Agent Name: {agent_name}")
    print(f"Agent Type: {agent_config.agent_type}")
    print(f"API Endpoint: {agent_config.api_endpoint}")
    print(f"HTTP Method: POST")
    print()

    print("Request Parameters:")
    print(f"  query_fields: {params['query_fields']}")
    print(f"  query_topics: {params['query_topics']}")
    print(f"  days_back: {params['days_back']}")
    print(f"  max_results: {params['max_results']}")
    print(f"  language: {params['language']}")
    print(f"  include_ai_summary: {params['include_ai_summary']}")
    print(f"  include_raw_response: {params['include_raw_response']}")
    print()

    # Display template file if exists
    template_dir = PathManager.get_templates_dir()
    agent_template = template_dir / f"{agent_name.lower()}_prompt.jinja2"
    if agent_template.exists():
        print(f"✓ Using template: {agent_template}")
    else:
        print(f"⚠ Template not found: {agent_template}")
    print()

    # Display current fake response flag states
    print("Current Fake Response Flags (from DebugConfig):")
    print(f"  fake_response_enabled: {DebugConfig.fake_response_enabled}")
    print(f"  fake_response_update: {DebugConfig.fake_response_update}")
    print(f"  fake_response_interact: {DebugConfig.fake_response_interact}")
    print()


def display_and_configure_flags():
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


def confirm_submission(agent_name: str, params: Dict[str, Any]) -> bool:
    """Display final config summary and ask user to confirm request submission"""
    print_section("Step 5: Final Submission Confirmation")

    print("FINAL REQUEST CONFIGURATION:")
    print()

    # Agent info
    print("Agent Information:")
    config = AGENT_CONFIGS[agent_name]
    print(f"  Agent Name: {agent_name}")
    print(f"  Agent Type: {config.agent_type}")
    print(f"  API Endpoint: {config.api_endpoint}")
    print()

    # Request parameters
    print("Request Parameters:")
    print(f"  Query Fields: {params.get('query_fields', [])}")
    print(f"  Query Topics: {params.get('query_topics', [])}")
    print(f"  Days Back: {params.get('days_back', 7)}")
    print(f"  Max Results: {params.get('max_results', 5)}")
    print(f"  Language: {params.get('language', 'zh')}")
    print(f"  Include AI Summary: {params.get('include_ai_summary', True)}")
    print(f"  Include Raw Response: {params.get('include_raw_response', True)}")
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


def ask_retry_or_finish() -> str:
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


def submit_request(agent_name: str, params: Dict[str, Any]) -> tuple:
    """Submit request to agent with fake response capture enabled"""
    print_section("Step 4: Submit Request")

    try:
        # Initialize settings
        settings = SchedulerSettings.initialize()
        ready_agents = settings.get_ready_agents()

        if agent_name not in ready_agents:
            print(f"❌ Agent {agent_name} not available (API key not configured)")
            return None, None

        # Ensure DEBUG is enabled (but don't override user-configured flags)
        DebugConfig.DEBUG = True
        # Note: fake_response_enabled, fake_response_update, and fake_response_interact
        # are already configured in Step 4, so we don't override them here

        # Get agent config and create agent instance
        agent_config = ready_agents[agent_name]

        # Create agent dynamically based on agent type
        if agent_name == "BOCHA":
            agent = BochaAgent(agent_config)
        else:
            print(f"⚠ Agent {agent_name} implementation not yet available")
            print(f"  (Only BOCHA agent is implemented)")
            return None, None

        # Create QueryRequest
        query = QueryRequest(
            query_fields=params['query_fields'],
            query_topics=params['query_topics'],
            source_agents=[agent_name],
            days_back=params['days_back'],
            max_results=params['max_results'],
            include_ai_summary=params['include_ai_summary'],
            include_raw_response=params['include_raw_response'],
            language=params['language']
        )

        print(f"Query ID: {query.query_id}")
        print(f"Sending request to {agent_name}...")
        print()

        # Call API
        query_string = " ".join(query.query_fields + query.query_topics)
        raw_response = agent.call_api(query_string, query)

        print(f"✓ Request submitted successfully")
        print(f"  Response type: {type(raw_response).__name__}")
        print()

        return raw_response, agent_name

    except Exception as e:
        print(f"❌ Error submitting request: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def find_cache_file(agent_name: str) -> Path:
    """Find the most recent cache file for agent"""
    cache_dir = PathManager.get_agent_cache_dir(agent_name)

    if not cache_dir.exists():
        return None

    json_files = list(cache_dir.glob("*.json"))
    json_files = [f for f in json_files if ".metadata" not in f.name]

    if not json_files:
        return None

    # Return most recent
    return sorted(json_files, key=lambda f: f.stat().st_mtime)[-1]


def display_response_summary(agent_name: str, cache_file: Path):
    """Display response summary from cached file"""
    print_section("Step 5: Response Summary")

    if not cache_file:
        print(f"❌ No cache file found for {agent_name}")
        return

    print(f"Cache file: {cache_file}")
    print(f"File size: {cache_file.stat().st_size:,} bytes")
    print()

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)

        # Display request body
        print("Request body:")
        req_body = cached_data.get('request_body', {})
        print(f"  query_fields: {req_body.get('query_fields')}")
        print(f"  query_topics: {req_body.get('query_topics')}")
        print(f"  days_back: {req_body.get('days_back')}")
        print(f"  max_results: {req_body.get('max_results')}")
        print(f"  language: {req_body.get('language')}")
        print()

        # Display response metadata
        print("Response metadata:")
        resp_body = cached_data.get('response_body', {})
        print(f"  Code: {resp_body.get('code')}")
        print(f"  Message: {resp_body.get('msg', 'N/A')}")
        print()

        # Display response details based on agent type
        if 'data' in resp_body and resp_body['data']:
            data = resp_body['data']

            if 'webPages' in data:
                web_pages = data['webPages']
                print("Web pages:")
                print(f"  Total matches: {web_pages.get('totalEstimatedMatches', 'N/A')}")
                print(f"  Results returned: {len(web_pages.get('value', []))}")

                results = web_pages.get('value', [])
                if results:
                    print()
                    print("First result sample:")
                    first = results[0]
                    print(f"  Title: {first.get('name', 'N/A')[:100]}")
                    print(f"  URL: {first.get('url', 'N/A')[:100]}")
                    print(f"  Source: {first.get('siteName', 'N/A')}")
                    print(f"  Published: {first.get('datePublished', 'N/A')}")
        print()

    except Exception as e:
        print(f"❌ Error reading cache file: {e}")


def verify_cache_file_updated(cache_file: Path, timeout_seconds: int = 3) -> bool:
    """
    Verify that cache file was updated within the timeout period.

    Args:
        cache_file: Path to the cache file
        timeout_seconds: How many seconds old the file can be

    Returns:
        bool: True if file was updated within timeout, False otherwise
    """
    import time

    if not cache_file or not cache_file.exists():
        return False

    # Get file modification time
    mod_time = cache_file.stat().st_mtime
    current_time = time.time()
    age_seconds = current_time - mod_time

    print(f"Cache file modification time check:")
    print(f"  File age: {age_seconds:.2f} seconds")
    print(f"  Timeout: {timeout_seconds} seconds")
    print(f"  Status: {'✓ UPDATED' if age_seconds <= timeout_seconds else '❌ NOT UPDATED'}")

    return age_seconds <= timeout_seconds


def verify_cache_modification(cache_file: Path, original_mtime: float, timeout_seconds: int = 3) -> bool:
    """
    Verify that cache file was modified (timestamp changed) within timeout period.

    Args:
        cache_file: Path to the cache file
        original_mtime: Original file modification time before re-submission
        timeout_seconds: How many seconds to wait for modification

    Returns:
        bool: True if file was modified, False otherwise
    """
    import time

    if not cache_file or not cache_file.exists():
        return False

    print(f"\nWaiting for cache file modification...")
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        current_mtime = cache_file.stat().st_mtime
        if current_mtime > original_mtime:
            elapsed = time.time() - start_time
            print(f"✓ Cache file modified within {elapsed:.2f} seconds")
            print(f"  Original mtime: {original_mtime}")
            print(f"  New mtime: {current_mtime}")
            print(f"  File size: {cache_file.stat().st_size:,} bytes (may be same size)")
            return True
        time.sleep(0.1)

    elapsed = time.time() - start_time
    print(f"❌ Cache file NOT modified after {elapsed:.2f} seconds")
    current_mtime = cache_file.stat().st_mtime
    print(f"  Original mtime: {original_mtime}")
    print(f"  Current mtime: {current_mtime}")
    return False


def resubmit_request_for_verification(agent_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Re-submit request to verify fake response capture is working.

    Args:
        agent_name: Name of the agent
        params: Query parameters

    Returns:
        dict: Response or None if failed
    """
    print_section("Step 6: Verify Cache Modification - Re-submit Request")

    try:
        # Get current cache file if it exists
        cache_dir = PathManager.get_agent_cache_dir(agent_name)
        if cache_dir.exists():
            json_files = list(cache_dir.glob("*.json"))
            json_files = [f for f in json_files if ".metadata" not in f.name]
            if json_files:
                cache_file = sorted(json_files, key=lambda f: f.stat().st_mtime)[-1]
                original_mtime = cache_file.stat().st_mtime
            else:
                original_mtime = 0
        else:
            original_mtime = 0

        # Initialize settings
        settings = SchedulerSettings.initialize()
        ready_agents = settings.get_ready_agents()

        if agent_name not in ready_agents:
            print(f"❌ Agent {agent_name} not available")
            return None

        # Ensure DEBUG is enabled (but don't override user-configured flags)
        DebugConfig.DEBUG = True
        # Note: fake_response_enabled, fake_response_update, and fake_response_interact
        # are already configured in Step 4, so we don't override them here

        # Get agent config and create agent
        agent_config = ready_agents[agent_name]

        if agent_name == "BOCHA":
            agent = BochaAgent(agent_config)
        else:
            print(f"⚠ Agent {agent_name} implementation not yet available")
            return None

        # Create QueryRequest with slightly different parameters to force new cache entry
        query = QueryRequest(
            query_fields=params['query_fields'],
            query_topics=params['query_topics'],
            source_agents=[agent_name],
            days_back=params['days_back'],
            max_results=params['max_results'],
            include_ai_summary=params['include_ai_summary'],
            include_raw_response=params['include_raw_response'],
            language=params['language']
        )

        print(f"Re-submitting request to verify cache capture...")
        print(f"Query ID: {query.query_id}")
        print()

        # Call API again
        query_string = " ".join(query.query_fields + query.query_topics)
        raw_response = agent.call_api(query_string, query)

        # Check cache modification
        cache_dir = PathManager.get_agent_cache_dir(agent_name)
        json_files = list(cache_dir.glob("*.json"))
        json_files = [f for f in json_files if ".metadata" not in f.name]

        if json_files:
            cache_file = sorted(json_files, key=lambda f: f.stat().st_mtime)[-1]
            modified = verify_cache_modification(cache_file, original_mtime, CACHE_MOD_TIMEOUT_SECONDS)
            if modified:
                print(f"✓ Cache modification verified")
                return raw_response
            else:
                print(f"❌ Cache file was NOT modified")
                return raw_response
        else:
            print(f"❌ No cache files found")
            return None

    except Exception as e:
        print(f"❌ Error during re-submission: {e}")
        import traceback
        traceback.print_exc()
        return None


def display_final_summary(agent_name: str, cache_file: Path):
    """Display final summary and next steps"""
    print_header("SUMMARY")

    if cache_file:
        print(f"✓ Request submitted successfully to {agent_name}")
        print(f"✓ Cache file created/updated")
        print()
        print(f"Cache file location:")
        print(f"  {cache_file}")
        print()
        print("To inspect the full cached response:")
        print()
        print(f"  # View in editor:")
        print(f"  code {cache_file}")
        print()
        print(f"  # View in terminal:")
        print(f"  cat {cache_file} | jq '.'")
        print()
        print(f"  # View with pretty-print:")
        print(f"  python -m json.tool {cache_file}")
        print()
    else:
        print("❌ Request failed or cache file not found")

    print("=" * 100)
    print()


def main():
    """Main debug flow with loop for retry/modify"""
    print_header("AGENT DEBUG SCRIPT - Interactive Request Testing")

    # Step 1: Select agent (do this once)
    agent_name = select_agent()

    # Main loop for retry/modify
    params = None
    while True:
        # Step 2: Configure parameters (skip if retrying with same params)
        if params is None:
            params = build_request_params()

        # Step 3: Display complete request report
        display_complete_request_report(agent_name, params)

        # Step 4: Display and configure fake response flags
        display_and_configure_flags()

        # Step 5: Confirm and submit
        if not confirm_submission(agent_name, params):
            print("\n⚠ Request cancelled")
            return

        # Step 6: Submit request
        raw_response, _ = submit_request(agent_name, params)

        if raw_response is None:
            continue

        # Step 7: Find and display response
        cache_file = find_cache_file(agent_name)
        display_response_summary(agent_name, cache_file)

        # Step 8A: Verify cache file was updated (CHECK WITHIN 3 SECONDS)
        if VERIFY_CACHE_UPDATE and cache_file:
            print_section("Step 8A: Verify Cache File Update")
            cache_updated = verify_cache_file_updated(cache_file, CACHE_UPDATE_TIMEOUT_SECONDS)
            if not cache_updated:
                print()
                print("❌ ERROR: Cache file was NOT updated within the timeout!")
                print(f"  This indicates the @fake_response_handler decorator is not working properly.")
                print(f"  Possible causes:")
                print(f"    1. fake_response_enabled flag is not set to True")
                print(f"    2. fake_response_update flag is not set to True")
                print(f"    3. The decorator is not intercepting the API call")
                print(f"    4. Permissions issue writing to cache directory")
                print()
                print("=" * 100)
                # Ask retry or finish
                choice = ask_retry_or_finish()
                if choice == 'r':
                    continue
                elif choice == 'm':
                    params = None
                    continue
                else:
                    return

        # Step 8B: Verify cache modification on re-submit (RE-SUBMIT AND CHECK)
        if VERIFY_CACHE_MODIFICATION and cache_file:
            resubmit_response = resubmit_request_for_verification(agent_name, params)

            if resubmit_response is None:
                print()
                print("❌ ERROR: Re-submission failed!")
                print("=" * 100)
                # Ask retry or finish
                choice = ask_retry_or_finish()
                if choice == 'r':
                    continue
                elif choice == 'm':
                    params = None
                    continue
                else:
                    return

            print()

        # Final summary
        display_final_summary(agent_name, cache_file)

        # Final status
        print_section("CACHE VERIFICATION RESULT")
        if VERIFY_CACHE_UPDATE and VERIFY_CACHE_MODIFICATION:
            print("✓ All cache verification checks PASSED")
            print("✓ Fake response caching is working correctly")
        elif VERIFY_CACHE_UPDATE:
            print("✓ Cache update verification PASSED")
        elif VERIFY_CACHE_MODIFICATION:
            print("✓ Cache modification verification PASSED")
        print()
        print("=" * 100)

        # Ask user what to do next
        choice = ask_retry_or_finish()
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


if __name__ == "__main__":
    main()
