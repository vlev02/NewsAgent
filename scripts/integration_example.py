#!/usr/bin/env python3
"""
Integration Example: Applying @simu_request to SearchAgent

This example shows how to integrate the @simu_request decorator with
actual SearchAgent subclasses like BochaAgent.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path.cwd().parent if 'scripts' in str(Path.cwd()) else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.simu_request import simu_request, SimuCallConfig
from src.agents.base import SearchAgent
from src.dataclasses import AgentConfig, QueryRequest, QueryResponse, SearchItem

print("="*70)
print("SearchAgent Integration Example")
print("="*70)

# Example: How to integrate with existing agents

example_code = '''
from src.utils.simu_request import simu_request
from src.agents.base import SearchAgent
import requests

class BochaAgent(SearchAgent):
    """BOCHA Search Agent with caching"""

    NAME = "BOCHA"
    api_keys = ["BOCHA_API_KEY"]

    def _get_request_schema_class(self):
        # ... existing implementation ...
        pass

    def build_query(self, request):
        # ... existing implementation ...
        pass

    @simu_request  # ← Add this decorator!
    def submit_request(self, query, request):
        """Submit request to BOCHA API with automatic caching"""

        # Your existing code - unchanged!
        response = requests.post(
            self.api_endpoint,
            json=self.request_body,
            headers=self.get_header_dict(),
            timeout=120
        )

        return response.json()

    def parse_response(self, raw_response):
        # ... existing implementation ...
        pass
'''

print("\nExample Integration Code:")
print("-" * 70)
print(example_code)

print("\n" + "="*70)
print("Configuration Options")
print("="*70)

config_examples = {
    "Offline Development": {
        "debug": 1,
        "description": "Capture and use cached responses"
    },
    "Testing": {
        "simu_call": 1,
        "update_response": 0,
        "description": "Use cached responses, no real API calls"
    },
    "Refresh Cache": {
        "simu_call": 0,
        "update_response": 1,
        "description": "Make real API calls and update cache"
    },
    "No Caching": {
        "simu_call": 0,
        "update_response": 0,
        "description": "Always call real API, no caching"
    }
}

for scenario, config in config_examples.items():
    print(f"\n{scenario}:")
    print(f"  Description: {config.pop('description')}")
    for key, value in config.items():
        print(f"  {key}: {value}")

print("\n" + "="*70)
print("Cache Storage")
print("="*70)

print("""
Cache files are automatically stored at:

  data/simu_responses/{ClassName}/{method_name}_{md5_hash}.json

Examples:
  • data/simu_responses/BochaAgent/submit_request_a1b2c3d4e5f6g7h8.json
  • data/simu_responses/XunfeiAgent/submit_request_f7h8i9j0k1l2m3n4.json
  • data/simu_responses/MetaAgent/submit_request_b2c3d4e5f6g7h8i9.json

Each cache file contains:
  {
    "response": {...},  // The actual API response
    "metadata": {
      "request_body": {...},
      "headers": {...}
    }
  }
""")

print("\n" + "="*70)
print("Step-by-Step Integration Guide")
print("="*70)

steps = """
1. Import the decorator:
   from src.utils.simu_request import simu_request

2. Apply decorator to submit_request:
   @simu_request
   def submit_request(self, query, request):
       response = requests.post(...)
       return response.json()

3. Configure behavior in config/simu_call.yaml:
   debug: 1              # Enable caching
   simu_call: 1          # Use cached responses
   update_response: 1    # Save new responses
   persist_dir: "data/simu_responses"

4. Run your code - caching works automatically!
   agent = BochaAgent(config)
   result = agent.submit_request(...)  # Uses cache if available

5. Manage cache as needed:
   - View cache: find data/simu_responses -name "*.json"
   - Clear cache: rm -rf data/simu_responses/
   - Update cache: Set debug: 1 and run
"""

print(steps)

print("\n" + "="*70)
print("Current Configuration")
print("="*70)

config = SimuCallConfig()
print(f"simu_call:       {config.get('simu_call')} (Load cache)")
print(f"update_response: {config.get('update_response')} (Save cache)")
print(f"debug:           {config.get('debug')} (Master flag)")
print(f"persist_dir:     {config.get('persist_dir')}")
print(f"log_calls:       {config.get('log_calls')}")

print("\n" + "="*70)
print("Benefits")
print("="*70)

benefits = """
✓ Offline Development
  • Capture real API responses once
  • Develop without internet access
  • Faster iteration (cache ~1ms vs API ~100ms-5s)

✓ Testing
  • Deterministic responses
  • No external dependencies
  • Tests run 100-1000x faster

✓ Cost Reduction
  • Avoid repeated API calls
  • Save on API quotas
  • Predictable usage

✓ Debugging
  • Inspect exact API responses
  • Reproduce issues reliably
  • Compare old vs new responses

✓ Simple Integration
  • Just add @simu_request decorator
  • No code changes needed
  • Works with existing agents
"""

print(benefits)

print("\n" + "="*70)
print("Next Steps")
print("="*70)

print("""
1. Add @simu_request to your SearchAgent.submit_request method
2. Update config/simu_call.yaml with desired flags
3. Run your code - caching works automatically!
4. Check data/simu_responses/ for cached files
5. Adjust flags based on your workflow

For detailed documentation:
  See SIMU_REQUEST_GUIDE.md

For examples:
  See scripts/example_simu_request.py

For testing:
  Run: python -m pytest tests/test_simu_request.py -v
""")
