#!/usr/bin/env python3
"""Batch pipeline for executing multiple agents and saving their outputs.

Steps performed:
1. Read config/agent_pipeline.yaml to determine which agents to run.
2. Create/initialize each agent, call submit_request(), and capture responses.
3. Persist all Request/ResponseItem records via DataManager.
4. Write a consolidated JSON summary for the run.
5. Print concise logs and an operator manual at the end.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Ensure project root on path when script invoked directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agents import get_agent_manager
from src.data_manager import (
    get_data_manager,
    DataModelType,
    RequestModel,
)
from src.utils.simu_request import SimuRequest

CONFIG_PATH = PROJECT_ROOT / "config" / "agent_pipeline.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "pipeline_runs"
OUTPUT_MAX_PREVIEW = 800


def load_pipeline_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Pipeline config not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("agents", [])
    data.setdefault("options", {})
    return data


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def serialize_preview(payload: Any) -> Any:
    """Return JSON serializable preview (trim long responses)."""
    try:
        text = json.dumps(payload, ensure_ascii=False)
    except TypeError:
        return str(payload)
    if len(text) > OUTPUT_MAX_PREVIEW:
        return text[:OUTPUT_MAX_PREVIEW] + "..."
    return json.loads(text)


def record_run(
    agent,
    result,
    execution_ms: int,
    dm,
) -> Dict[str, Any]:
    """Record request + response items into DataManager and return summary info."""
    response_type = "real_call"
    actual_response = result
    if isinstance(result, dict) and "response_type" in result:
        response_type = result.get("response_type", "real_call")
        actual_response = result.get("response")

    success = not isinstance(result, Exception)
    error_message = str(result) if isinstance(result, Exception) else None
    http_status = 200 if success else 500

    request_data = agent.parse_request(
        http_status=http_status,
        raw_response=actual_response if success else None,
        execution_time_ms=execution_ms,
        success=success,
        error_message=error_message,
        response_type=response_type,
    )
    request_id = dm.record(DataModelType.REQUEST, request_data)
    request_model = RequestModel(request_id=request_id, agent_name=agent.NAME)

    response_items: List[str] = []
    try:
        parsed_items = []
        if success and isinstance(actual_response, dict):
            parsed_items = agent.parse_response_items(actual_response)
        for item in parsed_items:
            item_id = dm.record(DataModelType.RESPONSE_ITEM, item, associated_case=request_model)
            response_items.append(item_id)
    except Exception as item_err:  # pylint: disable=broad-except
        response_items.append(f"FAILED_TO_PARSE: {item_err}")

    return {
        "request_id": request_id,
        "response_items": response_items,
        "response_preview": serialize_preview(actual_response if success else {"error": error_message}),
        "success": success,
        "error": error_message,
        "execution_ms": execution_ms,
    }


def run_pipeline():
    config = load_pipeline_config()
    selected_agents = config.get("agents", [])
    options = config.get("options", {})
    output_dir = ensure_output_dir(
        Path(options.get("output_dir", DEFAULT_OUTPUT_DIR))
        if options.get("output_dir")
        else DEFAULT_OUTPUT_DIR
    )

    print("✓ Environment loaded from:", PROJECT_ROOT / ".env")
    SimuRequest.status()

    manager = get_agent_manager()
    dm = get_data_manager()

    if not selected_agents:
        selected_agents = sorted(manager.agent_marketplace.keys())
        print("No agents specified in YAML. Defaulting to:", ", ".join(selected_agents))

    summaries = []
    for agent_name in selected_agents:
        print("\n=== Running", agent_name, "===")
        try:
            agent = manager.create_agent(agent_name)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"✗ Failed to create {agent_name}: {exc}")
            summaries.append({"agent_name": agent_name, "success": False, "error": str(exc)})
            continue

        start = time.time()
        try:
            result = agent.submit_request()
        except Exception as call_err:  # pylint: disable=broad-except
            execution_ms = int((time.time() - start) * 1000)
            print(f"✗ submit_request failed for {agent_name}: {call_err}")
            summary = record_run(agent, call_err, execution_ms, dm)
            summary["agent_name"] = agent_name
            summaries.append(summary)
            continue

        execution_ms = int((time.time() - start) * 1000)
        print(f"✓ {agent_name} completed in {execution_ms} ms")
        summary = record_run(agent, result, execution_ms, dm)
        summary["agent_name"] = agent_name
        summaries.append(summary)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"pipeline_run_{timestamp}.json"
    payload = {
        "run_timestamp": datetime.utcnow().isoformat() + "Z",
        "agents": summaries,
        "stats": {
            "requests_recorded": sum(1 for s in summaries if s.get("request_id")),
            "items_recorded": sum(
                len([item for item in s.get("response_items", []) if not str(item).startswith("FAILED")])
                for s in summaries
            ),
        },
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Export DataManager-style response items for this run
    response_item_records = []
    for summary in summaries:
        for item_id in summary.get("response_items", []):
            if isinstance(item_id, str) and item_id.startswith("FAILED"):
                continue
            if not item_id:
                continue
            record = dm.retrieve(DataModelType.RESPONSE_ITEM, item_id)
            if record:
                response_item_records.append(record)

    items_output_path = None
    if response_item_records:
        items_output_path = output_dir / f"pipeline_items_{timestamp}.json"
        with open(items_output_path, "w", encoding="utf-8") as f:
            json.dump({"response_item": response_item_records}, f, indent=2, ensure_ascii=False)

    print("\n=== Pipeline Summary ===")
    for summary in summaries:
        status = "SUCCESS" if summary.get("success") else "FAILED"
        print(f"{summary.get('agent_name')}: {status} | request_id={summary.get('request_id')} | items={len(summary.get('response_items', []))}")
    print(f"Output written to: {output_path}")
    if items_output_path:
        print(f"Response items exported to: {items_output_path}")
    else:
        print("No response items were recorded during this run.")

    print_manual()


def print_manual():
    print("\nPipeline Manual")
    print("Use this pipeline to batch-run agents, persist their data, and review aggregated outputs.")
    print("Configure agents and templates once, then trigger repeatable data collection runs whenever needed.")
    steps = [
        "Select agents: edit config/agent_pipeline.yaml and list the agent names under `agents`.",
        "Edit agent configs: adjust per-agent settings inside config/agents.yaml (endpoints, request bodies, etc.).",
        "Edit Jinja templates: update files in src/templates/ to change prompt structures for LLM agents.",
        "Execute: run `python scripts/run_agent_pipeline.py` to launch the batch pipeline.",
        "Explore output: inspect the generated JSON in data/pipeline_runs/ and use scripts/call_data_explorer.py for database insights.",
    ]
    for step in steps:
        print("-", step)


if __name__ == "__main__":
    run_pipeline()
