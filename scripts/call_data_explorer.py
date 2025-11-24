#!/usr/bin/env python3
"""
Interactive Data Manager Explorer

A comprehensive script that guides users to explore data items saved and managed by DataManager.

Features:
- Browse statistics across all data models
- View latest items for each model type
- Explore cascade relationships (REQUEST→RESPONSE_ITEM)
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
        for model_type in [DataModelType.REQUEST, DataModelType.RESPONSE_ITEM]:
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
            'response_item': limit
        })

        for model_name in ['request_model', 'response_item']:
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
        print("  REQUEST → RESPONSE_ITEM")
        print()

        self._cascade_from_request()

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

        # Get associated response items
        result = self.dm.smart_query({'request_model': request_id})

        if 'error' in result['request_model']:
            error = result['request_model']
            print(f"\n❌ Error: {error['error']}")
            return

        items = result['request_model']
        print(f"\n✓ Found {len(items)} associated response item(s)")

        if not items:
            print("  No response items found for this request")
            return

        self.print_section(f"REQUEST {request_id[:8]}... → Associated RESPONSE_ITEMs")

        for idx, item in enumerate(items, 1):
            self._display_item(idx, item, 'response_item')

    def show_search_by_agent(self):
        """Search and filter by agent name"""
        self.print_section("🔍 Search by Agent")

        # Get all agents
        all_agents = set()
        for model_type in [DataModelType.REQUEST, DataModelType.RESPONSE_ITEM]:
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

        for model_type in [DataModelType.REQUEST, DataModelType.RESPONSE_ITEM]:
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
        for model_type in [DataModelType.REQUEST, DataModelType.RESPONSE_ITEM]:
            result = self.dm.retrieve(model_type, case_id)
            if result:
                self.print_section(f"Found in {model_type.value}")
                self._display_full_item(result, model_type.value)
                found = True

                # If REQUEST, show cascade
                if model_type == DataModelType.REQUEST:
                    explore = input("\nExplore associated response items? (y/n): ").strip().lower()
                    if explore == 'y':
                        self._cascade_from_request_direct(case_id)

        if not found:
            print(f"❌ Case ID '{case_id}' not found in any model")

    def _cascade_from_request_direct(self, request_id: str):
        """Direct cascade from REQUEST ID"""
        result = self.dm.smart_query({'request_model': request_id})

        if 'error' in result['request_model']:
            print(f"❌ Error: {result['request_model']['error']}")
            return

        items = result['request_model']
        print(f"\n✓ Found {len(items)} associated response item(s)")

        for idx, item in enumerate(items, 1):
            self._display_item(idx, item, 'response_item')

    def show_clear_data(self):
        """Clear data with options"""
        self.print_section("🗑️ Clear Data")

        print("\nWhat would you like to do?")
        clear_options = {
            "1": "Delete requests with response_type != 'real_call' (and associated RESPONSE_ITEMs)",
            "2": "Remove ALL instances from database (permanent!)",
            "3": "Cancel",
        }
        self.print_menu(clear_options)

        choice = input("Select option (1-3): ").strip()

        if choice == "1":
            self._clear_non_real_call_requests()
        elif choice == "2":
            self._clear_all_data()
        elif choice == "3":
            print("Clear operation cancelled.")
        else:
            print("Invalid choice.")

    def _clear_non_real_call_requests(self):
        """Delete requests with response_type != 'real_call' (and their response items)"""
        self.print_section("🗑️ Clearing cached-request records...")

        try:
            result = self.dm.smart_query({'request_model': 1000})
            requests = result.get('request_model', [])

            if not requests:
                print("No request records found.")
                return

            targets = [
                req for req in requests
                if req.get('response_type', 'real_call') != 'real_call'
            ]

            if not targets:
                print("No requests found with response_type != 'real_call'")
                return

            print(f"\nFound {len(targets)} request(s) with cached responses.")
            print("These requests and their associated response items will be deleted:")
            for idx, req in enumerate(targets[:10], 1):
                print(f"  {idx}. Request {req['request_id'][:8]}... (agent: {req['agent_name']}, type: {req.get('response_type')})")
            if len(targets) > 10:
                print(f"  ... and {len(targets) - 10} more")

            confirm = input("\nAre you sure? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("Operation cancelled.")
                return

            deleted = 0
            for req in targets:
                if self.dm.delete(DataModelType.REQUEST, req['request_id'], cascade=True):
                    deleted += 1

            print(f"\n✓ Operation completed successfully!")
            print(f"  Requests deleted: {deleted}")

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

    def show_export_data(self):
        """Export data to JSON file"""
        self.print_section("💾 Export Data")

        print("What to export?")
        export_options = {
            "1": "Statistics summary",
            "2": "All REQUEST records",
            "3": "All RESPONSE_ITEM records",
            "4": "All data (requests + response items)",
        }
        self.print_menu(export_options)

        choice = input("Select option (1-4): ").strip()

        export_data = {}

        if choice == "1":
            export_data = self.dm.smart_query()
            filename = "datamanager_stats.json"

        elif choice == "2":
            result = self.dm.smart_query({'request_model': 1000})
            export_data = {"request_model": result['request_model']}
            filename = "datamanager_requests.json"

        elif choice == "3":
            result = self.dm.smart_query({'response_item': 1000})
            export_data = {"response_item": result['response_item']}
            filename = "datamanager_items.json"

        elif choice == "4":
            result = self.dm.smart_query({
                'request_model': 1000,
                'response_item': 1000
            })
            export_data = {
                'request_model': result['request_model'],
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

        elif model_type == 'response_item':
            print(f"\n  [{idx}] ITEM {item['item_id'][:8]}...")
            print(f"      Title: {item['title'][:60]}")
            print(f"      Source: {item['source_name']}")
            print(f"      URL: {item['source_url'][:50]}")
            if item.get('request_id'):
                print(f"      Request: {item['request_id'][:8]}...")
            if item.get('relevance_score') is not None:
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
