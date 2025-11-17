"""
Explore action - Browse recent research, queries, and results.
"""

from typing import Optional
from datetime import datetime, timedelta
from src.scheduler.actions.base import Action
from src.scheduler.interactive import (
    print_section, print_item, print_success, print_error,
    print_table, prompt_choice, prompt_text
)


class ExploreAction(Action):
    """Action to explore recent research and query history."""

    @property
    def name(self) -> str:
        return "Explore Recent Research"

    @property
    def description(self) -> str:
        return "Browse recent queries, responses, and search results"

    def execute(self) -> bool:
        """Execute explore action."""
        while True:
            explore_options = [
                "View recent queries",
                "View recent responses by agent",
                "View items by source type",
                "Search items by content",
                "Go back to main menu"
            ]

            choice = prompt_choice(explore_options, "What would you like to explore?")

            if choice is None or choice == 4:
                return True

            if choice == 0:
                self._show_recent_queries()
            elif choice == 1:
                self._show_recent_responses()
            elif choice == 2:
                self._show_items_by_source()
            elif choice == 3:
                self._search_items()

    def _show_recent_queries(self, limit: int = 20) -> None:
        """Display recent queries."""
        print_section("Recent Queries")

        try:
            queries = self.db.list_queries(limit=limit)

            if not queries:
                print_error("No queries found in database")
                return

            headers = ["Query ID", "Fields", "Topics", "Agents", "Date"]
            rows = []

            for query in queries:
                fields = ", ".join(query.query_fields[:2])
                if len(query.query_fields) > 2:
                    fields += f" (+{len(query.query_fields) - 2})"

                topics = ", ".join(query.query_topics[:2])
                if len(query.query_topics) > 2:
                    topics += f" (+{len(query.query_topics) - 2})"

                agents = ", ".join(query.source_agents)
                date = query.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(query, 'created_at') else "N/A"

                rows.append([query.query_id[:8], fields, topics, agents, date])

            print_table(headers, rows)

            # Option to view details
            if prompt_text("Enter Query ID (first 8 chars) to view details (or press Enter to skip)", allow_empty=True):
                self._show_query_details(prompt_text.__self__)

        except Exception as e:
            print_error(f"Failed to load queries: {e}")

    def _show_recent_responses(self, limit: int = 20) -> None:
        """Display recent responses by agent."""
        print_section("Recent Responses by Agent")

        try:
            responses = self.db.list_responses(limit=limit)

            if not responses:
                print_error("No responses found in database")
                return

            # Group by agent
            by_agent = {}
            for response in responses:
                agent = response.agent_name
                if agent not in by_agent:
                    by_agent[agent] = []
                by_agent[agent].append(response)

            for agent, agent_responses in sorted(by_agent.items()):
                print_item(agent, f"{len(agent_responses)} responses")

                headers = ["Response ID", "Status", "Items", "Time (ms)", "Date"]
                rows = []

                for resp in agent_responses[:10]:  # Show top 10 per agent
                    rows.append([
                        resp.response_id[:8],
                        resp.status,
                        str(resp.items_count),
                        str(resp.execution_time_ms or 0),
                        resp.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(resp, 'created_at') else "N/A"
                    ])

                print_table(headers, rows)

        except Exception as e:
            print_error(f"Failed to load responses: {e}")

    def _show_items_by_source(self) -> None:
        """Display items grouped by source type."""
        print_section("Items by Source Type")

        try:
            # Get items from database
            items = self.db.search_items(limit=1000)

            if not items:
                print_error("No items found in database")
                return

            # Group by source type
            by_source = {}
            for item in items:
                source = item.source_type
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(item)

            headers = ["Source Type", "Count", "Latest"]
            rows = []

            for source, source_items in sorted(by_source.items()):
                latest = max(source_items, key=lambda x: x.timestamp)
                rows.append([
                    source,
                    str(len(source_items)),
                    latest.timestamp.strftime("%Y-%m-%d %H:%M")
                ])

            print_table(headers, rows)

            # Show sample from selected source
            source_choice = prompt_choice(list(by_source.keys()), "Select a source to view samples")
            if source_choice is not None:
                self._show_source_samples(list(by_source.keys())[source_choice], by_source)

        except Exception as e:
            print_error(f"Failed to load items: {e}")

    def _show_source_samples(self, source_type: str, by_source: dict, limit: int = 5) -> None:
        """Display sample items from a source."""
        items = by_source[source_type][:limit]

        print(f"\n{source_type} - Sample Items (showing {len(items)}/{len(by_source[source_type])}):\n")

        for i, item in enumerate(items, 1):
            print(f"{i}. {item.title}")
            print(f"   Source: {item.source_name}")
            print(f"   URL: {item.source_url}")
            print(f"   Date: {item.timestamp.strftime('%Y-%m-%d %H:%M')}")
            if item.content:
                content_preview = item.content[:100] + "..." if len(item.content) > 100 else item.content
                print(f"   Content: {content_preview}")
            print()

    def _search_items(self) -> None:
        """Search items by keyword."""
        print_section("Search Items")

        keyword = prompt_text("Enter search keyword")
        if not keyword:
            return

        try:
            # Simple search in database (implement in DatabaseManager if needed)
            all_items = self.db.search_items(limit=1000)
            matched = [item for item in all_items
                      if keyword.lower() in item.title.lower() or
                      keyword.lower() in item.content.lower()]

            if not matched:
                print_error(f"No items found matching '{keyword}'")
                return

            print_success(f"Found {len(matched)} items matching '{keyword}'")
            print()

            for item in matched[:10]:  # Show top 10
                print(f"Title: {item.title}")
                print(f"Source: {item.source_name} ({item.source_type})")
                print(f"URL: {item.source_url}")
                print(f"Date: {item.timestamp.strftime('%Y-%m-%d %H:%M')}")
                print()

        except Exception as e:
            print_error(f"Search failed: {e}")
