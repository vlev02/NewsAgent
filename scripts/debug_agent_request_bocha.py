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
        self.agent = BochaAgent(self.config)

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
