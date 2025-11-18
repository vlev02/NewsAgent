# CLAUDE.md - Custom Configuration

This file provides critical configuration guidelines for Claude Code working on this repository.

## Critical Development Guidelines

### Documentation Policy
**DO NOT** output any summary/reference documentation files (*.md) without explicit permission. Documentation files create clutter in the project and are not helpful. Only create documentation when explicitly requested by the user.

### Git Commit Policy
**DO NOT** submit any git commits without explicit permission. Wait for user approval before creating commits. User will explicitly request commits when ready.

### Testing Policy
- All test modules **MUST** be saved in the `tests/` directory
- All tests **MUST** follow unittest format (inherit from `unittest.TestCase`)
- Test file naming: `tests/test_*.py` (e.g., `tests/test_agents.py`, `tests/test_database.py`)
- Example structure:
  ```python
  import unittest
  from src.agents.bocha import BochaAgent

  class TestBochaAgent(unittest.TestCase):
      def setUp(self):
          """Set up test fixtures"""
          pass

      def test_agent_initialization(self):
          """Test agent can be initialized"""
          self.assertIsNotNone(agent)

      def tearDown(self):
          """Clean up after tests"""
          pass
  ```

## Project Structure

```
NewsAgent/
├── src/                      # Modular architecture
├── scripts/                  # Debug and utility scripts
├── config/                   # Configuration files
├── examples/                 # Usage examples
├── tests/                    # Unit tests (unittest format)
├── docs/                     # Documentation
├── .env.example              # Environment template
├── .claude/CLAUDE.md         # This file
└── requirements.txt          # Dependencies
```

## Environment Setup

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Key Patterns

- **Agent Architecture**: Inherit from `SearchAgent` abstract base class
- **Configuration**: Centralized in `config/agents.yaml`
- **Environment**: Use `SchedulerSettings.initialize()` for all settings
- **Data Models**: Type-safe dataclasses (SearchItem, QueryRequest, QueryResponse)
- **Database**: Abstract DatabaseBackend interface with SQLite3 implementation
- **Debug Scripts**: Use modular `DebugAgentScript` base class pattern

## Important Notes

- Never commit `.env` file to version control
- Database uses no cascade relations for flexibility
- All API keys from `.env` file
- Use PathManager for all absolute paths
- Follow feature-based git commit naming convention
