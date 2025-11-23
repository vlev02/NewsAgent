#!/usr/bin/env python3
"""
Interactive Data Manager Explorer

A comprehensive script that guides users to explore data items saved and managed by DataManager.

Features:
- Browse statistics across all data models
- View latest items for each model type
- Explore cascade relationships (REQUEST→QUERY→RESPONSE_ITEM)
- Filter by agent name
- Search by case ID
- Export results to JSON
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Setup path
project_root = Path.cwd().parent if 'scripts' in str(Path.cwd()) else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data_manager import (
    get_data_manager,
    DataModelType,
    RequestModel,
    QueryModel,
)


class DataExplorer:
    """Interactive explorer for DataManager"""

    def __init__(self):
        self.dm = get_data_manager()
        self.current_selection = None

    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(text.center(80))
        print("=" * 80)

    def print_section(self, text: str):
        """Print formatted section"""
        print("\n" + "-" * 80)
        print(text)
        print("-" * 80)

    def print_menu(self, options: Dict[str, str]):
        """Print menu options"""
        for key, description in options.items():
            print(f"  {key}. {description}")
        print()

    def format_dict_preview(self, data: Dict[str, Any], max_keys: int = 5) -> str:
        """Format dict for preview display"""
        if not data:
            return "{}"
        keys = list(data.keys())[:max_keys]
        items = ", ".join(f"'{k}': ..." for k in keys)
        return "{" + items + "}"

    def format_timestamp(self, timestamp_str: Optional[str]) -> str:
        """Format timestamp for display"""
        if not timestamp_str:
            return "N/A"
        # Extract date and time part (YYYY-MM-DD HH:MM:SS)
        if 'T' in timestamp_str:
            # ISO format: 2025-11-23T19:18:53.123456 or similar
            date_time = timestamp_str.split('T')[1] if 'T' in timestamp_str else timestamp_str
            date_part = timestamp_str.split('T')[0]
            # Remove microseconds if present
            time_part = date_time.split('.')[0] if '.' in date_time else date_time
            return f"{date_part} {time_part}"
        return timestamp_str

    def show_overview(self):
        """Display overview statistics"""
        self.print_section("📊 DataManager Overview")

        stats = self.dm.smart_query()

        print(f"\nTotal Records:")
        total = 0
        for model_name, count in sorted(stats.items()):
            print(f"  • {model_name:20} : {count:6} records")
            total += count

        print(f"\n  {'Total':20} : {total:6} records")

        # Get agent statistics
        print(f"\nBreakdown by Model:")
        for model_type in [DataModelType.REQUEST, DataModelType.QUERY, DataModelType.RESPONSE_ITEM]:
            report = self.dm.explore(model_type)
            if report['by_agent']:
                print(f"\n  {model_type.value}:")
                for agent_name, count in sorted(report['by_agent'].items()):
                    print(f"    - {agent_name:20} : {count:4} records")

    def show_latest_items(self):
        """Display latest items for each model"""
        self.print_section("🕐 Latest Items")

        # Ask for number of items
        while True:
            try:
                limit = int(input("\nHow many latest items per model to display? (1-50, default=5): ").strip() or "5")
                if 1 <= limit <= 50:
                    break
                print("Please enter a number between 1 and 50")
            except ValueError:
                print("Invalid input. Please enter a number.")

        result = self.dm.smart_query({
            'request_model': limit,
            'query_model': limit,
            'response_item': limit
        })

        for model_name in ['request_model', 'query_model', 'response_item']:
            items = result[model_name]
            self.print_section(f"Latest {len(items)} {model_name} record(s)")

            if not items:
                print("  No records found")
                continue

            for idx, item in enumerate(items, 1):
                self._display_item(idx, item, model_name)

    def show_cascade_explorer(self):
        """Interactive cascade explorer"""
        self.print_section("🔗 Cascade Explorer")

        print("\nExplore relationships in the cascade chain:")
        print("  REQUEST → QUERY → RESPONSE_ITEM")
        print()

        model_choice = input("Start from which model? (request/query, default=request): ").strip().lower() or "request"

        if model_choice == "request":
            self._cascade_from_request()
        elif model_choice == "query":
            self._cascade_from_query()
        else:
            print("Invalid choice")

    def _cascade_from_request(self):
        """Cascade explorer starting from REQUEST"""
        print("\nEnter REQUEST ID to explore (or leave empty to view sample requests):")

        # Show sample requests
        report = self.dm.explore(DataModelType.REQUEST)
        sample_ids = report['sample_keys']

        if sample_ids:
            print(f"\nSample REQUEST IDs (use these to explore):")
            for idx, rid in enumerate(sample_ids[:5], 1):
                print(f"  {idx}. {rid}")

        request_id = input("\nEnter REQUEST ID: ").strip()

        if not request_id:
            print("No ID provided")
            return

        # Get associated queries
        result = self.dm.smart_query({'request_model': request_id})

        if 'error' in result['request_model']:
            error = result['request_model']
            print(f"\n❌ Error: {error['error']}")
            return

        queries = result['request_model']
        print(f"\n✓ Found {len(queries)} associated query(ies)")

        if not queries:
            print("  No queries found for this request")
            return

        self.print_section(f"REQUEST {request_id[:8]}... → Associated QUERYs")

        for idx, query in enumerate(queries, 1):
            self._display_item(idx, query, 'query_model')

            # Ask to explore this query
            explore = input(f"\n  Explore RESPONSE_ITEMs for query {idx}? (y/n): ").strip().lower()
            if explore == 'y':
                self._cascade_query_to_items(query['query_id'])

    def _cascade_from_query(self):
        """Cascade explorer starting from QUERY"""
        print("\nEnter QUERY ID to explore (or leave empty to view sample queries):")

        # Show sample queries
        report = self.dm.explore(DataModelType.QUERY)
        sample_ids = report['sample_keys']

        if sample_ids:
            print(f"\nSample QUERY IDs (use these to explore):")
            for idx, qid in enumerate(sample_ids[:5], 1):
                print(f"  {idx}. {qid}")

        query_id = input("\nEnter QUERY ID: ").strip()

        if not query_id:
            print("No ID provided")
            return

        self._cascade_query_to_items(query_id)

    def _cascade_query_to_items(self, query_id: str):
        """Helper to cascade from QUERY to RESPONSE_ITEMs"""
        result = self.dm.smart_query({'query_model': query_id})

        if 'error' in result['query_model']:
            error = result['query_model']
            print(f"\n❌ Error: {error['error']}")
            return

        items = result['query_model']
        print(f"\n✓ Found {len(items)} associated response item(s)")

        if not items:
            print("  No response items found for this query")
            return

        self.print_section(f"QUERY {query_id[:8]}... → Associated RESPONSE_ITEMs")

        for idx, item in enumerate(items, 1):
            self._display_item(idx, item, 'response_item')

    def show_search_by_agent(self):
        """Search and filter by agent name"""
        self.print_section("🔍 Search by Agent")

        # Get all agents
        all_agents = set()
        for model_type in [DataModelType.REQUEST, DataModelType.QUERY, DataModelType.RESPONSE_ITEM]:
            report = self.dm.explore(model_type)
            all_agents.update(report['by_agent'].keys())

        if not all_agents:
            print("No agents found in database")
            return

        print("\nAvailable agents:")
        agents_list = sorted(all_agents)
        for idx, agent in enumerate(agents_list, 1):
            print(f"  {idx}. {agent}")

        try:
            choice = int(input("\nSelect agent by number (or 0 to cancel): ").strip() or "0")
            if choice == 0 or choice < 1 or choice > len(agents_list):
                return
            agent_name = agents_list[choice - 1]
        except ValueError:
            print("Invalid input")
            return

        # Show statistics for this agent
        self.print_section(f"📊 Statistics for Agent: {agent_name}")

        for model_type in [DataModelType.REQUEST, DataModelType.QUERY, DataModelType.RESPONSE_ITEM]:
            report = self.dm.explore(model_type)
            count = report['by_agent'].get(agent_name, 0)
            print(f"  {model_type.value:20} : {count:4} records")

    def show_search_by_id(self):
        """Search by case ID"""
        self.print_section("🔍 Search by Case ID")

        case_id = input("Enter case ID to search: ").strip()

        if not case_id:
            print("No ID provided")
            return

        found = False

        # Try to find in each model
        for model_type in [DataModelType.REQUEST, DataModelType.QUERY, DataModelType.RESPONSE_ITEM]:
            result = self.dm.retrieve(model_type, case_id)
            if result:
                self.print_section(f"Found in {model_type.value}")
                self._display_full_item(result, model_type.value)
                found = True

                # If REQUEST or QUERY, show cascade
                if model_type == DataModelType.REQUEST:
                    explore = input("\nExplore associated queries? (y/n): ").strip().lower()
                    if explore == 'y':
                        self._cascade_from_request_direct(case_id)

                elif model_type == DataModelType.QUERY:
                    explore = input("\nExplore associated response items? (y/n): ").strip().lower()
                    if explore == 'y':
                        self._cascade_query_to_items(case_id)

        if not found:
            print(f"❌ Case ID '{case_id}' not found in any model")

    def _cascade_from_request_direct(self, request_id: str):
        """Direct cascade from REQUEST ID"""
        result = self.dm.smart_query({'request_model': request_id})

        if 'error' in result['request_model']:
            print(f"❌ Error: {result['request_model']['error']}")
            return

        queries = result['request_model']
        print(f"\n✓ Found {len(queries)} associated query(ies)")

        for idx, query in enumerate(queries, 1):
            self._display_item(idx, query, 'query_model')

    def show_clear_data(self):
        """Clear data with options"""
        self.print_section("🗑️ Clear Data")

        print("\nWhat would you like to do?")
        clear_options = {
            "1": "Clear query_models with response_type != 'real_call' (and associated RESPONSE_ITEMs)",
            "2": "Remove ALL instances from database (permanent!)",
            "3": "Cancel",
        }
        self.print_menu(clear_options)

        choice = input("Select option (1-3): ").strip()

        if choice == "1":
            self._clear_non_real_call_queries()
        elif choice == "2":
            self._clear_all_data()
        elif choice == "3":
            print("Clear operation cancelled.")
        else:
            print("Invalid choice.")

    def _clear_non_real_call_queries(self):
        """Clear query_models with response_type != 'real_call' and their associated response items"""
        self.print_section("🗑️ Clearing non-real-call queries...")

        try:
            # Get all query_models
            report = self.dm.explore(DataModelType.QUERY)
            sample_keys = report['sample_keys']

            if not sample_keys:
                print("No query_models found in database.")
                return

            # Get all queries (up to 1000)
            result = self.dm.smart_query({'query_model': 1000})
            all_queries = result.get('query_model', [])

            if not all_queries:
                print("No query_models found in database.")
                return

            # Filter queries by response_type
            queries_to_delete = []
            for query in all_queries:
                # Get the associated request to check response_type
                request_id = query.get('request_id')
                if request_id:
                    request = self.dm.retrieve(DataModelType.REQUEST, request_id)
                    if request:
                        response_type = request.get('response_type', 'real_call')
                        if response_type != 'real_call':
                            queries_to_delete.append(query)

            if not queries_to_delete:
                print("No queries found with response_type != 'real_call'")
                return

            print(f"\nFound {len(queries_to_delete)} query(ies) with response_type != 'real_call'")
            print("\nThese queries and their associated response items will be deleted:")
            for idx, query in enumerate(queries_to_delete[:10], 1):
                print(f"  {idx}. Query {query['query_id'][:8]}... (agent: {query['agent_name']})")
            if len(queries_to_delete) > 10:
                print(f"  ... and {len(queries_to_delete) - 10} more")

            confirm = input("\nAre you sure? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("Operation cancelled.")
                return

            # Delete the queries using DataManager
            deleted_count = self.dm.delete_queries_by_response_type('cached_response', cascade=True)

            print(f"\n✓ Operation completed successfully!")
            print(f"  Total records deleted: {deleted_count}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    def _clear_all_data(self):
        """Clear all instances from database (permanent!)"""
        self.print_section("⚠️ DANGER: Remove ALL Data")

        print("\n" + "!" * 80)
        print("WARNING: This will PERMANENTLY delete ALL data from the database!")
        print("!" * 80)

        # Double confirmation
        confirm1 = input("\nType 'DELETE ALL' to confirm: ").strip()
        if confirm1 != 'DELETE ALL':
            print("Operation cancelled.")
            return

        confirm2 = input("Type 'YES, DELETE EVERYTHING' to confirm again: ").strip()
        if confirm2 != 'YES, DELETE EVERYTHING':
            print("Operation cancelled.")
            return

        try:
            # Get stats before deletion
            stats = self.dm.smart_query()
            total_records = sum(stats.values())

            print(f"\n✓ Database overview before deletion:")
            for model_name, count in sorted(stats.items()):
                print(f"  • {model_name:20} : {count:6} records")
            print(f"  {'Total':20} : {total_records:6} records")

            # Perform the deletion
            print("\n⏳ Deleting all records...")
            deleted_count = self.dm.delete_all()

            print(f"\n✓ Deletion completed successfully!")
            print(f"  Total records deleted: {deleted_count}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    def _enrich_queries_with_response_type(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich query_models with response_type from associated requests

        Args:
            queries: List of query_model dictionaries

        Returns:
            List of query_models with response_type field added
        """
        enriched = []
        for query in queries:
            query_copy = query.copy()
            request_id = query.get('request_id')
            if request_id:
                request = self.dm.retrieve(DataModelType.REQUEST, request_id)
                if request:
                    query_copy['response_type'] = request.get('response_type', 'N/A')
                else:
                    query_copy['response_type'] = 'N/A'
            else:
                query_copy['response_type'] = 'N/A'
            enriched.append(query_copy)
        return enriched

    def show_export_data(self):
        """Export data to JSON file"""
        self.print_section("💾 Export Data")

        print("What to export?")
        export_options = {
            "1": "Statistics summary",
            "2": "All REQUEST records",
            "3": "All QUERY records (with response_type)",
            "4": "All RESPONSE_ITEM records",
            "5": "All data (full export with response_type)",
        }
        self.print_menu(export_options)

        choice = input("Select option (1-5): ").strip()

        export_data = {}

        if choice == "1":
            export_data = self.dm.smart_query()
            filename = "datamanager_stats.json"

        elif choice == "2":
            result = self.dm.smart_query({'request_model': 1000})
            export_data = {"request_model": result['request_model']}
            filename = "datamanager_requests.json"

        elif choice == "3":
            result = self.dm.smart_query({'query_model': 1000})
            queries = result['query_model']
            # Enrich queries with response_type from associated requests
            enriched_queries = self._enrich_queries_with_response_type(queries)
            export_data = {"query_model": enriched_queries}
            filename = "datamanager_queries.json"

        elif choice == "4":
            result = self.dm.smart_query({'response_item': 1000})
            export_data = {"response_item": result['response_item']}
            filename = "datamanager_items.json"

        elif choice == "5":
            result = self.dm.smart_query({
                'request_model': 1000,
                'query_model': 1000,
                'response_item': 1000
            })
            # Enrich queries with response_type from associated requests
            enriched_queries = self._enrich_queries_with_response_type(result['query_model'])
            export_data = {
                'request_model': result['request_model'],
                'query_model': enriched_queries,
                'response_item': result['response_item']
            }
            filename = "datamanager_full.json"

        else:
            print("Invalid choice")
            return

        # Save to file
        output_path = project_root / filename
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Data exported to: {output_path}")
            print(f"  File size: {output_path.stat().st_size / 1024:.2f} KB")
        except Exception as e:
            print(f"\n❌ Export failed: {e}")

    def _display_item(self, idx: int, item: Dict[str, Any], model_type: str):
        """Display single item in list format"""
        if model_type == 'request_model':
            print(f"\n  [{idx}] REQUEST {item['request_id'][:8]}...")
            print(f"      Agent: {item['agent_name']}")
            print(f"      Status: {item['http_status']}")
            print(f"      Request Time: {self.format_timestamp(item['timestamp'])}")
            if item.get('created_at'):
                print(f"      Recorded At: {self.format_timestamp(item['created_at'])}")
            print(f"      Execution: {item['execution_time_ms']}ms")

        elif model_type == 'query_model':
            print(f"\n  [{idx}] QUERY {item['query_id'][:8]}...")
            print(f"      Agent: {item['agent_name']}")
            print(f"      Keywords: {item['query_keywords']}")
            print(f"      Max results: {item['max_results']}")
            print(f"      Time: {self.format_timestamp(item['timestamp'])}")
            # Get associated request to show response_type
            request_id = item.get('request_id')
            if request_id:
                request = self.dm.retrieve(DataModelType.REQUEST, request_id)
                if request:
                    response_type = request.get('response_type', 'N/A')
                    print(f"      Response Type: {response_type}")

        elif model_type == 'response_item':
            print(f"\n  [{idx}] ITEM {item['item_id'][:8]}...")
            print(f"      Title: {item['title'][:60]}")
            print(f"      Source: {item['source_name']}")
            print(f"      URL: {item['source_url'][:50]}")
            if item['relevance_score']:
                print(f"      Relevance: {item['relevance_score']:.2f}")

    def _display_full_item(self, item: Dict[str, Any], model_type: str):
        """Display full item details"""
        print(json.dumps(item, indent=2, ensure_ascii=False))

    def run(self):
        """Main interactive loop"""
        self.print_header("📚 DataManager Explorer")

        while True:
            print("\n" + "=" * 80)
            print("Main Menu".center(80))
            print("=" * 80)

            menu = {
                "1": "View Overview Statistics",
                "2": "View Latest Items",
                "3": "Explore Cascade Relationships",
                "4": "Search by Agent",
                "5": "Search by Case ID",
                "6": "Export Data to JSON",
                "7": "Clear Data",
                "8": "Exit",
            }

            self.print_menu(menu)

            choice = input("Select option (1-8): ").strip()

            try:
                if choice == "1":
                    self.show_overview()

                elif choice == "2":
                    self.show_latest_items()

                elif choice == "3":
                    self.show_cascade_explorer()

                elif choice == "4":
                    self.show_search_by_agent()

                elif choice == "5":
                    self.show_search_by_id()

                elif choice == "6":
                    self.show_export_data()

                elif choice == "7":
                    self.show_clear_data()

                elif choice == "8":
                    print("\n✓ Exiting explorer... Goodbye!\n")
                    break

                else:
                    print("Invalid choice. Please select 1-8")

            except KeyboardInterrupt:
                print("\n\n✓ Explorer interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()


def main():
    """Entry point"""
    explorer = DataExplorer()
    explorer.run()


if __name__ == "__main__":
    main()
