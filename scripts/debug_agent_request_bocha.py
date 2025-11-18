#!/usr/bin/env python3
"""
Interactive debug script for testing BOCHA agent with cache verification.

This script allows you to:
1. Configure BOCHA-specific request parameters
2. Preview request before submitting
3. Submit the request with fake response capture enabled
4. Verify cache file updates and modifications

BOCHA API Configuration:
========================
- API: https://api.bochaai.com/v1/web-search
- Type: REST API
- Authentication: Bearer token in Authorization header
- Response Format: Bocha-specific JSON structure

Usage:
    python scripts/debug_agent_request_bocha.py

Example workflow:
    1. Start script
    2. Configure search parameters (query fields, topics, days_back, max_results)
    3. Review the complete request report
    4. Configure fake response flags (enable/update/interact)
    5. Confirm and submit the request
    6. View cache file location and verification results
    7. Retry with same params, modify params, or finish
"""

from pathlib import Path
import sys
from typing import Dict, Any, Optional, Union

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add scripts directory to path for sibling imports
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from debug_agent_request_abstract import DebugAgentScript
from src.agents.bocha import BochaAgent
from src.dataclasses import QueryRequest
from src.debug_config import DebugConfig


class BochaDebugScript(DebugAgentScript):
    """
    BOCHA-specific debug script implementation.

    Inherits common functionality from DebugAgentScript and implements
    BOCHA-specific methods for query building and request submission.
    """

    # BOCHA-specific cache verification settings
    VERIFY_CACHE_UPDATE = True
    CACHE_UPDATE_TIMEOUT_SECONDS = 3
    VERIFY_CACHE_MODIFICATION = True
    CACHE_MOD_TIMEOUT_SECONDS = 3

    def __init__(self):
        """Initialize BOCHA debug script"""
        super().__init__("BOCHA")

        # Load API key from environment variables
        from src.scheduler.scheduler_settings import SchedulerSettings
        settings = SchedulerSettings.initialize()
        ready_agents = settings.get_ready_agents()
        bocha_config = ready_agents.get("BOCHA")
        if bocha_config:
            self.config.api_key = bocha_config.api_key

        self.agent = BochaAgent(self.config)
        # Store the actual handle_api_request parameters for debugging
        self._last_handle_api_request_params = None

    def get_default_configs(self) -> Dict[str, Any]:
        """
        Return default configuration parameters for BOCHA.

        Returns:
            Dict with BOCHA-specific defaults
        """
        return {
            "query_fields": ["人工智能"],
            "query_topics": ["大模型"],
            "days_back": 7,
            "max_results": 5,
            "language": "zh",
            "include_ai_summary": True,
            "include_raw_response": True,
        }

    def get_handle_api_request_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute the exact parameters that will be passed to handle_api_request().

        This mirrors what actually happens in BochaAgent.call_api() for debugging.

        Args:
            params: Configuration dictionary from user input

        Returns:
            Dict with all parameters that will be passed to handle_api_request()
        """
        from src.utils import get_api_time_filter
        import json

        # Build query string (same as build_query_from_params)
        query_string = self.build_query_from_params(params)

        # Get API-specific time filter
        time_filter = get_api_time_filter(params.get('days_back', 7), "BOCHA")

        # Build request body (same as BochaAgent.call_api)
        body = {
            "query": query_string,
            "freshness": time_filter,
            "count": params.get('max_results', 5),
            "summary": params.get('include_ai_summary', True)
        }

        # Get headers (same as agent)
        headers = self.agent.get_header_dict()

        # Return all parameters
        return {
            "agent_name": "BOCHA",
            "url": self.config.api_endpoint,
            "method": "POST",
            "description": "web_search",
            "json_body": body,
            "headers": headers,
            "timeout": 120,
            "query_request": None  # Will be created during actual call
        }

    def confirm_submission(self, params: Dict[str, Any]) -> bool:
        """
        Display final config with ACTUAL handle_api_request() parameters.

        Override parent to show the exact parameters that will be passed
        to handle_api_request() for easier debugging.
        """
        import json
        from debug_agent_request_abstract import print_section

        print_section("Step 5: Final Submission Confirmation")

        print("BOCHA handle_api_request() PARAMETERS:")
        print()

        # Get the actual parameters
        handle_params = self.get_handle_api_request_params(params)
        self._last_handle_api_request_params = handle_params

        # Display each parameter
        print("Parameters that will be passed to handle_api_request():")
        print()

        print(f"agent_name: {handle_params['agent_name']!r}")
        print()

        print(f"url: {handle_params['url']!r}")
        print()

        print(f"method: {handle_params['method']!r}")
        print()

        print(f"description: {handle_params['description']!r}")
        print()

        print("json_body:")
        print(json.dumps(handle_params['json_body'], indent=2, ensure_ascii=False))
        print()

        print("headers:")
        print(json.dumps(handle_params['headers'], indent=2, ensure_ascii=False))
        print()

        print(f"timeout: {handle_params['timeout']}")
        print()

        print(f"query_request: {handle_params['query_request']}")
        print()

        # Fake response flags
        print("Fake Response Flags (from DebugConfig):")
        print(f"  fake_response_enabled: {DebugConfig.fake_response_enabled}")
        print(f"  fake_response_update: {DebugConfig.fake_response_update}")
        print(f"  fake_response_interact: {DebugConfig.fake_response_interact}")
        print()

        # Ask for confirmation
        while True:
            response = input("Submit request? (y/n): ").strip().lower()
            if response in ['y', 'n']:
                return response == 'y'
            print("Please enter 'y' or 'n'")

    def build_query_from_params(self, params: Dict[str, Any]) -> str:
        """
        Convert parameters to BOCHA query string.

        BOCHA accepts a simple text query, so we combine all fields and topics.

        Args:
            params: Configuration dictionary with query_fields and query_topics

        Returns:
            Combined query string
        """
        # Combine query fields and topics
        all_terms = params.get('query_fields', []) + params.get('query_topics', [])
        query_string = " ".join(all_terms)
        return query_string

    def submit_request(self, query: str, params: Dict[str, Any]) -> Optional[Dict]:
        """
        Execute the BOCHA API call.

        Args:
            query: Query string built by build_query_from_params()
            params: Original parameters (for context)

        Returns:
            Raw API response or None if failed
        """
        # Create QueryRequest for the agent
        query_request = QueryRequest(
            query_fields=params.get('query_fields', []),
            query_topics=params.get('query_topics', []),
            source_agents=["BOCHA"],
            days_back=params.get('days_back', 7),
            max_results=params.get('max_results', 5),
            include_ai_summary=params.get('include_ai_summary', True),
            include_raw_response=params.get('include_raw_response', True),
            language=params.get('language', 'zh')
        )

        # Ensure debug is enabled
        DebugConfig.DEBUG = True

        try:
            print("\n📡 Submitting request to BOCHA API...")
            print(f"   Query: {query}")
            print(f"   Days back: {params.get('days_back', 7)}")
            print(f"   Max results: {params.get('max_results', 5)}")
            print()

            # Call the agent's API
            raw_response = self.agent.call_api(query, query_request)

            if raw_response:
                print("✓ API call successful")
                if isinstance(raw_response, dict):
                    if 'webPages' in raw_response:
                        total_matches = raw_response['webPages'].get('totalEstimatedMatches', 0)
                        results = len(raw_response['webPages'].get('value', []))
                        print(f"  Total matches: {total_matches}")
                        print(f"  Results returned: {results}")
                    print(f"  Response keys: {list(raw_response.keys())}")
                return raw_response
            else:
                print("❌ API call returned None")
                return None

        except Exception as e:
            print(f"❌ Error during API call: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """Main entry point"""
    try:
        script = BochaDebugScript()
        script.run()
    except KeyboardInterrupt:
        print("\n\n⚠ Script interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
