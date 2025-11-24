# Agent Pipeline Manual

Use this batch pipeline when you want to trigger multiple agents, persist their responses, and capture a consolidated snapshot of each run. Configure the pieces once and rerun the script whenever your monitoring cadence calls for fresh data.

- **Select agents:** edit `config/agent_pipeline.yaml` and list the agent names under `agents`.
- **Edit agent configs:** update endpoints, auth settings, and request bodies per agent inside `config/agents.yaml`.
- **Edit Jinja templates:** tune the prompt templates for LLM agents in `src/templates/` to steer narrative or formatting.
- **Execute:** run `python scripts/run_agent_pipeline.py` from the project root to launch the batch job.
- **Explore output:** open the timestamped JSON files in `data/pipeline_runs/` or dig deeper with `scripts/call_data_explorer.py`.
