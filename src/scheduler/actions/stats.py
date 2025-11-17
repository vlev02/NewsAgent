"""
Stats action - Display database statistics and project overview.
"""

from src.scheduler.actions.base import Action
from src.scheduler.interactive import (
    print_section, print_item, print_info, print_table
)


class StatsAction(Action):
    """Action to display database statistics."""

    @property
    def name(self) -> str:
        return "View Statistics"

    @property
    def description(self) -> str:
        return "Display database statistics and project overview"

    def execute(self) -> bool:
        """Execute stats action."""
        print_section("Database Statistics")

        try:
            stats = self.db.get_stats()

            # Display overview
            print_item("Total Queries", str(stats.get("total_queries", 0)))
            print_item("Total Responses", str(stats.get("total_responses", 0)))
            print_item("Total Items", str(stats.get("total_items", 0)))
            print_item("Unique Sources", str(stats.get("unique_sources", 0)))
            print()

            # Display agent breakdown
            responses_by_agent = stats.get("responses_by_agent", {})
            if responses_by_agent:
                print_section("Responses by Agent")
                headers = ["Agent", "Count"]
                rows = [[agent, str(count)] for agent, count in responses_by_agent.items()]
                print_table(headers, rows)
                print()

            # Display source breakdown
            items_by_source = stats.get("items_by_source", {})
            if items_by_source:
                print_section("Items by Source Type")
                headers = ["Source", "Count"]
                rows = [[source, str(count)] for source, count in items_by_source.items()]
                print_table(headers, rows)
                print()

            return True

        except Exception as e:
            print_info(f"Failed to load statistics: {e}")
            return False
