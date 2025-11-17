"""
Submit Query action - Build and submit queries step-by-step with validation.
"""

from typing import Optional, List, Dict, Any
from src.dataclasses import QueryRequest
from src.dataclasses.config import AgentConfig
from src.scheduler.actions.base import Action
from src.scheduler.interactive import (
    print_section, print_item, print_success, print_error, print_warning, print_info,
    prompt_choice, prompt_text, prompt_list, prompt_confirm, print_table
)
from src.utils import TIME_FILTER_MAPPING, get_time_description, build_query_string
from src.agents.bocha import BochaAgent
from src.pipeline import SearchPipeline


class SubmitQueryAction(Action):
    """Action to submit a query step-by-step with validation."""

    @property
    def name(self) -> str:
        return "Submit Query"

    @property
    def description(self) -> str:
        return "Build and submit a new search query with step-by-step validation"

    def execute(self) -> bool:
        """Execute submit query action."""
        print_section("Submit New Query")

        # Step 1: Select agents
        agents = self._select_agents()
        if not agents:
            print_warning("Query cancelled")
            return False

        # Step 2: Enter query fields (domains)
        fields = self._get_query_fields()
        if fields is None:
            print_warning("Query cancelled")
            return False

        # Step 3: Enter query topics
        topics = self._get_query_topics()
        if topics is None:
            print_warning("Query cancelled")
            return False

        # Step 4: Select time filter
        days_back = self._select_time_filter()
        if days_back is None:
            print_warning("Query cancelled")
            return False

        # Step 5: Set result limits
        max_results = self._set_result_limits()
        if max_results is None:
            print_warning("Query cancelled")
            return False

        # Step 6: Review and preview
        query = self._build_query(fields, topics, agents, days_back, max_results)
        if not self._review_query(query):
            print_warning("Query cancelled")
            return False

        # Step 7: Preview templates for each agent
        if not self._preview_templates(query):
            print_warning("Query cancelled")
            return False

        # Step 8: Check resources and execute
        if not self._check_resources_and_execute(query, agents):
            return False

        return True

    def _select_agents(self) -> Optional[List[str]]:
        """Select which agents to use."""
        print_section("Step 1: Select Agents")

        agent_names = list(self.agents_config.keys())
        print_info(f"Available agents: {', '.join(agent_names)}")
        print()

        # Show agent capabilities
        for name in agent_names:
            config = self.agents_config[name]
            print_item(name, f"Rate limit: {config.rate_limit_per_minute or 'unlimited'} req/min", indent=1)

        selected = []
        while True:
            choice = prompt_choice(agent_names + ["Done"], "Select agents (one at a time)")

            if choice is None:
                return None
            if choice == len(agent_names):  # Done
                if not selected:
                    print_warning("Select at least one agent")
                    continue
                return selected
            if agent_names[choice] not in selected:
                selected.append(agent_names[choice])
                print_success(f"Selected: {', '.join(selected)}")

    def _get_query_fields(self) -> Optional[List[str]]:
        """Get query fields (domains)."""
        print_section("Step 2: Enter Query Fields (Domains)")
        print_info("Separate multiple fields with commas (e.g., '自动驾驶, 具身智能, 大模型')")

        fields = prompt_list("Enter query fields")
        if fields is None:
            return None

        print_success(f"Query fields: {', '.join(fields)}")
        return fields

    def _get_query_topics(self) -> Optional[List[str]]:
        """Get query topics."""
        print_section("Step 3: Enter Query Topics")
        print_info("Separate multiple topics with commas (e.g., '特斯拉FSD, 人形机器人')")

        topics = prompt_list("Enter query topics")
        if topics is None:
            return None

        print_success(f"Query topics: {', '.join(topics)}")
        return topics

    def _select_time_filter(self) -> Optional[int]:
        """Select time filter."""
        print_section("Step 4: Select Time Filter")

        time_options = [
            ("1 day", 1),
            ("7 days (1 week)", 7),
            ("30 days (1 month)", 30),
            ("365 days (1 year)", 365),
        ]

        time_labels = [f"{label}" for label, _ in time_options]
        choice = prompt_choice(time_labels, "Select time range")

        if choice is None:
            return None

        days = time_options[choice][1]
        time_desc = get_time_description(days)
        print_success(f"Time filter: {days} days ({time_desc})")
        return days

    def _set_result_limits(self) -> Optional[int]:
        """Set result limit."""
        print_section("Step 5: Set Result Limits")
        print_info("Maximum number of results to retrieve per agent")

        limit_options = ["5 results", "10 results", "20 results", "50 results", "100 results", "Custom"]

        choice = prompt_choice(limit_options, "Select result limit")

        if choice is None:
            return None

        if choice < 5:
            limit = int(limit_options[choice].split()[0])
        else:
            custom = prompt_text("Enter custom limit", validator=lambda x: x.isdigit())
            if custom is None:
                return None
            limit = int(custom)

        print_success(f"Result limit: {limit} per agent")
        return limit

    def _build_query(self, fields: List[str], topics: List[str], agents: List[str],
                     days_back: int, max_results: int) -> QueryRequest:
        """Build QueryRequest object."""
        return QueryRequest(
            query_fields=fields,
            query_topics=topics,
            source_agents=agents,
            days_back=days_back,
            max_results=max_results,
            include_ai_summary=True,
            exclude_duplicates=True,
            language="zh"
        )

    def _review_query(self, query: QueryRequest) -> bool:
        """Review query before proceeding."""
        print_section("Step 6: Review Query")

        print_item("Query ID", query.query_id[:8])
        print_item("Fields", ", ".join(query.query_fields))
        print_item("Topics", ", ".join(query.query_topics))
        print_item("Agents", ", ".join(query.source_agents))
        print_item("Time Range", f"{query.days_back} days")
        print_item("Max Results", str(query.max_results))
        print_item("Language", query.language)
        print()

        return prompt_confirm("Proceed with this query")

    def _preview_templates(self, query: QueryRequest) -> bool:
        """Preview Jinja2 templates for each agent."""
        print_section("Step 7: Preview Agent Prompts")

        query_string = build_query_string(query.query_fields, query.query_topics)
        time_desc = get_time_description(query.days_back)

        for agent_name in query.source_agents:
            config = self.agents_config[agent_name]
            print_item(agent_name, "Prompt preview", indent=0)

            # Show query string
            print(f"\n  Query String: {query_string}")
            print(f"  Time Description: {time_desc}")
            print(f"  Days Back: {query.days_back}")

            # Show API-specific time filter
            api_time_filter = TIME_FILTER_MAPPING.get(agent_name, {}).get(query.days_back)
            if api_time_filter:
                print(f"  API Time Filter ({agent_name}): {api_time_filter}")

            # Show template name if available
            if hasattr(config, 'prompt_template'):
                print(f"  Template: {config.prompt_template}")

            print()

        return prompt_confirm("Proceed with these prompts")

    def _check_resources_and_execute(self, query: QueryRequest, agents: List[str]) -> bool:
        """Check resources and execute query."""
        print_section("Step 8: Check Resources & Execute")

        # Check agent configurations
        for agent_name in agents:
            config = self.agents_config[agent_name]
            print_item(agent_name, "Configuration valid", indent=1)

            if not config.api_key:
                print_warning(f"  API key not set for {agent_name}")

        print()

        # Ask for confirmation before executing
        if not prompt_confirm("Execute query"):
            return False

        # Execute with BOCHA as example
        try:
            print("\nExecuting query...")

            # Currently only BOCHA is implemented, so execute with available agents
            available_agents = {name: BochaAgent(self.agents_config[name])
                               for name in agents if name == "BOCHA"}

            if not available_agents:
                print_warning("No fully implemented agents selected. (Only BOCHA is currently implemented)")
                print_info("Other agents (XUNFEI, HUNYUAN, QIANFAN, META, TWITTER) are planned")
                return False

            # Create pipeline and execute
            pipeline = SearchPipeline(available_agents, self.db)
            responses = pipeline.execute_query(query)

            # Report results
            print()
            print_success(f"Query executed successfully!")

            total_items = sum(r.items_count for r in responses)
            print_item("Total Items Retrieved", str(total_items))
            print_item("Responses", str(len(responses)))

            for response in responses:
                status_emoji = "✓" if response.success else "✗"
                print_item(f"  {response.agent_name}", f"{status_emoji} {response.items_count} items ({response.execution_time_ms}ms)", indent=1)

            # Show sample results
            all_items = pipeline.aggregate_results(responses)
            if all_items:
                print_section("Sample Results (first 3)")
                for item in all_items[:3]:
                    print(f"  • {item.title}")
                    print(f"    {item.source_name} - {item.timestamp.strftime('%Y-%m-%d %H:%M')}")

            return True

        except Exception as e:
            print_error(f"Query execution failed: {e}")
            return False
