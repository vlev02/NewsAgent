# NewsAgent

Multi-agent workflow for collecting, caching, and exploring tech-news intelligence across REST and LLM-based providers.

## Dependencies
- Python 3.12+
- pip / virtualenv
- System packages required by any agent-specific SDKs (see `requirements.txt`)

## Installation
```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Batch Pipeline Usage
1. Edit `config/agent_pipeline.yaml` to list the agents you want to run.
2. Adjust per-agent settings in `config/agents.yaml` and templates in `src/templates/` as needed.
3. Run `python scripts/run_agent_pipeline.py` to execute all selected agents.
4. Review the timestamped JSON summary in `data/pipeline_runs/` and dive deeper with `scripts/call_data_explorer.py`.

## Adding a New Agent
Follow `src/agents/docs/AGENT_CREATION_PROMPT.md`:
- Prepare a sample API request and decide whether the agent is `LLM_SEARCH` or `REST_API`.
- Generate the agent class (`src/agents/agent_<name>.py`), schemas, and optional Jinja template.
- Register configuration entries in `config/agents.yaml` (endpoint, auth, query body, template vars).
- The manager auto-discovers `SearchAgent` subclasses, so the new agent appears in the marketplace automatically.

## Useful Commands
- `python scripts/call_agent.py` — interactively run a single agent and inspect/stash results.
- `python scripts/call_data_explorer.py` — browse recorded requests/items from the DataManager.
- `pytest` — run the automated test suite (focus on DataManager/agent wrapper behaviors).
