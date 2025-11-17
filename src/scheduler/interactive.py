"""
Interactive utilities for terminal-based user input and output.
"""

from typing import List, Optional, Any, Callable
import sys


# ANSI Color codes
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str, width: int = 70) -> None:
    """Print a formatted header."""
    print("\n" + "=" * width)
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(width)}{Colors.ENDC}")
    print("=" * width + "\n")


def print_section(text: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}→ {text}{Colors.ENDC}")
    print("-" * 60)


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")


def print_item(label: str, value: Any, indent: int = 0) -> None:
    """Print a labeled item."""
    prefix = "  " * indent
    print(f"{prefix}{Colors.BOLD}{label}:{Colors.ENDC} {value}")


def prompt_choice(options: List[str], prompt_text: str = "Select an option") -> Optional[int]:
    """
    Prompt user to select from a list of options.

    Args:
        options: List of option strings
        prompt_text: Prompt text to display

    Returns:
        Index of selected option (0-based) or None if cancelled
    """
    print(f"\n{Colors.BOLD}{prompt_text}:{Colors.ENDC}")
    for i, option in enumerate(options, 1):
        print(f"  {Colors.CYAN}{i}{Colors.ENDC}. {option}")
    print(f"  {Colors.CYAN}0{Colors.ENDC}. {Colors.YELLOW}Cancel{Colors.ENDC}")

    while True:
        try:
            choice = input(f"\n{Colors.BOLD}Enter choice (0-{len(options)}): {Colors.ENDC}").strip()
            choice_num = int(choice)
            if choice_num == 0:
                return None
            if 1 <= choice_num <= len(options):
                return choice_num - 1
            print_error(f"Please enter a number between 0 and {len(options)}")
        except ValueError:
            print_error("Invalid input. Please enter a number.")


def prompt_text(prompt_text: str, allow_empty: bool = False,
                validator: Optional[Callable[[str], bool]] = None) -> Optional[str]:
    """
    Prompt user for text input.

    Args:
        prompt_text: Prompt text to display
        allow_empty: Allow empty input
        validator: Optional validation function that returns True if valid

    Returns:
        User input or None if cancelled
    """
    while True:
        try:
            user_input = input(f"{Colors.BOLD}{prompt_text}: {Colors.ENDC}").strip()

            if not user_input and not allow_empty:
                print_warning("Input cannot be empty")
                continue

            if user_input and validator and not validator(user_input):
                print_error("Invalid input format")
                continue

            return user_input if user_input else None
        except KeyboardInterrupt:
            print_warning("\nOperation cancelled")
            return None


def prompt_list(prompt_text: str, separator: str = ",",
                validator: Optional[Callable[[str], bool]] = None) -> Optional[List[str]]:
    """
    Prompt user for comma-separated list input.

    Args:
        prompt_text: Prompt text to display
        separator: Separator character (default: comma)
        validator: Optional validation function for each item

    Returns:
        List of items or None if cancelled
    """
    while True:
        try:
            user_input = input(f"{Colors.BOLD}{prompt_text}: {Colors.ENDC}").strip()

            if not user_input:
                print_warning("Input cannot be empty")
                continue

            items = [item.strip() for item in user_input.split(separator) if item.strip()]

            if validator and not all(validator(item) for item in items):
                print_error("One or more items are invalid")
                continue

            return items
        except KeyboardInterrupt:
            print_warning("\nOperation cancelled")
            return None


def prompt_confirm(prompt_text: str = "Continue") -> bool:
    """
    Prompt user for yes/no confirmation.

    Args:
        prompt_text: Prompt text to display

    Returns:
        True if user confirms, False otherwise
    """
    while True:
        response = input(f"\n{Colors.BOLD}{prompt_text}? (y/n): {Colors.ENDC}").strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print_error("Please enter 'y' or 'n'")


def print_table(headers: List[str], rows: List[List[Any]], col_widths: Optional[List[int]] = None) -> None:
    """
    Print a formatted table.

    Args:
        headers: List of column headers
        rows: List of rows, each row is a list of values
        col_widths: Optional list of column widths
    """
    if not col_widths:
        col_widths = [max(len(str(h)), max(len(str(row[i])) for row in rows)) if rows else len(str(h))
                      for i, h in enumerate(headers)]

    # Print header
    header_line = " | ".join(f"{h:{w}}" for h, w in zip(headers, col_widths))
    print(f"\n{Colors.BOLD}{header_line}{Colors.ENDC}")
    print("-" * len(header_line))

    # Print rows
    for row in rows:
        print(" | ".join(f"{str(v):{w}}" for v, w in zip(row, col_widths)))


def clear_screen() -> None:
    """Clear terminal screen."""
    print("\033c", end="")


def pause(message: str = "Press Enter to continue...") -> None:
    """Pause and wait for user to press Enter."""
    input(f"\n{Colors.BOLD}{message}{Colors.ENDC}")
