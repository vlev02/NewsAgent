"""
Simple field info collector from Pydantic schemas

Extracts field information directly from Pydantic BaseModel without extra configuration.
Uses only what Pydantic provides: type, default, description, constraints.
"""

import sys
import json
from typing import Dict, Any, Optional, get_args, get_origin
from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo


class FieldCollector:
    """Collects and organizes field information from Pydantic schemas"""

    @staticmethod
    def get_field_info(model: type[BaseModel], field_name: str) -> Dict[str, Any]:
        """
        Get field information directly from Pydantic model.

        Args:
            model: Pydantic BaseModel class
            field_name: Name of the field

        Returns:
            Dictionary with field info (type, default, description, constraints)
        """
        field_info = model.model_fields[field_name]

        info = {
            "name": field_name,
            "type": field_info.annotation,
            "description": field_info.description or "",
            "required": field_info.is_required(),
        }

        # Add default value
        if not field_info.is_required():
            if field_info.default is not None:
                info["default"] = field_info.default
            elif field_info.default_factory:
                info["default"] = field_info.default_factory()

        # Extract Literal/Enum options from type annotation
        origin = get_origin(field_info.annotation)
        if origin is not None:
            args = get_args(field_info.annotation)
            if args:
                info["options"] = list(args)

        # Extract numeric/string constraints
        # These are available directly on FieldInfo in Pydantic v2
        constraints = {}
        for attr in ["ge", "le", "gt", "lt", "min_length", "max_length"]:
            val = getattr(field_info, attr, None)
            if val is not None:
                constraints[attr] = val

        if constraints:
            info["constraints"] = constraints

        return info

    @staticmethod
    def get_all_fields(model: type[BaseModel]) -> Dict[str, Dict[str, Any]]:
        """
        Get all fields from a Pydantic model.

        Args:
            model: Pydantic BaseModel class

        Returns:
            Dictionary mapping field_name -> field_info
        """
        fields = {}
        for field_name in model.model_fields:
            fields[field_name] = FieldCollector.get_field_info(model, field_name)
        return fields

    @staticmethod
    def format_field_prompt(field_info: Dict[str, Any]) -> str:
        """
        Format a user prompt for a single field.

        Args:
            field_info: Field information from get_field_info()

        Returns:
            Formatted prompt string with hints
        """
        lines = []

        field_name = field_info["name"]
        description = field_info.get("description", "")
        field_type = field_info.get("type", "")
        default = field_info.get("default")
        options = field_info.get("options")
        constraints = field_info.get("constraints", {})

        # Field name and description
        lines.append(f"\n{field_name}")
        if description:
            lines.append(f"  ({description})")

        # Type hint
        type_str = str(field_type).replace("typing.", "").replace("<class '", "").replace("'>", "")
        lines.append(f"  Type: {type_str}")

        # Options for Literal/Enum types
        if options:
            lines.append(f"  Options: {', '.join(str(o) for o in options)}")

        # Constraints
        if constraints:
            constraint_strs = []
            for key, val in constraints.items():
                if key == "min_length":
                    constraint_strs.append(f"min {val} chars")
                elif key == "max_length":
                    constraint_strs.append(f"max {val} chars")
                elif key == "ge":
                    constraint_strs.append(f">= {val}")
                elif key == "le":
                    constraint_strs.append(f"<= {val}")
            if constraint_strs:
                lines.append(f"  Constraints: {', '.join(constraint_strs)}")

        # Default value
        if default is not None:
            lines.append(f"  [Default: {default}]")
        elif field_info.get("required"):
            lines.append(f"  [Required]")

        prompt = "\n".join(lines) + "\n  Enter value: "
        return prompt

    @staticmethod
    def generate_table(model: type[BaseModel], config: Dict[str, Any]) -> str:
        """
        Generate a formatted table of current configuration.

        Args:
            model: Pydantic BaseModel class
            config: Current configuration dictionary

        Returns:
            Formatted table string
        """
        fields = FieldCollector.get_all_fields(model)

        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("CURRENT REQUEST CONFIGURATION")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"{'Field':<25} {'Value':<50}")
        lines.append("-" * 80)

        for field_name, field_info in fields.items():
            value = config.get(field_name, field_info.get("default", ""))

            # Format value
            if isinstance(value, bool):
                value_str = "✓" if value else "✗"
            elif isinstance(value, (list, tuple)):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)

            # Truncate if too long
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."

            lines.append(f"{field_name:<25} {value_str:<50}")

        lines.append("=" * 80)
        return "\n".join(lines) + "\n"

    @staticmethod
    def get_default_body(model: type[BaseModel]) -> Dict[str, Any]:
        """
        Create a request-ready body with all default values.

        Args:
            model: Pydantic BaseModel class

        Returns:
            Dictionary with all fields initialized to their default values
        """
        body = {}
        fields = FieldCollector.get_all_fields(model)

        for field_name, field_info in fields.items():
            if "default" in field_info:
                body[field_name] = field_info["default"]

        return body


class InteractiveFieldCollector:
    """Interactive form builder using FieldCollector for schema-driven user input"""

    def __init__(self, schema_class: type[BaseModel]):
        """
        Initialize with a schema class.

        Args:
            schema_class: Pydantic BaseModel class (e.g., BochaRequestSchema)
        """
        self.schema_class = schema_class
        self.schema_name = schema_class.__name__.replace("RequestSchema", "")
        self.fields = FieldCollector.get_all_fields(schema_class)

    def print_header(self):
        """Print form header"""
        print("\n" + "=" * 80)
        print(f"BUILD {self.schema_name} REQUEST")
        print("=" * 80)
        print(f"\nFill in the following {len(self.fields)} fields to build a request body:")
        print()

    def get_user_input_for_field(self, field_name: str, field_info: Dict[str, Any]):
        """
        Get user input for a single field with validation.

        Args:
            field_name: Name of the field
            field_info: Field information from FieldCollector

        Returns:
            User-provided value or default
        """
        # Generate prompt
        prompt = FieldCollector.format_field_prompt(field_info)

        field_type = field_info.get("type", "")
        options = field_info.get("options")
        default = field_info.get("default")
        required = field_info.get("required", False)

        while True:
            try:
                user_input = input(prompt).strip()

                # Use default if empty
                if not user_input:
                    if default is not None:
                        print(f"  → Using default: {default}\n")
                        return default
                    elif required:
                        print("  ✗ This field is required. Please enter a value.")
                        continue
                    else:
                        print("  → Skipped (optional)\n")
                        return None

                # Handle enum/literal fields
                if options:
                    if user_input in options:
                        print(f"  ✓ Selected: {user_input}\n")
                        return user_input
                    # Try numeric selection
                    try:
                        idx = int(user_input) - 1
                        if 0 <= idx < len(options):
                            selected = options[idx]
                            print(f"  ✓ Selected: {selected}\n")
                            return selected
                    except ValueError:
                        pass
                    print(f"  ✗ Please select from: {', '.join(options)}")
                    continue

                # Handle boolean fields
                if "bool" in str(field_type):
                    if user_input.lower() in ("y", "yes", "true", "1"):
                        print(f"  ✓ Value: True\n")
                        return True
                    elif user_input.lower() in ("n", "no", "false", "0"):
                        print(f"  ✓ Value: False\n")
                        return False
                    else:
                        print("  ✗ Please enter yes/no or true/false")
                        continue

                # Handle integer fields
                if "int" in str(field_type):
                    try:
                        value = int(user_input)
                        # Check constraints
                        constraints = field_info.get("constraints", {})
                        if "ge" in constraints and value < constraints["ge"]:
                            print(f"  ✗ Value must be >= {constraints['ge']}")
                            continue
                        if "le" in constraints and value > constraints["le"]:
                            print(f"  ✗ Value must be <= {constraints['le']}")
                            continue
                        print(f"  ✓ Value: {value}\n")
                        return value
                    except ValueError:
                        print("  ✗ Please enter a valid integer")
                        continue

                # Default: return as string
                constraints = field_info.get("constraints", {})
                if "min_length" in constraints:
                    if len(user_input) < constraints["min_length"]:
                        print(f"  ✗ Minimum length: {constraints['min_length']}")
                        continue
                if "max_length" in constraints:
                    if len(user_input) > constraints["max_length"]:
                        print(f"  ✗ Maximum length: {constraints['max_length']}")
                        continue

                print(f"  ✓ Value: {user_input}\n")
                return user_input

            except KeyboardInterrupt:
                print("\n\n✗ Cancelled by user")
                sys.exit(0)
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue

    def build_request_body(self, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Interactively build request body.

        Args:
            body: Optional existing body dictionary. If provided, existing values
                  will be shown as defaults during user input. If not provided,
                  a new empty dictionary will be used.

        Returns:
            Dictionary with user-provided values merged with existing body
        """
        self.print_header()

        if body is None:
            body = {}

        for i, (field_name, field_info) in enumerate(self.fields.items(), 1):
            print(f"[Field {i}/{len(self.fields)}]")

            # If field exists in body, use it as the current value in field_info
            if field_name in body:
                field_info = field_info.copy()
                field_info["default"] = body[field_name]

            value = self.get_user_input_for_field(field_name, field_info)
            if value is not None:
                body[field_name] = value

        return body

    def validate_and_display(self, body: Dict[str, Any]) -> bool:
        """
        Validate body against schema and display results.

        Args:
            body: Request body dictionary

        Returns:
            True if validation passed, False otherwise
        """
        print("\n" + "=" * 80)
        print("VALIDATING REQUEST BODY")
        print("=" * 80)
        print()

        try:
            # Validate using schema
            self.schema_class(**body)
            print("✓ Validation passed!\n")

            # Display as table
            print("FINAL REQUEST CONFIGURATION:")
            table = FieldCollector.generate_table(self.schema_class, body)
            print(table)

            # Display as JSON
            print("JSON REQUEST BODY:")
            print(json.dumps(body, indent=2, ensure_ascii=False))
            print()

            print("=" * 80)
            print("✅ READY TO SUBMIT")
            print("=" * 80)

            return True

        except ValidationError as e:
            print("✗ Validation failed:\n")
            for error in e.errors():
                print(f"  • {error['loc'][0]}: {error['msg']}")
            print()
            return False
