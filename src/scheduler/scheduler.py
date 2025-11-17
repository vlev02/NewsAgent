"""
Main Scheduler class - Interactive terminal-based pipeline manager.
"""

from typing import Optional, Dict, Any
from src.database import DatabaseManager, SQLite3Backend
from src.dataclasses.config import AgentConfig
from src.scheduler.config import SchedulerConfig, get_agent_configs
from src.scheduler.interactive import (
    print_header, print_section, print_item, print_info,
    print_success, print_warning, prompt_choice
)
from src.scheduler.actions import (
    ExploreAction, SubmitQueryAction, ExportAction,
    StatsAction, SettingsAction
)


class Scheduler:
    """Interactive terminal-based scheduler for managing agents and queries."""

    def __init__(self, config: Optional[SchedulerConfig] = None, agents_config: Optional[Dict[str, AgentConfig]] = None):
        """
        Initialize scheduler.

        Args:
            config: Scheduler configuration
            agents_config: Agent configurations dictionary
        """
        self.config = config or SchedulerConfig.from_env()
        self.agents_config = agents_config or get_agent_configs()

        # Initialize database
        self.db = DatabaseManager(SQLite3Backend(self.config.database_path))
        self.db.connect()

        # Initialize actions
        self.actions = [
            ExploreAction(self.db, self.agents_config),
            SubmitQueryAction(self.db, self.agents_config),
            ExportAction(self.db, self.agents_config),
            StatsAction(self.db, self.agents_config),
            SettingsAction(self.db, self.agents_config),
        ]

    def print_briefing(self) -> None:
        """Print project briefing and current status."""
        print_header("NewsAgent - Interactive Pipeline Manager")

        try:
            stats = self.db.get_stats()

            print_section("Project Overview")
            print_item("Database", self.config.database_path)
            print_item("Total Queries", str(stats.get("total_queries", 0)))
            print_item("Total Responses", str(stats.get("total_responses", 0)))
            print_item("Total Items", str(stats.get("total_items", 0)))
            print_item("Configured Agents", str(len(self.agents_config)))
            print()

            # Show recent activity
            queries = self.db.list_queries(limit=3)
            if queries:
                print_section("Recent Queries (last 3)")
                for query in queries:
                    print_item(
                        f"  {query.query_id[:8]}",
                        f"{', '.join(query.query_fields[:2])} ({len(query.query_topics)} topics)",
                        indent=0
                    )
                print()

            # Show agent status
            print_section("Agent Status")
            for name, config in self.agents_config.items():
                status = "✓" if config.api_key else "✗"
                print_item(f"  {name}", f"{status} {'Ready' if config.api_key else 'Missing API Key'}", indent=0)
            print()

        except Exception as e:
            print_warning(f"Failed to load briefing: {e}")

    def show_main_menu(self) -> Optional[int]:
        """Show main menu and get user choice."""
        menu_items = [action.name for action in self.actions] + ["Exit"]

        choice = prompt_choice(menu_items, "Select an action")
        return choice

    def run(self) -> None:
        """Run the scheduler main loop."""
        print_header("NewsAgent - Agentic News Aggregation Pipeline")
        print_info("Interactive terminal-based pipeline manager")
        print()

        self.print_briefing()

        while True:
            choice = self.show_main_menu()

            if choice is None or choice == len(self.actions):  # Exit
                print_success("Goodbye!")
                break

            action = self.actions[choice]

            try:
                action.execute()
            except KeyboardInterrupt:
                print_warning("\nOperation cancelled by user")
            except Exception as e:
                print_warning(f"Error executing action: {e}")

            print()

    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self.db:
                self.db.disconnect()
        except Exception as e:
            print_warning(f"Error during cleanup: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
