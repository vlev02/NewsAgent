#!/usr/bin/env python3
import os
import sys
import json
import time
from pathlib import Path

# Disable proxy for direct API calls
# This removes any system proxy configuration that might block requests
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

project_root = Path.cwd().parent if 'scripts' in str(Path.cwd()) else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agents import get_agent_manager
from src.utils.simu_request import SimuRequest
from src.data_manager import get_data_manager, DataModelType, RequestModel, QueryModel

def print_agents(marketplace):
    print("\nAvailable Agents:")
    for idx, (name, agent_type) in enumerate(sorted(marketplace.items()), 1):
        print(f"  {idx}. {name:12} ({agent_type})")
    print()

def display_request(agent):
    body = agent.request_body
    headers = agent.get_header_dict()

    print("\n" + "="*70)
    print("HTTP REQUEST CONFIGURATION (Raw JSON)")
    print("="*70)

    request_dict = {
        "url": agent.api_endpoint,
        "method": "POST",
        "headers": headers,
        "json": body,
    }

    print(json.dumps(request_dict, indent=2, ensure_ascii=False))
    print("="*70 + "\n")

def record_to_data_manager(agent, response, execution_time_ms, success=True, error_msg=None):
    """
    Use AgentDataWrapper parse methods to record request and response to DataManager.

    This demonstrates the AgentDataWrapper integration with DataManager.

    Note: SimuRequest decorator wraps responses in {"response": ..., "response_type": "..."}
    """
    try:
        dm = get_data_manager()

        # Step 1: Record the raw API request using parse_request()
        print("\n" + "-"*70)
        print("Recording to DataManager using AgentDataWrapper...")
        print("-"*70)

        # Extract response_type from decorator-wrapped response
        response_type = "real_call"
        actual_response = response
        if isinstance(response, dict) and "response_type" in response:
            response_type = response.get("response_type", "real_call")
            actual_response = response.get("response")

        request_data = agent.parse_request(
            http_status=200 if success else 500,
            raw_response=actual_response if success else None,
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_msg,
            response_type=response_type
        )

        request_id = dm.record(DataModelType.REQUEST, request_data)
        print(f"✓ RequestModel recorded: {request_id}")

        # Step 2: Record the parsed query using parse_query()
        query_data = agent.parse_query(
            request_id=request_id,
            max_results=10
        )

        request_model = RequestModel(request_id=request_id, agent_name=agent.NAME)
        query_id = dm.record(DataModelType.QUERY, query_data, associated_case=request_model)
        print(f"✓ QueryModel recorded: {query_id}")

        # Step 3: Try to record response items (if agent implements item parsing)
        try:
            items = agent.parse_response_items(actual_response if success else {})
            if items:
                query_model = QueryModel(query_id=query_id, request_id=request_id)
                item_count = 0
                for item_data in items:
                    item_id = dm.record(DataModelType.RESPONSE_ITEM, item_data, associated_case=query_model)
                    item_count += 1
                print(f"✓ Recorded {item_count} ResponseItem(s)")
            else:
                print("  (No response items to record)")
        except Exception as e:
            print(f"  (Response item parsing not implemented: {type(e).__name__})")

        # Step 4: Display DataManager statistics
        print("\n" + "-"*70)
        print("DataManager Statistics:")
        print("-"*70)
        request_report = dm.explore(DataModelType.REQUEST)
        query_report = dm.explore(DataModelType.QUERY)
        item_report = dm.explore(DataModelType.RESPONSE_ITEM)

        print(f"  RequestModels: {request_report['total']} total")
        print(f"  QueryModels:   {query_report['total']} total")
        print(f"  ResponseItems: {item_report['total']} total")
        print("-"*70 + "\n")

    except Exception as e:
        print(f"\n✗ Error recording to DataManager: {e}")
        import traceback
        traceback.print_exc()

def main():
    manager = get_agent_manager()
    marketplace = manager.agent_marketplace

    if not marketplace:
        print("No agents available")
        return

    print("\n" + "="*70)
    print("SIMU_REQUEST CONFIGURATION")
    print("="*70)
    SimuRequest.status()
    print()

    agent_list = sorted(marketplace.keys())

    while True:
        print_agents(marketplace)

        try:
            choice = input("Select agent (number): ").strip()
            if not choice:
                continue

            idx = int(choice) - 1
            if 0 <= idx < len(agent_list):
                agent_name = agent_list[idx]
                break
            else:
                print(f"Invalid selection. Choose 1-{len(agent_list)}\n")
        except ValueError:
            print("Invalid input\n")

    config = manager.get_agent_config(agent_name)
    print(f"\n✓ Selected: {agent_name} ({config.agent_type})")

    try:
        agent = manager.create_agent(agent_name)
        display_request(agent)

        response = input("Submit request? (y/n, default=y): ").strip().lower()
        # Default to 'y' if empty input
        if response == '' or response == 'y':
            print("\n" + "="*70)
            print("SIMU_REQUEST CONFIGURATION (Before Submission)")
            print("="*70)
            SimuRequest.status()
            print()

            print("Submitting...")
            start_time = time.time()
            result = agent.submit_request()
            execution_time_ms = int((time.time() - start_time) * 1000)
            print("\nResponse received")
            # Handle decorator-wrapped response
            display_result = result
            if isinstance(result, dict) and "response_type" in result:
                display_result = result.get("response", result)
            print(json.dumps(display_result, indent=2, ensure_ascii=False)[:500] + "...")

            # Record to DataManager using AgentDataWrapper parse methods
            record_to_data_manager(agent, result, execution_time_ms, success=True)
        else:
            print("Request cancelled.")

    except KeyError as e:
        print(f"\nAPI Key required: {e}")
        print(f"Set environment variable or use: manager.add_api_key()")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
