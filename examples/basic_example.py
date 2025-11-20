"""
Basic example of using the NewsAgent pipeline.

This example shows how to:
1. Create a query request
2. Execute it with one or more agents
3. Access results from the database
"""

import os
from datetime import datetime
from dotenv import load_dotenv

from src.dataclasses import QueryRequest
from src.dataclasses.config import BOCHA_CONFIG
from src.agents.agent_bocha import BochaAgent
from src.database import SQLite3Backend, DatabaseManager
from src.pipeline import SearchPipeline


def main():
    """Run basic pipeline example"""

    # Load environment variables from .env file
    load_dotenv()

    # 1. Setup database
    db_backend = SQLite3Backend(db_path="newsagent.db")
    db_manager = DatabaseManager(db_backend)
    db_manager.connect()

    # 2. Setup agents
    # For this example, we'll use BOCHA which is a REST API
    bocha_api_key = os.getenv("BOCHA_API_KEY")
    if not bocha_api_key:
        print("\n⚠️  WARNING: BOCHA_API_KEY not set in environment")
        print("Set your API key: export BOCHA_API_KEY='your-key-here'")
        print("Or copy .env.example to .env and fill in API keys\n")
        bocha_api_key = "demo-key"

    bocha_config = BOCHA_CONFIG
    bocha_config.api_key = bocha_api_key

    bocha_agent = BochaAgent(bocha_config)

    agents = {
        "BOCHA": bocha_agent
    }

    # 3. Create pipeline
    pipeline = SearchPipeline(agents, db_manager)

    # 4. Create a query request
    query = QueryRequest(
        query_fields=["自动驾驶", "具身智能", "大模型"],
        query_topics=["特斯拉FSD", "人形机器人", "AI大模型突破"],
        source_agents=["BOCHA"],
        days_back=7,
        time_filter="oneWeek",
        max_results=10,
        include_ai_summary=True,
        language="zh"
    )

    print("\n" + "="*70)
    print("NEWSAGENT PIPELINE - BASIC EXAMPLE")
    print("="*70)
    print(f"\nQuery ID: {query.query_id}")
    print(f"Fields: {', '.join(query.query_fields)}")
    print(f"Topics: {', '.join(query.query_topics)}")
    print(f"Agents: {', '.join(query.source_agents)}")
    print(f"Time Range: {query.days_back} days")

    # 5. Execute query
    print("\nExecuting query...")
    responses = pipeline.execute_query(query)

    # 6. Aggregate results
    aggregated_items = pipeline.aggregate_results(responses)

    # 7. Generate report
    report = pipeline.generate_report(query, responses, aggregated_items)
    pipeline.print_report(report)

    # 8. Display sample results
    print("\nSAMPLE RESULTS (first 3 items):")
    print("-" * 70)
    for i, item in enumerate(aggregated_items[:3], 1):
        print(f"\n{i}. {item.title}")
        print(f"   Source: {item.source_name} ({item.source_type})")
        print(f"   URL: {item.source_url}")
        print(f"   Date: {item.timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Content: {item.content[:150]}...")

    # 9. Check database stats
    print("\n" + "="*70)
    db_manager.print_stats()

    # 10. Query database
    print("\nQuerying database...")
    recent_queries = db_manager.list_queries(limit=5)
    print(f"Recent queries: {len(recent_queries)}")

    recent_responses = db_manager.list_responses(limit=5)
    print(f"Recent responses: {len(recent_responses)}")

    recent_items = db_manager.get_recent_items(days=7, limit=10)
    print(f"Recent items (7 days): {len(recent_items)}")

    # Cleanup
    db_manager.disconnect()
    print("\nExample completed!")


if __name__ == "__main__":
    main()
