# NewsAgent Scheduler - Interactive Pipeline Manager

The Scheduler is a terminal-based interactive CLI for managing the entire NewsAgent pipeline. It provides a user-friendly interface for submitting queries, exploring results, and managing the database.

## Quick Start

```bash
# Run the scheduler
python -m examples.scheduler

# Run with custom database
python -m examples.scheduler --db custom_news.db

# Run with config file
python -m examples.scheduler --config scheduler_config.json
```

## Main Menu

The scheduler displays an interactive menu with these actions:

1. **Explore Recent Research** - Browse queries, responses, and results
2. **Submit Query** - Create and submit new search queries with step-by-step validation
3. **Export Results** - Export items to JSON or Markdown format
4. **View Statistics** - Display database statistics and project overview
5. **Settings** - View and manage agent configurations
6. **Exit** - Close the scheduler

## Actions

### 1. Explore Recent Research

Browse your research history and results.

**Sub-options:**
- **View recent queries** - See your last queries with details
- **View recent responses by agent** - See which agents returned results
- **View items by source type** - Explore results grouped by source (BOCHA, XUNFEI, etc.)
- **Search items by content** - Find items matching a keyword

**Example:**
```
→ Explore Recent Research
What would you like to explore?
  1. View recent queries
  2. View recent responses by agent
  3. View items by source type
  4. Search items by content
  5. Go back to main menu

Enter choice (0-5): 1

→ Recent Queries
Query ID | Fields              | Topics            | Agents | Date
--------|---------------------|-------------------|--------|------------------
a1b2c3d4 | 自动驾驶, 具身智能  | 特斯拉FSD, 人形... | BOCHA  | 2024-11-17 14:30
```

### 2. Submit Query

Submit a new search query with interactive step-by-step guidance.

**Steps:**
1. **Select Agents** - Choose which agents to query
2. **Enter Query Fields** - Specify domains (e.g., "自动驾驶, 具身智能")
3. **Enter Query Topics** - Specify topics (e.g., "特斯拉FSD, 人形机器人")
4. **Select Time Filter** - Choose time range (1 day, 7 days, 30 days, 1 year)
5. **Set Result Limits** - Specify max results per agent
6. **Review Query** - Confirm all parameters
7. **Preview Agent Prompts** - Review Jinja2 templates for each agent
8. **Check Resources & Execute** - Verify API keys and execute

**Example:**
```
→ Submit New Query

→ Step 1: Select Agents
Available agents: XUNFEI, BOCHA, HUNYUAN, QIANFAN, META, TWITTER

What would you like to do?
  1. XUNFEI
  2. BOCHA
  3. HUNYUAN
  ...

Select agents (one at a time)
Enter choice (0-8): 2
✅ Selected: BOCHA

→ Step 2: Enter Query Fields (Domains)
ℹ️  Separate multiple fields with commas (e.g., '自动驾驶, 具身智能, 大模型')
Enter query fields: 自动驾驶, 大模型
✅ Query fields: 自动驾驶, 大模型

→ Step 3: Enter Query Topics
ℹ️  Separate multiple topics with commas (e.g., '特斯拉FSD, 人形机器人')
Enter query topics: 特斯拉FSD, AI大模型突破
✅ Query topics: 特斯拉FSD, AI大模型突破

[... continues through remaining steps ...]

→ Step 8: Check Resources & Execute
BOCHA: Configuration valid
    ✓ API Key configured

Execute query? (y/n): y

Executing query...
✅ Query executed successfully!
Total Items Retrieved: 15
Responses: 1
  BOCHA: ✓ 15 items (2082ms)
```

### 3. Export Results

Export search results to JSON or Markdown format.

**Export Options:**
- **All items from database** - Export everything
- **Items by source type** - Export items from specific source
- **Items from recent query** - Export results from a specific query

**Formats:**
- **JSON** - Structured data format with metadata
- **Markdown** - Human-readable format with formatting

**Example:**
```
→ Export Results
What would you like to export?
  1. All items from database
  2. Items by source type
  3. Items from recent query
  4. Go back to main menu

Enter choice (0-4): 1

Select export format?
  1. JSON
  2. Markdown

Enter choice (0-2): 1

ℹ️  Default output: data/all_items_20241117_143530.json
Custom filename (or press Enter for default):
✅ Exported 15 items to data/all_items_20241117_143530.json
ℹ️  File size: 125.3 KB
```

### 4. View Statistics

Display comprehensive database statistics.

Shows:
- Total queries, responses, and items
- Breakdown by agent
- Breakdown by source type
- Unique sources

**Example:**
```
→ Database Statistics
Total Queries: 3
Total Responses: 3
Total Items: 15
Unique Sources: 1

→ Responses by Agent
Agent | Count
------|------
BOCHA | 3

→ Items by Source Type
Source | Count
-------|------
BOCHA  | 15
```

### 5. Settings

View and manage agent configurations.

**Options:**
- **View agent capabilities** - See endpoint, auth method, features
- **View database configuration** - Check database stats
- **Agent status** - Which agents have API keys configured

**Example:**
```
→ Settings
Configured Agents: 6
  XUNFEI: ✗ API Key configured
  BOCHA: ✓ API Key configured
  HUNYUAN: ✗ API Key configured
  QIANFAN: ✗ API Key configured
  META: ✗ API Key configured
  TWITTER: ✗ API Key configured
```

## Configuration

### Environment Variables

Configure API keys via `.env` file:

```bash
# Xunfei Spark API
XUNFEI_APPID=your_appid_here
XUNFEI_APISecret=your_api_secret_here
XUNFEI_APIKey=your_api_key_here

# BOCHA Web Search API
BOCHA_API_KEY=your_api_key_here

# Tencent Hunyuan API
HUNYUAN_API_KEY=your_api_key_here

# Baidu Qianfan
QIANFAN_API_KEY=your_api_key_here

# MetaSo Search
META_API_KEY=your_api_key_here

# Twitter/X API
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Database and Logging
DATABASE_PATH=newsagent.db
LOG_LEVEL=INFO
LOG_FILE=newsagent.log
```

### Config File

Create a JSON configuration file:

```json
{
  "database_path": "newsagent.db",
  "log_level": "INFO",
  "log_file": "newsagent.log",
  "default_time_range_days": 7,
  "default_max_results": 10,
  "export_directory": "data"
}
```

Use it:
```bash
python -m examples.scheduler --config scheduler_config.json
```

## Architecture

### Module Structure

```
src/scheduler/
├── __init__.py              # Package initialization
├── scheduler.py             # Main Scheduler class
├── interactive.py           # Terminal UI utilities
├── config.py               # Configuration loader
└── actions/
    ├── __init__.py         # Actions package
    ├── base.py             # Abstract Action base class
    ├── explore.py          # Explore action
    ├── submit_query.py     # Submit query action
    ├── export.py           # Export action
    ├── stats.py            # Statistics action
    └── settings.py         # Settings action
```

### Class Hierarchy

```
Scheduler
├── SchedulerConfig
├── DatabaseManager
├── Action (Abstract)
│   ├── ExploreAction
│   ├── SubmitQueryAction
│   ├── ExportAction
│   ├── StatsAction
│   └── SettingsAction
└── Interactive utilities
    ├── prompt_choice()
    ├── prompt_text()
    ├── prompt_list()
    ├── print_*() functions
    └── Colors
```

## Interactive UI Features

### Input Methods

- **Menu Selection** - Navigate with numeric choices
- **Text Input** - Enter custom values with validation
- **List Input** - Enter comma-separated values
- **Confirmation** - Confirm actions with y/n

### Output Formatting

- **Color Coding** - Different colors for different message types
  - ✅ Success (Green)
  - ❌ Error (Red)
  - ⚠️ Warning (Yellow)
  - ℹ️ Info (Cyan)
  - → Section headers (Cyan, bold)

- **Tables** - Formatted data tables with aligned columns
- **Indentation** - Hierarchical information display

## Query Submission Workflow

The submit query action provides a comprehensive step-by-step workflow:

1. **Agent Selection**
   - Choose from available agents
   - View agent capabilities and rate limits
   - Select multiple agents if desired

2. **Query Definition**
   - Enter search fields (domains)
   - Enter specific topics
   - Support for Chinese and English text

3. **Time Filtering**
   - 1 day, 7 days (1 week), 30 days (1 month), 365 days (1 year)
   - Automatic mapping to API-specific formats

4. **Result Configuration**
   - Set result limits (5, 10, 20, 50, 100, or custom)
   - Select deduplication strategy

5. **Review & Validation**
   - Confirm all parameters
   - Preview Jinja2 templates
   - Check API key configuration

6. **Execution**
   - Real-time feedback
   - Item count and timing
   - Sample results display

## Data Export

### JSON Export Format

```json
{
  "export_date": "2024-11-17T14:30:45.123456",
  "item_count": 15,
  "query": {
    "query_id": "abc123def456",
    "fields": ["自动驾驶", "大模型"],
    "topics": ["特斯拉FSD", "AI突破"],
    "agents": ["BOCHA"],
    "time_range_days": 7
  },
  "items": [
    {
      "id": "item_uuid",
      "title": "Article Title",
      "content": "Article content...",
      "source_url": "https://...",
      "source_name": "Source Name",
      "source_type": "BOCHA",
      "timestamp": "2024-11-17T12:00:00",
      "category": "Technology",
      "relevance_score": 0.95,
      "key_entities": ["Tesla", "FSD"]
    }
  ]
}
```

### Markdown Export Format

```markdown
# Search Results Export

**Export Date:** 2024-11-17 14:30:45

## Query Information

- **Fields:** 自动驾驶, 大模型
- **Topics:** 特斯拉FSD, AI大模型突破
- **Agents:** BOCHA
- **Time Range:** 7 days

## Results (15 items)

### 1. Article Title

**Source:** Source Name (BOCHA)
**Date:** 2024-11-17 14:30
**URL:** [https://example.com](https://example.com)

**Category:** Technology
**Relevance:** 0.95
**Entities:** Tesla, FSD

Article content here...

---
```

## Tips & Best Practices

1. **Before Submitting Queries:**
   - Check Settings to verify API keys are configured
   - View recent queries to avoid duplicates
   - Start with smaller time ranges (7 days) for faster results

2. **Exploring Results:**
   - Use Search to find specific topics
   - View by source type to understand data distribution
   - Check recent responses to see which agents worked best

3. **Exporting Data:**
   - Use JSON for data analysis
   - Use Markdown for sharing with others
   - Set custom filenames for organization

4. **Managing Database:**
   - Export regularly to back up important results
   - Review statistics to understand data volume
   - Check agent status when queries fail

## Troubleshooting

### "API key not set" warning

- Make sure `.env` file exists in project root
- Copy `.env.example` to `.env` and fill in API keys
- Run `source .env` or set variables in your shell

### No results returned

- Check Settings to verify agent API key is set
- View recent responses to see if query was executed
- Try a different agent or broader time filter

### Database errors

- Ensure write permissions to project directory
- Check database file is not corrupted
- Try deleting `newsagent.db` to start fresh

### Import errors

- Verify all source files are in place
- Run `pip install -r requirements.txt`
- Check Python version (3.9+)

## Advanced Usage

### Custom Configuration

Create a custom config file for different environments:

```json
{
  "database_path": "/data/newsagent/prod.db",
  "log_level": "DEBUG",
  "log_file": "/logs/newsagent.log",
  "default_time_range_days": 30,
  "default_max_results": 50,
  "export_directory": "/exports"
}
```

### Batch Processing

While the scheduler is interactive, you can script interactions:

```python
from src.scheduler import Scheduler

scheduler = Scheduler()
# Programmatically access actions
explore_action = scheduler.actions[0]
explore_action.execute()
```

## Future Enhancements

Planned features for the scheduler:

- [ ] Async query execution
- [ ] Query templates and presets
- [ ] Advanced search filters
- [ ] Real-time result streaming
- [ ] Result deduplication strategies
- [ ] API cost tracking
- [ ] Bulk query import
- [ ] Result tagging and categorization
- [ ] Notification system
- [ ] Query scheduling (cron-like)

---

**Version:** 1.0
**Status:** Production-Ready
**Last Updated:** November 17, 2024
