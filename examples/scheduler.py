#!/usr/bin/env python3
"""
NewsAgent Scheduler - Interactive terminal-based pipeline manager.

Usage:
    python -m examples.scheduler [--config config.json] [--db newsagent.db]

This script launches an interactive CLI for:
- Submitting new search queries with step-by-step validation
- Exploring recent research and query history
- Exporting results to JSON or Markdown
- Viewing database statistics
- Managing settings and agent configurations
"""

import sys
import argparse
from pathlib import Path

from src.scheduler import Scheduler
from src.scheduler.config import SchedulerConfig, get_agent_configs


def main():
    """Main entry point for the scheduler."""
    parser = argparse.ArgumentParser(
        description="NewsAgent Interactive Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m examples.scheduler
  python -m examples.scheduler --db news_custom.db
  python -m examples.scheduler --config scheduler_config.json
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to scheduler configuration file (JSON)"
    )

    parser.add_argument(
        "--db",
        type=str,
        help="Path to database file (default: newsagent.db)"
    )

    args = parser.parse_args()

    try:
        # Load configuration
        if args.config and Path(args.config).exists():
            config = SchedulerConfig.from_file(args.config)
        else:
            config = SchedulerConfig.from_env()

        # Override database path if provided
        if args.db:
            config.database_path = args.db

        # Load agent configurations
        agents_config = get_agent_configs()

        # Create and run scheduler
        with Scheduler(config, agents_config) as scheduler:
            scheduler.run()

    except KeyboardInterrupt:
        print("\nScheduler interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
