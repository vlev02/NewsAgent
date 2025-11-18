#!/usr/bin/env python3
"""
Interactive debug script for testing META agent with cache verification.

This script allows you to:
1. Configure META-specific request parameters
2. Select resource scopes (webpage, blog, scholar)
3. Choose time filters (day, week, month, unlimited)
4. Preview request before submitting
5. Submit the request with fake response capture enabled
6. Verify cache file updates and modifications

META API Configuration:
=======================
- API: https://metaso.cn/api/v1/search
- Type: REST API
- Authentication: Bearer token in Authorization header
- Response Format: META-specific JSON structure with webpages array

Resource Types:
- webpage: General web pages (most common)
- blog: Technical blogs and personal shares
- scholar: Academic papers and research

Time Filters:
- day: Last 1 day
- week: Last 7 days
- month: Last 30 days
- None: No time limit

Usage:
    python scripts/debug_agent_request_meta.py

Example workflow:
    1. Start script
    2. Configure search parameters
    3. Select resource scopes (webpage/blog/scholar)
    4. Choose time filter (day/week/month/unlimited)
    5. Review the complete request report
    6. Configure fake response flags
    7. Confirm and submit the request
    8. View cache file location and verification results
    9. Retry with same params, modify params, or finish
"""

from pathlib import Path
import sys
import requests
from typing import Dict, Any, Optional, Union

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from debug_agent_request_abstract import DebugAgentScript, print_section
from src.dataclasses import QueryRequest
from src.debug_config import DebugConfig
from src.scheduler.scheduler_settings import SchedulerSettings


class MetaDebugScript(DebugAgentScript):
    """
    META-specific debug script implementation.

    Inherits common functionality from DebugAgentScript and implements
    META-specific methods for query building and request submission.

    Extends base functionality with:
    - Multiple resource type selection (webpage, blog, scholar)
    - Time filter configuration (day, week, month)
    - META-specific response handling
    """

    # META-specific cache verification settings
    VERIFY_CACHE_UPDATE = True
    CACHE_UPDATE_TIMEOUT_SECONDS = 3
    VERIFY_CACHE_MODIFICATION = True
    CACHE_MOD_TIMEOUT_SECONDS = 3

    # META-specific configuration
    AVAILABLE_SCOPES = ['webpage', 'blog', 'scholar']
    AVAILABLE_TIME_FILTERS = ['day', 'week', 'month', 'unlimited']

    def __init__(self):
        """Initialize META debug script"""
        super().__init__("META")
        self.api_key = SchedulerSettings.initialize().get_ready_agents().get("META", {}).get("api_key")

    def get_default_configs(self) -> Dict[str, Any]:
        """
        Return default configuration parameters for META.

        Returns:
            Dict with META-specific defaults including scopes and time_filter
        """
        return {
            "query_fields": ["人工智能"],
            "query_topics": ["大模型"],
            "days_back": 7,
            "max_results": 5,
            "language": "zh",
            "scopes": ['webpage', 'blog'],  # Default to webpage and blog
            "time_filter": "week",  # Default to last week
            "include_ai_summary": False,  # META doesn't support summary
            "include_raw_response": True,
        }

    def configure_scopes(self) -> list:
        """
        Interactive configuration for resource scopes.

        Returns:
            List of selected scopes
        """
        print_section("Step 2A: Select Resource Scopes")

        print("Available resource types:")
        print("  1. webpage  - General web pages (most common)")
        print("  2. blog     - Technical blogs and personal shares")
        print("  3. scholar  - Academic papers and research")
        print()

        selected = []
        while True:
            choice = input("Select scopes (e.g., '1,2' or '1' or 'a' for all): ").strip().lower()

            if choice == 'a':
                selected = self.AVAILABLE_SCOPES
                print(f"✓ Selected all scopes: {selected}")
                break
            elif choice:
                try:
                    indices = [int(x.strip()) - 1 for x in choice.split(',')]
                    selected = [self.AVAILABLE_SCOPES[i] for i in indices if 0 <= i < len(self.AVAILABLE_SCOPES)]
                    if selected:
                        print(f"✓ Selected scopes: {selected}")
                        break
                    else:
                        print("⚠ Invalid selection")
                except ValueError:
                    print("⚠ Please enter numbers separated by commas")

        return selected

    def configure_time_filter(self) -> str:
        """
        Interactive configuration for time filters.

        Returns:
            Selected time filter or None for unlimited
        """
        print_section("Step 2B: Select Time Filter")

        print("Available time filters:")
        print("  1. day       - Last 1 day")
        print("  2. week      - Last 7 days")
        print("  3. month     - Last 30 days")
        print("  4. unlimited - No time limit")
        print()

        while True:
            choice = input("Select time filter (1-4): ").strip()

            if choice == '1':
                print("✓ Selected: day (last 1 day)")
                return 'day'
            elif choice == '2':
                print("✓ Selected: week (last 7 days)")
                return 'week'
            elif choice == '3':
                print("✓ Selected: month (last 30 days)")
                return 'month'
            elif choice == '4':
                print("✓ Selected: unlimited (no time limit)")
                return None
            else:
                print("⚠ Please enter 1, 2, 3, or 4")

    def build_request_params(self) -> Dict[str, Any]:
        """
        Build request parameters with META-specific configuration.

        Overrides parent method to include scope and time_filter configuration.
        """
        params = self.get_default_configs().copy()

        while True:
            print_section("Step 2: Configure Request Parameters")

            print("Current parameters:")
            print(f"  query_fields: {params['query_fields']}")
            print(f"  query_topics: {params['query_topics']}")
            print(f"  days_back: {params['days_back']}")
            print(f"  max_results: {params['max_results']}")
            print(f"  language: {params['language']}")
            print(f"  scopes: {params['scopes']}")
            print(f"  time_filter: {params['time_filter'] or 'unlimited'}")
            print()

            customize = input("Modify parameters? (y/n): ").strip().lower()

            if customize == 'y':
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
                print("✓ Basic parameters updated")
                print()

                # Configure scopes
                scopes = self.configure_scopes()
                params['scopes'] = scopes
                print()

                # Configure time filter
                time_filter = self.configure_time_filter()
                params['time_filter'] = time_filter
                print()

                print("✓ All parameters updated")
                print()
                # Loop back to show updated values
            else:
                # User confirmed - exit loop
                print(f"✓ Parameters confirmed")
                print()
                break

        return params

    def build_query_from_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert parameters to META API request format.

        Args:
            params: Configuration dictionary

        Returns:
            META API request dictionary
        """
        # Combine query fields and topics
        all_terms = params.get('query_fields', []) + params.get('query_topics', [])
        query_string = " ".join(all_terms)

        # Build META API request
        request_dict = {
            "q": query_string,
            "scope": params.get('scopes', ['webpage'])[0],  # Use first scope for now
            "size": str(params.get('max_results', 5)),
            "includeSummary": params.get('include_ai_summary', False),
            "includeRawContent": params.get('include_raw_response', True),
            "conciseSnippet": False
        }

        return request_dict

    def submit_request(self, query: Dict[str, Any], params: Dict[str, Any]) -> Optional[Dict]:
        """
        Execute the META API call.

        Args:
            query: Query dictionary built by build_query_from_params()
            params: Original parameters (for context)

        Returns:
            Raw API response or None if failed
        """
        try:
            # Get API key from environment
            settings = SchedulerSettings.initialize()
            ready_agents = settings.get_ready_agents()
            meta_config = ready_agents.get("META")

            if not meta_config or not meta_config.api_key:
                print("❌ META API key not configured")
                return None

            print("\n📡 Submitting request to META API...")
            print(f"   Query: {query.get('q', 'N/A')}")
            print(f"   Scope: {query.get('scope', 'N/A')}")
            print(f"   Max results: {query.get('size', 'N/A')}")
            print()

            # Build request headers
            headers = {
                'Authorization': f'Bearer {meta_config.api_key}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

            # Make API request
            response = requests.post(
                self.config.api_endpoint,
                json=query,
                headers=headers,
                timeout=30
            )

            # Check response status
            if response.status_code != 200:
                print(f"❌ API returned error status: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

            raw_response = response.json()

            if raw_response:
                print("✓ API call successful")
                if isinstance(raw_response, dict):
                    if 'webpages' in raw_response:
                        webpages = raw_response['webpages'].get('value', [])
                        print(f"  Results returned: {len(webpages)}")
                    print(f"  Response keys: {list(raw_response.keys())}")
                return raw_response
            else:
                print("❌ API call returned empty response")
                return None

        except requests.exceptions.Timeout:
            print("❌ API call timeout")
            return None
        except Exception as e:
            print(f"❌ Error during API call: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """Main entry point"""
    try:
        script = MetaDebugScript()
        script.run()
    except KeyboardInterrupt:
        print("\n\n⚠ Script interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
