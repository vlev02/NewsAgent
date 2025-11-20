#!/usr/bin/env python3
"""
Example: Using simu_request decorator with SearchAgent

Demonstrates how to apply the @simu_request decorator to SearchAgent.submit_request
method to enable caching with minimal configuration.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path.cwd().parent if 'scripts' in str(Path.cwd()) else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.simu_request import simu_request, SimuCallConfig


# Example 1: Checking current configuration
print("="*70)
print("Current Simulation Configuration")
print("="*70)

config = SimuCallConfig()
print(f"simu_call:      {config.get('simu_call')}")
print(f"update_response: {config.get('update_response')}")
print(f"debug:          {config.get('debug')}")
print(f"persist_dir:    {config.get('persist_dir')}")
print(f"log_calls:      {config.get('log_calls')}")


# Example 2: Simple mock agent to demonstrate decorator
print("\n" + "="*70)
print("Example Agent with @simu_request Decorator")
print("="*70)


class ExampleAgent:
    """Simple example agent showing @simu_request usage"""

    NAME = "EXAMPLE"

    def __init__(self):
        self.call_count = 0

    @simu_request
    def submit_request(self, query, request):
        """
        Example submit_request method with @simu_request decorator.

        In real SearchAgent, this would call:
            response = requests.post(self.api_endpoint, json=self.request_body)

        For this example, we just return a mock response.
        """
        self.call_count += 1
        print(f"    [ExampleAgent] Processing query: {query}")

        # Mock API response
        response = {
            "status": "success",
            "results": [
                {"title": "Result 1", "url": "https://example.com/1"},
                {"title": "Result 2", "url": "https://example.com/2"},
            ],
            "call_count": self.call_count
        }

        return response


# Create agent and make calls
agent = ExampleAgent()

print("\nFirst call (will cache if update_response=1):")
result1 = agent.submit_request("test query", None)
print(f"  Result: {result1}")

print("\nSecond call (will use cache if simu_call=1):")
result2 = agent.submit_request("test query", None)
print(f"  Result: {result2}")

if result1 == result2:
    print("\n✓ Responses are identical (cache is working)")
else:
    print("\n✓ Responses differ (cache is not enabled)")


# Example 3: Showing cache file location
print("\n" + "="*70)
print("Cache File Location")
print("="*70)

from src.utils.simu_request import _get_cache_path

cache_path = _get_cache_path("ExampleAgent", "submit_request")
print(f"Cache would be stored at:")
print(f"  {cache_path}")
print(f"Relative path: {cache_path.relative_to(cache_path.parent.parent.parent)}")

if cache_path.exists():
    print(f"\n✓ Cache file exists!")
    import json
    with open(cache_path) as f:
        cache_data = json.load(f)
    print(f"Cached response: {json.dumps(cache_data['response'], indent=2)}")
else:
    print(f"\n✗ Cache file does not exist (enable update_response=1 to create)")


# Example 4: How to use with SearchAgent
print("\n" + "="*70)
print("Integration with SearchAgent")
print("="*70)

print("""
To use @simu_request with SearchAgent.submit_request:

1. Import the decorator:
   from src.utils.simu_request import simu_request

2. Apply to submit_request method:
   class MySearchAgent(SearchAgent):
       @simu_request
       def submit_request(self, query, request):
           # Make API call
           response = requests.post(...)
           return response

3. Control behavior via config/simu_call.yaml:
   debug: 1              # Enable both simu_call and update_response
   simu_call: 1          # Use cached responses
   update_response: 1    # Update cache with real calls
   persist_dir: "data/simu_responses"

4. Cache files are automatically stored as:
   data/simu_responses/{ClassName}/submit_request_{md5_hash}.json
""")


# Example 5: Configuration flags explanation
print("\n" + "="*70)
print("Configuration Flags Explained")
print("="*70)

print("""
simu_call = 1:
  • If cache exists: Return cached response (no API call)
  • If cache missing: Call real API

simu_call = 0:
  • Always call real API, ignore cache

update_response = 1:
  • When calling real API: Save response to cache
  • When using cache: Don't update

update_response = 0:
  • Never save API responses to cache

debug = 1:
  • Enables: simu_call = 1 AND update_response = 1
  • Overrides individual flag settings

debug = 0:
  • Disables: simu_call = 0 AND update_response = 0
  • Uses individual flag settings
""")


# Example 6: Practical workflow
print("\n" + "="*70)
print("Practical Workflow")
print("="*70)

print("""
Development Flow:

1. First time development (capture API responses):
   debug: 1           # Cache all responses

   Run your code normally. Real API calls are cached automatically.

2. Development without internet (offline):
   simu_call: 1       # Use cached responses
   update_response: 0 # Don't make real calls

   All API calls return cached responses.

3. Testing (predictable responses):
   simu_call: 1       # Use cached responses
   update_response: 0 # No real API calls

   Tests run fast and deterministically.

4. Refresh cache (update stale data):
   simu_call: 0       # Make real API calls
   update_response: 1 # Save new responses

   Fetch fresh data and cache it.
""")
