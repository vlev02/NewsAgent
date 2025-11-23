# Agent Creation Prompt - Quick Start

## Instructions
1. Copy this entire prompt
2. **Replace the demo request below** with your actual API demo
3. Paste to Claude Code - it will create the agent automatically

---

## DEMO REQUEST - EDIT THIS SECTION

```json
{
  "url": "https://api.example.com/v1/endpoint",
  "headers": {"Authorization": "Bearer <key>"},
  "json": {
    "model": "example-model",
    "stream": false,
    "temperature": 0.3
  }
}
```

---

## AGENT CREATION TASK

Based on the demo request above, create a complete agent for the NewsAgent project:

**Steps to follow:**
1. Analyze the demo request (endpoint, auth method, fields, types)
2. Determine agent type: LLM_SEARCH (has messages array) or REST_API (query-based)
3. Create agent class file: `src/agents/agent_[name].py`
   - Define RequestSchema with all demo fields
   - Define TemplateSchema (LLM_SEARCH only)
   - Implement Agent class inheriting SearchAgent
   - Implement required methods: `__init__`, `get_header_dict`, `_get_request_schema_class`
   - For LLM: implement `_load_template`, `_render_prompt_template`, `template_vars` property, `request_body` property
4. Create Jinja2 template: `src/templates/[agent_name]_prompt.jinja2` (LLM_SEARCH only)
5. Update `config/agents.yaml` with agent configuration
   - Add agent section with: name, type, endpoint, auth_header
   - For LLM: add template and template_vars sections
   - Add query_body with all demo fields
6. Verify auto-discovery (agent appears in marketplace automatically)
7. Test request body generation

**Key rules:**
- File naming: `agent_[name].py` (lowercase)
- Class naming: `[Name]Agent` with NAME = "[NAME]" (uppercase)
- Api keys: api_keys = ["[NAME]_API_KEY"]
- Types: Match demo exactly (string vs float, etc.)
- For LLM agents: auto-generate messages from template
- For special configs (tools, filters): auto-build from query_body
- No hardcoding endpoints - all config goes in agents.yaml

**Verification:**
- Agent discovered in marketplace
- Request body generates without errors
- Headers constructed correctly
- For LLM: messages auto-generate from template

Proceed with agent creation.
```
