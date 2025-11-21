#!/usr/bin/env python3
import os
import sys
import json
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
            result = agent.submit_request()
            print("\nResponse received")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:500] + "...")
        else:
            print("Request cancelled.")

    except KeyError as e:
        print(f"\nAPI Key required: {e}")
        print(f"Set environment variable or use: manager.add_api_key()")

if __name__ == "__main__":
    main()
