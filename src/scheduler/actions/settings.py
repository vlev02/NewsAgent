"""
Settings action - View and manage scheduler settings.
"""

from src.scheduler.actions.base import Action
from src.scheduler.interactive import (
    print_section, print_item, print_info, print_warning,
    prompt_choice
)


class SettingsAction(Action):
    """Action to view and manage settings."""

    @property
    def name(self) -> str:
        return "Settings"

    @property
    def description(self) -> str:
        return "View and manage scheduler settings"

    def execute(self) -> bool:
        """Execute settings action."""
        while True:
            print_section("Settings")

            # Show agent configurations
            print_item("Configured Agents", str(len(self.agents_config)))
            print()

            for agent_name, config in self.agents_config.items():
                status = "✓" if config.api_key else "✗"
                print_item(f"  {agent_name}", f"{status} API Key configured", indent=1)

                if hasattr(config, 'rate_limit_per_minute') and config.rate_limit_per_minute:
                    print_item(
                        f"    Rate Limit",
                        f"{config.rate_limit_per_minute} requests/minute",
                        indent=2
                    )

            print()

            # Show menu
            options = [
                "View agent capabilities",
                "View database configuration",
                "Go back to main menu"
            ]

            choice = prompt_choice(options, "Settings")

            if choice is None or choice == 2:
                return True

            if choice == 0:
                self._show_agent_capabilities()
            elif choice == 1:
                self._show_database_config()

    def _show_agent_capabilities(self) -> None:
        """Show agent capabilities."""
        print_section("Agent Capabilities")

        for agent_name, config in self.agents_config.items():
            print_item(agent_name, "", indent=0)
            print_item("Endpoint", config.endpoint or "N/A", indent=1)
            print_item("Auth Method", config.auth_method or "N/A", indent=1)

            if hasattr(config, 'supports_time_filter') and config.supports_time_filter:
                print_item("Time Filter", "✓ Supported", indent=1)
            if hasattr(config, 'supports_ai_summary') and config.supports_ai_summary:
                print_item("AI Summary", "✓ Supported", indent=1)
            if hasattr(config, 'supports_streaming') and config.supports_streaming:
                print_item("Streaming", "✓ Supported", indent=1)

            print()

    def _show_database_config(self) -> None:
        """Show database configuration."""
        print_section("Database Configuration")

        try:
            stats = self.db.get_stats()
            print_item("Total Queries", str(stats.get("total_queries", 0)))
            print_item("Total Responses", str(stats.get("total_responses", 0)))
            print_item("Total Items", str(stats.get("total_items", 0)))
            print_info("Database is SQLite3 (see newsagent.db)")
        except Exception as e:
            print_warning(f"Failed to get database info: {e}")

        print()
