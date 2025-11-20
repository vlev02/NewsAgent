#!/usr/bin/env python3
"""
Example script demonstrating AgentManager usage.

This script shows how to:
1. Get the AgentManager instance
2. View available agents (marketplace)
3. Create and initialize agents
4. Access agent configuration and properties
5. Understand agent request schema
"""

from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agents import get_agent_manager


def print_header(title: str):
    """Print a section header"""
    print()
    print("=" * 80)
    print(f" {title}")
    print("=" * 80)


def example_1_get_manager():
    """Example 1: Get AgentManager instance"""
    print_header("Example 1: Get AgentManager Instance")

    # Get the global AgentManager instance
    manager = get_agent_manager()

    print(f"Manager: {manager}")
    print(f"Manager type: {type(manager).__name__}")
    print()


def example_2_agent_marketplace():
    """Example 2: View available agents"""
    print_header("Example 2: Agent Marketplace")

    manager = get_agent_manager()

    # Get the marketplace (available agents)
    marketplace = manager.agent_marketplace

    print("Available agents:")
    for agent_name, agent_type in sorted(marketplace.items()):
        print(f"  • {agent_name:12} ({agent_type})")
    print()

    print(f"Total agents available: {len(marketplace)}")
    print()


def example_3_agent_configuration():
    """Example 3: Access agent configuration"""
    print_header("Example 3: Agent Configuration")

    manager = get_agent_manager()

    # Get configuration for a specific agent
    bocha_config = manager.get_agent_config('BOCHA')

    print(f"Agent: {bocha_config.agent_name}")
    print(f"Type: {bocha_config.agent_type}")
    print(f"Endpoint: {bocha_config.api_endpoint}")
    print(f"Auth Header: {bocha_config.auth_header_name}")
    print(f"Auth Prefix: {bocha_config.auth_prefix}")
    print()

    print("Default Query Parameters:")
    for key, value in bocha_config.default_params.items():
        print(f"  • {key:15} = {value}")
    print()


def example_4_create_agent():
    """Example 4: Create and initialize an agent"""
    print_header("Example 4: Create Agent Instance")

    manager = get_agent_manager()

    # Create a BOCHA agent with API key
    print("Creating BOCHA agent...")
    agent = manager.create_agent('BOCHA', api_key='test-api-key-12345')

    print(f"✓ Agent created: {type(agent).__name__}")
    print()

    # Access agent properties
    print("Agent Properties:")
    print(f"  • NAME (class property): {agent.NAME}")
    print(f"  • Config name: {agent.config.agent_name}")
    print(f"  • Config type: {agent.config.agent_type}")
    print(f"  • API Endpoint: {agent.config.api_endpoint}")
    print()


def example_5_agent_schema():
    """Example 5: Understand agent RequestSchema"""
    print_header("Example 5: Agent RequestSchema")

    manager = get_agent_manager()

    # Create agent
    agent = manager.create_agent('BOCHA', api_key='test-key')

    # Access schema information
    print(f"RequestSchema Type: {type(agent.request_schema).__name__}")
    print(f"Schema class: {agent.request_schema.__class__}")
    print()

    print("Schema has method 'validate_and_get_dict':")
    print(f"  {hasattr(agent.request_schema, 'validate_and_get_dict')}")
    print()

    # Convert schema to dict
    schema_dict = agent.request_schema.validate_and_get_dict()
    print("Current schema as dictionary:")
    for key, value in schema_dict.items():
        print(f"  • {key:15} = {value}")
    print()


def example_6_query_body():
    """Example 6: Work with agent query_body"""
    print_header("Example 6: Agent Query Body")

    manager = get_agent_manager()
    agent = manager.create_agent('BOCHA', api_key='test-key')

    print("Initial query_body:")
    for key, value in agent.query_body.items():
        print(f"  • {key:15} = {value}")
    print()

    # Modify query_body
    print("Modifying query_body...")
    new_body = agent.query_body
    new_body['query'] = 'machine learning'
    new_body['count'] = 20
    agent.query_body = new_body
    print("✓ Query body updated")
    print()

    print("Updated query_body:")
    for key, value in agent.query_body.items():
        print(f"  • {key:15} = {value}")
    print()

    print("Updated schema:")
    updated_schema = agent.request_schema.validate_and_get_dict()
    for key, value in updated_schema.items():
        print(f"  • {key:15} = {value}")
    print()


def example_7_multiple_agents():
    """Example 7: Create multiple agents"""
    print_header("Example 7: Create Multiple Agents")

    manager = get_agent_manager()

    print("Creating all available agents...")
    agents = {}

    for agent_name in manager.agent_marketplace.keys():
        try:
            agent = manager.create_agent(agent_name, api_key='dummy-key')
            agents[agent_name] = agent
            print(f"  ✓ {agent_name:12} -> {type(agent).__name__}")
        except KeyError as e:
            print(f"  ✗ {agent_name:12} -> NOT IMPLEMENTED (not in registry)")

    print()
    print(f"Successfully created: {len(agents)} agents")
    print()

    # Show each agent's properties
    print("Agent Properties:")
    for agent_name, agent in agents.items():
        print(f"  {agent_name:12} - NAME={agent.NAME}, Type={agent.config.agent_type}")
    print()


def example_8_error_handling():
    """Example 8: Error handling"""
    print_header("Example 8: Error Handling")

    manager = get_agent_manager()

    # Try to get non-existent agent
    print("Attempting to get non-existent agent config...")
    try:
        config = manager.get_agent_config('NONEXISTENT')
    except KeyError as e:
        print(f"✓ Caught expected error: {e}")
    print()

    # Try to create unimplemented agent
    print("Attempting to create unimplemented agent...")
    try:
        # This agent might be in config but not implemented
        agent = manager.create_agent('XUNFEI', api_key='test-key')
        print(f"✓ Agent created (XUNFEI is implemented)")
    except KeyError as e:
        print(f"✓ Caught expected error: {e}")
    print()


def main():
    """Run all examples"""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  AgentManager Usage Examples".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")

    # Run examples
    example_1_get_manager()
    example_2_agent_marketplace()
    example_3_agent_configuration()
    example_4_create_agent()
    example_5_agent_schema()
    example_6_query_body()
    example_7_multiple_agents()
    example_8_error_handling()

    # Summary
    print_header("Summary")
    print("""
Key Takeaways:

1. AgentManager is a singleton - use get_agent_manager() to access it
2. Agent marketplace shows all available agents from agents.yaml
3. Each agent configuration includes all default parameters
4. Create agents with manager.create_agent(name, api_key)
5. Each agent maintains a RequestSchema instance
6. Modify agent behavior via query_body property
7. Agent NAME property provides fixed agent identifier
8. Error handling for missing or unimplemented agents

For more information, see:
  • src/agents/manager.py - AgentManager implementation
  • src/agents/base.py - SearchAgent base class
  • config/agents.yaml - Agent configurations
    """)


if __name__ == "__main__":
    main()
