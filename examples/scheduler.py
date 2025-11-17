#!/usr/bin/env python3
"""
NewsAgent Scheduler - Interactive terminal-based pipeline manager.

Usage:
    python -m examples.scheduler [--env .env] [--db newsagent.db] [--show-env]

This script launches an interactive CLI for:
- Submitting new search queries with step-by-step validation
- Exploring recent research and query history
- Exporting results to JSON or Markdown
- Viewing database statistics
- Managing settings and agent configurations

Environment Setup:
    The scheduler loads configuration from .env file in the project root.
    Copy .env.example to .env and fill in your API keys:
        cp .env.example .env
        # Edit .env with your API keys
"""

import sys
import argparse

from src.scheduler import Scheduler
from src.scheduler.scheduler_settings import initialize_scheduler_settings
from src.scheduler.interactive import print_header, print_info, print_error


def main():
    """Main entry point for the scheduler."""
    parser = argparse.ArgumentParser(
        description="NewsAgent Interactive Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m examples.scheduler                    # Run with .env
  python -m examples.scheduler --env .env.local   # Custom env file
  python -m examples.scheduler --show-env         # Show settings without running
  python -m examples.scheduler --db news_prod.db  # Custom database
        """
    )

    parser.add_argument(
        "--env",
        type=str,
        default=".env",
        help="Path to .env file (default: .env)"
    )

    parser.add_argument(
        "--db",
        type=str,
        help="Path to database file (overrides DATABASE_PATH from .env)"
    )

    parser.add_argument(
        "--show-env",
        action="store_true",
        help="Display environment and configuration status without running scheduler"
    )

    parser.add_argument(
        "--show-env-vars",
        action="store_true",
        help="Display detailed environment variable status"
    )

    args = parser.parse_args()

    try:
        # Initialize scheduler settings from .env file
        settings = initialize_scheduler_settings(args.env)

        if not settings:
            print_error("Failed to initialize scheduler settings")
            sys.exit(1)

        # Override database path if provided
        if args.db:
            settings.env_vars.database_path = args.db

        # Show environment status if requested
        if args.show_env:
            print_header("NewsAgent Scheduler - Configuration Status")
            settings.print_summary()
            sys.exit(0)

        if args.show_env_vars:
            print_header("NewsAgent Scheduler - Environment Variables")
            settings.print_env_status()
            sys.exit(0)

        # Run full initialization report
        print_header("NewsAgent Scheduler - Initialization")
        if not settings.full_initialization_report():
            print_error("\nInitialization failed. Please check your configuration.")
            sys.exit(1)

        print_info("\nLaunching interactive scheduler...\n")

        # Create and run scheduler with settings
        with Scheduler(settings=settings) as scheduler:
            scheduler.run()

    except KeyboardInterrupt:
        print("\nScheduler interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
