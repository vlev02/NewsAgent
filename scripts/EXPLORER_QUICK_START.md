# Data Explorer - Quick Start Guide

## Running the Script

```bash
python scripts/call_data_explorer.py
```

You'll see a menu-driven interface like this:

```
================================================================================
                         📚 DataManager Explorer
================================================================================

================================================================================
                            Main Menu
================================================================================

  1. View Overview Statistics
  2. View Latest Items
  3. Explore Cascade Relationships
  4. Search by Agent
  5. Search by Case ID
  6. Export Data to JSON
  7. Exit

Select option (1-7):
```

## Quick Menu Reference

| # | Feature | What it does | Best for |
|---|---------|-------------|----------|
| 1 | **Overview Statistics** | Show total records and agent breakdown | Understanding data distribution |
| 2 | **Latest Items** | View N recent items per model | Seeing recent activity |
| 3 | **Cascade Explorer** | Navigate REQUEST→QUERY→ITEM relationships | Tracing data flow |
| 4 | **Search by Agent** | Filter by agent name | Understanding specific agent's data |
| 5 | **Search by Case ID** | Find specific record | Locating known data |
| 6 | **Export Data** | Save to JSON files | External analysis |
| 7 | **Exit** | Quit the explorer | When done |

## Common Workflows

### I want to see overall statistics
```
1. Select option: 1
2. View summary and agent breakdown
3. Press Enter to return to menu
```

### I want to explore data relationships
```
1. Select option: 3
2. Choose starting model (request/query)
3. Enter case ID or select from samples
4. View associated items
5. Choose to explore deeper (y/n)
```

### I want to find data by agent
```
1. Select option: 4
2. Select agent from list (1-N)
3. View statistics for that agent
4. Press Enter to return to menu
```

### I want to search for specific record
```
1. Select option: 5
2. Enter case ID you're looking for
3. System finds and displays record
4. Choose to explore related items (y/n)
```

### I want to export data for analysis
```
1. Select option: 6
2. Choose what to export (1-5):
   1 = Statistics summary
   2 = All REQUEST records
   3 = All QUERY records
   4 = All RESPONSE_ITEM records
   5 = Complete data dump
3. File saved to project root (datamanager_*.json)
```

## Data Model Overview

```
REQUEST
├─ Contains: API request and response
├─ Fields: request_id, agent_name, status, execution_time, etc.
└─ Links to: QUERY (one-to-many)

QUERY
├─ Contains: Search parameters
├─ Fields: query_id, request_id, keywords, topics, etc.
└─ Links to: RESPONSE_ITEM (one-to-many)

RESPONSE_ITEM
├─ Contains: Individual search result
├─ Fields: item_id, query_id, title, source_url, etc.
└─ No further links (leaf node)
```

## Sample Output

### Option 1 - Overview Statistics
```
📊 DataManager Overview

Total Records:
  • query_model          :     96 records
  • request_model        :    158 records
  • response_item        :    105 records

Breakdown by Model:
  request_model:
    - BOCHA                :  103 records
    - META                 :   19 records
```

### Option 2 - Latest Items
```
[1] REQUEST 3216d8ad...
    Agent: BOCHA
    Status: 200
    Time: 2024-11-22
    Execution: 1500ms

[2] QUERY 9b11135d...
    Agent: META
    Keywords: ['AI', 'news']
    Max results: 10
```

### Option 3 - Cascade
```
✓ Found 2 associated query(ies)

[1] QUERY 96d78672...
    Agent: DEMO_AGENT
    Keywords: ['AI', 'news']
    Max results: 10

Explore RESPONSE_ITEMs for query 1? (y/n):
```

## File Locations

| File | Purpose |
|------|---------|
| `scripts/call_data_explorer.py` | Main interactive script |
| `scripts/DATA_EXPLORER_README.md` | Comprehensive documentation |
| `scripts/EXPLORER_QUICK_START.md` | This quick reference |
| `datamanager_*.json` | Exported data files (created on demand) |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` | Gracefully exit at any time |
| `Enter` | Accept default value (if shown) |
| `y` / `n` | Yes/No for interactive prompts |

## Tips & Tricks

### Getting Sample IDs
When searching by case ID, the explorer shows sample IDs:
```
Sample REQUEST IDs (use these to explore):
  1. 3216d8ad-1234-5678-abcd-ef1234567890
  2. 7f8a9b0c-5678-9012-cdef-1234567890ab
```
Copy and paste these into your search.

### Efficient Exploration
1. Start with **Option 1** to understand your data
2. Then use **Option 3** to explore relationships
3. Use **Option 5** to find specific records
4. Use **Option 6** to export for deeper analysis

### Understanding Counts
- In overview: Total records per model type
- In latest items: Most recent N records
- In cascade: Associated items only (not total)
- In export: Records included in file (up to limit)

### Export File Sizes
- Statistics: < 1 KB
- Requests: ~10 KB per 100 records
- Queries: ~5 KB per 100 records
- Items: ~15 KB per 100 records
- Full dump: Size varies with data volume

## Common Issues

### "No records found"
- Run `python scripts/call_agent.py` to create data first
- Or check that agent names match what you're searching for

### "Case ID not found"
- Verify you have the correct case ID
- Use **Option 4** to see available agents first
- Use **Option 2** to get sample IDs

### Export fails
- Check disk space in project directory
- Verify write permissions
- Try exporting less data (use limit options)

## Next Steps

1. **Run the script**: `python scripts/call_data_explorer.py`
2. **Select Option 1**: Get overview of your data
3. **Select Option 3**: Explore cascade relationships
4. **Select Option 6**: Export data for analysis
5. **Check documentation**: See `DATA_EXPLORER_README.md` for advanced usage

## Need Help?

See the full documentation: [DATA_EXPLORER_README.md](DATA_EXPLORER_README.md)

Or use in Python:
```python
from scripts.call_data_explorer import DataExplorer

explorer = DataExplorer()
explorer.show_overview()  # Show statistics
result = explorer.dm.smart_query()  # Get raw data
```

---

**Happy exploring!** 🚀
