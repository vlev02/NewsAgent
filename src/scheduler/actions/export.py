"""
Export action - Export search results to JSON or Markdown formats.
"""

import json
from datetime import datetime
from pathlib import Path
from src.scheduler.actions.base import Action
from src.scheduler.interactive import (
    print_section, print_success, print_error, print_info,
    prompt_choice, prompt_text
)


class ExportAction(Action):
    """Action to export search results in various formats."""

    @property
    def name(self) -> str:
        return "Export Results"

    @property
    def description(self) -> str:
        return "Export search results to JSON or Markdown format"

    def execute(self) -> bool:
        """Execute export action."""
        print_section("Export Results")

        # Ask what to export
        export_options = [
            "All items from database",
            "Items by source type",
            "Items from recent query",
            "Go back to main menu"
        ]

        choice = prompt_choice(export_options, "What would you like to export?")

        if choice is None or choice == 3:
            return True

        if choice == 0:
            self._export_all_items()
        elif choice == 1:
            self._export_by_source()
        elif choice == 2:
            self._export_by_query()

        return True

    def _export_all_items(self) -> None:
        """Export all items from database."""
        try:
            items = self.db.search_items(limit=10000)

            if not items:
                print_error("No items to export")
                return

            format_choice = prompt_choice(["JSON", "Markdown"], "Select export format")
            if format_choice is None:
                return

            output_file = self._get_output_filename(
                f"all_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "json" if format_choice == 0 else "md"
            )

            if format_choice == 0:
                self._export_json(items, output_file)
            else:
                self._export_markdown(items, output_file)

        except Exception as e:
            print_error(f"Export failed: {e}")

    def _export_by_source(self) -> None:
        """Export items grouped by source type."""
        try:
            items = self.db.search_items(limit=10000)

            if not items:
                print_error("No items to export")
                return

            # Get unique sources
            sources = list(set(item.source_type for item in items))

            source_choice = prompt_choice(sources, "Select source type")
            if source_choice is None:
                return

            selected_source = sources[source_choice]
            source_items = [item for item in items if item.source_type == selected_source]

            format_choice = prompt_choice(["JSON", "Markdown"], "Select export format")
            if format_choice is None:
                return

            output_file = self._get_output_filename(
                f"{selected_source.lower()}_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "json" if format_choice == 0 else "md"
            )

            if format_choice == 0:
                self._export_json(source_items, output_file)
            else:
                self._export_markdown(source_items, output_file)

        except Exception as e:
            print_error(f"Export failed: {e}")

    def _export_by_query(self) -> None:
        """Export items from a recent query."""
        try:
            queries = self.db.list_queries(limit=20)

            if not queries:
                print_error("No queries in database")
                return

            # Build query list for display
            query_labels = [
                f"{q.query_id[:8]} - {', '.join(q.query_fields[:2])} ({len(q.query_topics)} topics)"
                for q in queries
            ]

            query_choice = prompt_choice(query_labels, "Select query")
            if query_choice is None:
                return

            selected_query = queries[query_choice]

            # Get items for this query
            items = self.db.search_items(query_id=selected_query.query_id, limit=1000)

            if not items:
                print_error(f"No items found for query {selected_query.query_id[:8]}")
                return

            format_choice = prompt_choice(["JSON", "Markdown"], "Select export format")
            if format_choice is None:
                return

            output_file = self._get_output_filename(
                f"query_{selected_query.query_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "json" if format_choice == 0 else "md"
            )

            if format_choice == 0:
                self._export_json(items, output_file, selected_query)
            else:
                self._export_markdown(items, output_file, selected_query)

        except Exception as e:
            print_error(f"Export failed: {e}")

    def _export_json(self, items, output_file: str, query=None) -> None:
        """Export items to JSON format."""
        data = {
            "export_date": datetime.now().isoformat(),
            "item_count": len(items),
            "items": []
        }

        if query:
            data["query"] = {
                "query_id": query.query_id,
                "fields": query.query_fields,
                "topics": query.query_topics,
                "agents": query.source_agents,
                "time_range_days": getattr(query, 'days_back', 7)
            }

        for item in items:
            data["items"].append({
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "source_url": item.source_url,
                "source_name": item.source_name,
                "source_type": item.source_type,
                "timestamp": item.timestamp.isoformat(),
                "category": item.category,
                "relevance_score": item.relevance_score,
                "key_entities": item.key_entities
            })

        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print_success(f"Exported {len(items)} items to {output_file}")
            print_info(f"File size: {output_path.stat().st_size / 1024:.1f} KB")

        except Exception as e:
            print_error(f"Failed to write JSON file: {e}")

    def _export_markdown(self, items, output_file: str, query=None) -> None:
        """Export items to Markdown format."""
        md_lines = [
            "# Search Results Export",
            "",
            f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        if query:
            md_lines.extend([
                "## Query Information",
                "",
                f"- **Fields:** {', '.join(query.query_fields)}",
                f"- **Topics:** {', '.join(query.query_topics)}",
                f"- **Agents:** {', '.join(query.source_agents)}",
                f"- **Time Range:** {getattr(query, 'days_back', 7)} days",
                "",
            ])

        md_lines.extend([
            f"## Results ({len(items)} items)",
            "",
        ])

        for i, item in enumerate(items, 1):
            md_lines.extend([
                f"### {i}. {item.title}",
                "",
                f"**Source:** {item.source_name} ({item.source_type})",
                f"**Date:** {item.timestamp.strftime('%Y-%m-%d %H:%M')}",
                f"**URL:** [{item.source_url}]({item.source_url})",
                "",
            ])

            if item.category:
                md_lines.append(f"**Category:** {item.category}")

            if item.relevance_score:
                md_lines.append(f"**Relevance:** {item.relevance_score:.2f}")

            if item.key_entities:
                md_lines.append(f"**Entities:** {', '.join(item.key_entities)}")

            md_lines.extend([
                "",
                f"{item.content}",
                "",
                "---",
                "",
            ])

        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(md_lines))

            print_success(f"Exported {len(items)} items to {output_file}")
            print_info(f"File size: {output_path.stat().st_size / 1024:.1f} KB")

        except Exception as e:
            print_error(f"Failed to write Markdown file: {e}")

    def _get_output_filename(self, base_name: str, extension: str) -> str:
        """Get output filename from user or use default."""
        default_name = f"data/{base_name}.{extension}"
        print_info(f"Default output: {default_name}")

        custom = prompt_text("Custom filename (or press Enter for default)", allow_empty=True)
        return custom if custom else default_name
