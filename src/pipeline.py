"""Search pipeline orchestrator"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from src.agents.base import SearchAgent
from src.dataclasses import QueryRequest, QueryResponse, SearchItem
from src.database.manager import DatabaseManager


class SearchPipeline:
    """
    Orchestrates multiple agents with database persistence.

    Executes queries across multiple agents in parallel,
    aggregates results, and stores everything in the database.
    """

    def __init__(self, agents: Dict[str, SearchAgent],
                 db_manager: DatabaseManager):
        """
        Initialize pipeline.

        Args:
            agents: Dict mapping agent names to SearchAgent instances
            db_manager: DatabaseManager for persistence
        """
        self.agents = agents
        self.db = db_manager

    async def execute_query_async(self,
                                  request: QueryRequest) -> Dict[str, QueryResponse]:
        """
        Execute query across agents in parallel.

        Args:
            request: QueryRequest to execute

        Returns:
            Dict mapping agent names to QueryResponse objects
        """
        # Save query to database
        self.db.save_query(request)

        # Execute agents in parallel
        tasks = []
        agent_names = []

        for agent_name in request.source_agents:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                tasks.append(agent.submit_and_parse(request))
                agent_names.append(agent_name)

        # Run all tasks concurrently
        responses = await asyncio.gather(*tasks)

        # Save responses and items
        response_dict = {}
        for agent_name, response in zip(agent_names, responses):
            response.agent_name = agent_name
            response.query_id = request.query_id
            response.timestamp = datetime.now()
            self.db.save_response(response)
            response_dict[agent_name] = response

        return response_dict

    def execute_query(self, request: QueryRequest) -> Dict[str, QueryResponse]:
        """
        Execute query synchronously.

        Args:
            request: QueryRequest to execute

        Returns:
            Dict mapping agent names to QueryResponse objects
        """
        # For synchronous execution, just call agents directly
        self.db.save_query(request)

        response_dict = {}
        for agent_name in request.source_agents:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                response = agent.submit_and_parse(request)
                response.agent_name = agent_name
                response.query_id = request.query_id
                response.timestamp = datetime.now()
                self.db.save_response(response)
                response_dict[agent_name] = response

        return response_dict

    def aggregate_results(self,
                         responses: Dict[str, QueryResponse],
                         merge_strategy: str = "dedup_by_url") -> List[SearchItem]:
        """
        Combine and deduplicate results from multiple agents.

        Args:
            responses: Dict of QueryResponse objects from agents
            merge_strategy: "dedup_by_url" | "dedup_by_title" | "content_hash" | "union"

        Returns:
            Aggregated list of SearchItem objects
        """
        all_items = []
        for response in responses.values():
            all_items.extend(response.items)

        # Deduplicate
        deduplicated = self.db.deduplicate_items(all_items, strategy=merge_strategy)

        return deduplicated

    def generate_report(self,
                       request: QueryRequest,
                       responses: Dict[str, QueryResponse],
                       items: List[SearchItem]) -> Dict:
        """
        Generate execution report with statistics.

        Args:
            request: Original QueryRequest
            responses: Dict of QueryResponse objects
            items: Aggregated SearchItem list

        Returns:
            Report dict with statistics
        """
        report = {
            "query_id": request.query_id,
            "timestamp": datetime.now().isoformat(),
            "query": {
                "fields": request.query_fields,
                "topics": request.query_topics,
                "source_agents": request.source_agents,
                "days_back": request.days_back
            },
            "execution": {
                "total_agents": len(responses),
                "successful_agents": sum(1 for r in responses.values() if r.success),
                "failed_agents": sum(1 for r in responses.values() if not r.success),
                "agents": {}
            },
            "results": {
                "total_items": len(items),
                "total_raw_items": sum(len(r.items) for r in responses.values()),
                "duplicates_removed": sum(len(r.items) for r in responses.values()) - len(items),
                "items_by_source": {}
            }
        }

        # Per-agent stats
        for agent_name, response in responses.items():
            report["execution"]["agents"][agent_name] = {
                "success": response.success,
                "items_returned": len(response.items),
                "execution_time_ms": response.execution_time_ms,
                "status": response.status,
                "error": response.error_message,
                "tokens_used": response.tokens_used
            }

        # Items by source
        for source_type in set(item.source_type for item in items):
            report["results"]["items_by_source"][source_type] = \
                len([i for i in items if i.source_type == source_type])

        return report

    def print_report(self, report: Dict) -> None:
        """Pretty-print execution report"""
        print("\n" + "="*70)
        print("SEARCH PIPELINE EXECUTION REPORT")
        print("="*70)

        query = report['query']
        print(f"\nQuery ID: {report['query_id']}")
        print(f"Fields: {', '.join(query['fields'])}")
        print(f"Topics: {', '.join(query['topics'])}")
        print(f"Agents: {', '.join(query['source_agents'])}")
        print(f"Time Range: Last {query['days_back']} days")

        print("\nEXECUTION:")
        exec_stats = report['execution']
        print(f"  Successful: {exec_stats['successful_agents']}/{exec_stats['total_agents']}")
        print(f"  Failed: {exec_stats['failed_agents']}/{exec_stats['total_agents']}")

        print("\nPER-AGENT RESULTS:")
        for agent, stats in exec_stats['agents'].items():
            status_mark = "✓" if stats['success'] else "✗"
            print(f"  {status_mark} {agent}: {stats['items_returned']} items " +
                  f"({stats['execution_time_ms']}ms)")
            if stats['error']:
                print(f"      Error: {stats['error']}")

        print("\nAGGREGATED RESULTS:")
        result_stats = report['results']
        print(f"  Total Items (after dedup): {result_stats['total_items']}")
        print(f"  Raw Items (before dedup): {result_stats['total_raw_items']}")
        print(f"  Duplicates Removed: {result_stats['duplicates_removed']}")

        if result_stats['items_by_source']:
            print("\n  Items by Source:")
            for source, count in result_stats['items_by_source'].items():
                print(f"    {source}: {count}")

        print("="*70 + "\n")
