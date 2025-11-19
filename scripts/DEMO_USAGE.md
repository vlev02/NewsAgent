# FieldCollector Interactive Demo

This demo shows how to use `FieldCollector` to build request-ready JSON bodies interactively.

## Overview

`FieldCollector` extracts field information from Pydantic schemas and guides users through filling each field with:
- Field descriptions (hints)
- Type information
- Default values
- Constraints (min/max, options)
- Validation feedback

## Running the Demo

```bash
cd NewsAgent
python scripts/demo_field_collector.py
```

## What It Does

### Step 1: Select Schema
```
Available schemas:
  1. BOCHA
  2. META

Select schema (1-2): 1
```

### Step 2: Fill in Fields
For each field, you get:
- Field name
- Description (hint)
- Type information
- Constraints
- Default value (optional)

Example for BOCHA's `query` field:
```
[Field 1/4]

query
  (Search query keywords (1-1000 characters))
  Type: <class 'str'>
  Constraints: min 1 chars, max 1000 chars
  [Required]
  Enter value:
```

### Step 3: Optional Fields
Fields with defaults are optional - press Enter to skip:
```
freshness
  (Time filter for search results (oneDay, oneWeek, oneMonth, oneYear))
  Type: typing.Literal['oneDay', 'oneWeek', 'oneMonth', 'oneYear']
  Options: oneDay, oneWeek, oneMonth, oneYear
  [Default: oneWeek]
  Enter value:
  → Using default: oneWeek
```

### Step 4: Validation & Display
After filling all fields, you get:

**Configuration Table:**
```
════════════════════════════════════════════════════════════════════════════
CURRENT REQUEST CONFIGURATION
════════════════════════════════════════════════════════════════════════════

Field                     Value
────────────────────────────────────────────────────────────────────────────
query                     test query
freshness                 oneWeek
count                     10
summary                   ✓
════════════════════════════════════════════════════════════════════════════
```

**JSON Body:**
```json
{
  "query": "test query",
  "freshness": "oneWeek",
  "count": 10,
  "summary": true
}
```

## How FieldCollector Works

### Extract Field Information

```python
from src.schemas import BochaRequestSchema, FieldCollector

# Get all fields from schema
fields = FieldCollector.get_all_fields(BochaRequestSchema)

# Returns:
# {
#   "query": {
#     "name": "query",
#     "type": <class 'str'>,
#     "description": "Search query keywords...",
#     "required": True,
#     "constraints": {"min_length": 1, "max_length": 1000}
#   },
#   "freshness": {
#     "name": "freshness",
#     "type": Literal['oneDay', 'oneWeek', ...],
#     "description": "Time filter...",
#     "required": False,
#     "default": "oneWeek",
#     "options": ['oneDay', 'oneWeek', 'oneMonth', 'oneYear']
#   },
#   ...
# }
```

### Get Information About Single Field

```python
field_info = fields["query"]

# Get type
print(field_info["type"])  # <class 'str'>

# Get description (hint)
print(field_info["description"])  # "Search query keywords..."

# Get constraints
print(field_info["constraints"])  # {"min_length": 1, "max_length": 1000}

# Check if required
print(field_info["required"])  # True

# Get default (if exists)
print(field_info.get("default"))  # None (query is required)
```

### Generate User Prompt

```python
prompt = FieldCollector.format_field_prompt(field_info)
print(prompt)
# Output:
# query
#   (Search query keywords (1-1000 characters))
#   Type: <class 'str'>
#   Constraints: min 1 chars, max 1000 chars
#   [Required]
#   Enter value:
```

### Generate Configuration Table

```python
config = {
    "query": "test",
    "freshness": "oneWeek",
    "count": 10,
    "summary": True
}

table = FieldCollector.generate_table(BochaRequestSchema, config)
print(table)
```

### Validate Configuration

```python
from src.schemas import validate_request_body
from pydantic import ValidationError

body = {
    "query": "test",
    "freshness": "oneWeek",
    "count": 10,
    "summary": True
}

try:
    result = validate_request_body("BOCHA", body)
    print("Valid!")
except ValidationError as e:
    print(f"Invalid: {e}")
```

## Key Methods

### `FieldCollector.get_all_fields(model)`
Extract all field information from a Pydantic model.

```python
fields = FieldCollector.get_all_fields(BochaRequestSchema)
# Returns: Dict[str, Dict[str, Any]]
```

### `FieldCollector.get_field_info(model, field_name)`
Get information about a single field.

```python
field_info = FieldCollector.get_field_info(BochaRequestSchema, "query")
# Returns: Dict[str, Any]
```

### `FieldCollector.format_field_prompt(field_info)`
Generate a user-friendly prompt for a field.

```python
prompt = FieldCollector.format_field_prompt(field_info)
# Returns: str (formatted prompt with hints)
```

### `FieldCollector.generate_table(model, config)`
Generate a formatted table of current configuration.

```python
table = FieldCollector.generate_table(BochaRequestSchema, config)
# Returns: str (formatted table)
```

## Benefits

✅ **No Hardcoded Values**: All field information comes from schema
✅ **Automatic Validation**: Constraints extracted from schema
✅ **User Guidance**: Descriptions and hints from field definitions
✅ **Type-Safe**: Pydantic validates all input
✅ **Reusable**: Works with any RequestSchema subclass
✅ **Extensible**: Add new agents by creating new schema, everything else works automatically

## Extending to Other Agents

The demo works with any RequestSchema. To use with a new agent:

```python
from src.schemas import LlamaRequestSchema, FieldCollector

# Same pattern - no changes needed!
collector = InteractiveFieldCollector(LlamaRequestSchema)
body = collector.build_request_body()
collector.validate_and_display(body)
```

## Example Output

Full example session:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                   FieldCollector Interactive Demo                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

Available schemas:
  1. BOCHA
  2. META

Select schema (1-2): 1

════════════════════════════════════════════════════════════════════════════════
BUILD BOCHA REQUEST
════════════════════════════════════════════════════════════════════════════════

Fill in the following 4 fields to build a request body:

[Field 1/4]

query
  (Search query keywords (1-1000 characters))
  Type: <class 'str'>
  Constraints: min 1 chars, max 1000 chars
  [Required]
  Enter value: AI news
  ✓ Value: AI news

[Field 2/4]

freshness
  (Time filter for search results (oneDay, oneWeek, oneMonth, oneYear))
  Type: typing.Literal['oneDay', 'oneWeek', 'oneMonth', 'oneYear']
  Options: oneDay, oneWeek, oneMonth, oneYear
  [Default: oneWeek]
  Enter value:
  → Using default: oneWeek

[Field 3/4]

count
  (Number of results to return (1-100))
  Type: <class 'int'>
  Constraints: >= 1, <= 100
  [Default: 10]
  Enter value:
  → Using default: 10

[Field 4/4]

summary
  (Include AI-generated summary in results)
  Type: <class 'bool'>
  [Default: True]
  Enter value:
  → Using default: True

════════════════════════════════════════════════════════════════════════════════
VALIDATING REQUEST BODY
════════════════════════════════════════════════════════════════════════════════

✓ Validation passed!

FINAL REQUEST CONFIGURATION:
════════════════════════════════════════════════════════════════════════════════
CURRENT REQUEST CONFIGURATION
════════════════════════════════════════════════════════════════════════════════

Field                     Value
────────────────────────────────────────────────────────────────────────────
query                     AI news
freshness                 oneWeek
count                     10
summary                   ✓
════════════════════════════════════════════════════════════════════════════════

JSON REQUEST BODY:
{
  "query": "AI news",
  "freshness": "oneWeek",
  "count": 10,
  "summary": true
}

════════════════════════════════════════════════════════════════════════════════
✅ READY TO SUBMIT
════════════════════════════════════════════════════════════════════════════════
```
