# Documentation & Test File Organization Plan

## Overview

This document outlines the proposed organization for documentation and test files to maintain a clean project structure.

---

## Current State

### Root Level Documentation
```
NewsAgent/
├── README.md                          (Project overview)
├── SCHEDULER_SETUP.md                 (API key setup guide)
├── FAKE_RESPONSE_MANUAL.md            (Fake response usage)
├── MODULE_CHECKING_GUIDE.md           (Just created)
├── CLAUDE.md                          (Development notes)
└── docs/
    ├── SCHEDULER_SETTINGS.md
    ├── SCHEDULER_COMPLETE_GUIDE.md
    ├── SCHEDULER.md
    ├── README_NEW_ARCHITECTURE.md
    └── IMPLEMENTATION_SUMMARY.md
```

### Test Files
```
examples/
├── scheduler.py                       (Main CLI entry)
├── basic_example.py                   (Usage example)
├── test_fake_response.py              (Test suite)
└── test_scheduler_settings.py         (Test suite)
```

---

## Proposed Organization

### Root Level (Essential Entry Points)
Keep at root level only the most essential documents that users see first:

```
NewsAgent/
├── README.md                          (Project overview - what is NewsAgent?)
├── QUICK_START.md                     (5-min getting started)
├── MODULE_CHECKING_GUIDE.md           (Understanding the codebase)
├── SETUP.md                           (Installation and configuration)
└── [Keep] CLAUDE.md                   (Development notes for Claude AI)
```

**Rationale**: Users landing on repo see these first. Keep count minimal for clarity.

### docs/ Directory (Detailed Documentation)
Organize feature-specific documentation logically:

```
docs/
├── ARCHITECTURE.md                    (System architecture overview)
├── API_REFERENCE.md                   (Complete API reference)
│
├── SCHEDULER/
│   ├── README.md                      (Scheduler overview)
│   ├── SETUP.md                       (API key configuration)
│   ├── SETTINGS.md                    (Configuration reference)
│   └── GUIDE.md                       (Complete usage guide)
│
├── FAKE_RESPONSE/
│   └── MANUAL.md                      (Fake response usage)
│
├── AGENTS/
│   ├── BOCHA.md                       (BOCHA agent guide)
│   ├── ARCHITECTURE.md                (Agent system design)
│   └── IMPLEMENTATION.md              (How to implement new agents)
│
└── DEVELOPMENT/
    ├── CONTRIBUTING.md                (How to contribute)
    ├── TESTING.md                     (Testing strategy)
    └── IMPLEMENTATION_SUMMARY.md      (Current implementation status)
```

**Rationale**: Organized by feature/topic for easy navigation.

### tests/ Directory (Test Suite)
Create formal test structure separate from examples:

```
tests/
├── __init__.py
├── test_fake_response.py              (Moved from examples/)
├── test_scheduler_settings.py         (Moved from examples/)
├── fixtures/
│   ├── __init__.py
│   └── sample_data.py                 (Test data and fixtures)
└── test_agents.py                     (New: Agent tests - when agents complete)
```

**Rationale**: Professional test organization. Examples/ stays for usage demos only.

### examples/ Directory (Cleaned)
Keep only usage examples, remove tests:

```
examples/
├── __init__.py
├── scheduler.py                       (Keep: Main CLI entry)
├── basic_example.py                   (Keep: Programmatic usage example)
└── [MOVE to tests/] test_*.py files
```

**Rationale**: Clear separation of concerns - examples show HOW to use, tests verify THAT it works.

---

## Migration Plan

### Step 1: Create Directory Structure
```bash
# Create new directories
mkdir -p docs/SCHEDULER
mkdir -p docs/FAKE_RESPONSE
mkdir -p docs/AGENTS
mkdir -p docs/DEVELOPMENT
mkdir -p tests/fixtures
```

### Step 2: Move & Consolidate Documentation

| Current Path | Action | New Path | Reason |
|--------------|--------|----------|--------|
| SCHEDULER_SETUP.md | Move | docs/SCHEDULER/SETUP.md | Consolidate scheduler docs |
| FAKE_RESPONSE_MANUAL.md | Move | docs/FAKE_RESPONSE/MANUAL.md | Organize by feature |
| docs/SCHEDULER_COMPLETE_GUIDE.md | Move | docs/SCHEDULER/GUIDE.md | Cleaner naming |
| docs/SCHEDULER_SETTINGS.md | Move | docs/SCHEDULER/SETTINGS.md | Consolidate scheduler docs |
| docs/SCHEDULER.md | Move | docs/SCHEDULER/README.md | Feature overview |
| docs/README_NEW_ARCHITECTURE.md | Move | docs/ARCHITECTURE.md | Root architecture doc |
| docs/IMPLEMENTATION_SUMMARY.md | Move | docs/DEVELOPMENT/IMPLEMENTATION_SUMMARY.md | Dev-related |
| CLAUDE.md | Keep | CLAUDE.md | Development guidance |

### Step 3: Move Test Files
```bash
# Move test files to formal tests/ directory
mv examples/test_fake_response.py tests/
mv examples/test_scheduler_settings.py tests/
```

### Step 4: Create New Overview Documents
Create these new files to provide better entry points:

- `SETUP.md` - consolidated setup instructions
- `QUICK_START.md` - 5-minute quick start
- `docs/SCHEDULER/README.md` - scheduler overview
- `docs/AGENTS/ARCHITECTURE.md` - agent system explanation
- `docs/AGENTS/IMPLEMENTATION.md` - guide for adding new agents
- `docs/DEVELOPMENT/TESTING.md` - testing strategy
- `tests/README.md` - test suite documentation

### Step 5: Update Import Paths
Update any documentation that references moved files:
- Update links in moved .md files
- Update import paths in test files (if any)

---

## New Directory Tree

After organization:

```
NewsAgent/
├── README.md                          # Project overview
├── QUICK_START.md                     # 5-min getting started
├── SETUP.md                           # Installation & config
├── MODULE_CHECKING_GUIDE.md           # Codebase guide
├── CLAUDE.md                          # Dev notes
│
├── src/                               # Source code (unchanged)
├── config/                            # Configuration (unchanged)
├── data/                              # Data directory (unchanged)
├── examples/                          # Usage examples (cleaned)
│   ├── __init__.py
│   ├── scheduler.py                   # Main CLI
│   └── basic_example.py               # Usage example
│
├── tests/                             # Test suite (new)
│   ├── __init__.py
│   ├── test_fake_response.py
│   ├── test_scheduler_settings.py
│   ├── fixtures/
│   │   ├── __init__.py
│   │   └── sample_data.py
│   └── README.md
│
├── docs/                              # Detailed documentation (reorganized)
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   │
│   ├── SCHEDULER/
│   │   ├── README.md
│   │   ├── SETUP.md
│   │   ├── SETTINGS.md
│   │   └── GUIDE.md
│   │
│   ├── FAKE_RESPONSE/
│   │   └── MANUAL.md
│   │
│   ├── AGENTS/
│   │   ├── BOCHA.md
│   │   ├── ARCHITECTURE.md
│   │   └── IMPLEMENTATION.md
│   │
│   └── DEVELOPMENT/
│       ├── CONTRIBUTING.md
│       ├── TESTING.md
│       └── IMPLEMENTATION_SUMMARY.md
│
└── .gitignore, pyproject.toml, etc.
```

---

## Benefits of This Organization

✅ **Clear Navigation**: Users quickly understand what's important
✅ **Scalable**: Easy to add new agents or features
✅ **Professional**: Follows Python project best practices
✅ **Maintainable**: Related docs grouped together
✅ **Cleaner Root**: Only essential entry points at top level
✅ **Separate Concerns**: Tests, examples, and docs are distinct

---

## File Changes Summary

### Files to Move
- SCHEDULER_SETUP.md → docs/SCHEDULER/SETUP.md
- FAKE_RESPONSE_MANUAL.md → docs/FAKE_RESPONSE/MANUAL.md
- docs/SCHEDULER_COMPLETE_GUIDE.md → docs/SCHEDULER/GUIDE.md
- docs/SCHEDULER_SETTINGS.md → docs/SCHEDULER/SETTINGS.md
- docs/SCHEDULER.md → docs/SCHEDULER/README.md
- docs/README_NEW_ARCHITECTURE.md → docs/ARCHITECTURE.md
- docs/IMPLEMENTATION_SUMMARY.md → docs/DEVELOPMENT/IMPLEMENTATION_SUMMARY.md
- examples/test_fake_response.py → tests/test_fake_response.py
- examples/test_scheduler_settings.py → tests/test_scheduler_settings.py

### Files to Create
- SETUP.md (consolidated setup guide)
- QUICK_START.md (5-min quick start)
- docs/SCHEDULER/README.md (scheduler overview)
- docs/API_REFERENCE.md (complete API reference)
- docs/AGENTS/ARCHITECTURE.md (agent system design)
- docs/AGENTS/IMPLEMENTATION.md (how to add agents)
- docs/AGENTS/BOCHA.md (BOCHA agent documentation)
- docs/DEVELOPMENT/CONTRIBUTING.md (contribution guidelines)
- docs/DEVELOPMENT/TESTING.md (testing strategy)
- tests/__init__.py (package init)
- tests/README.md (test suite overview)
- tests/fixtures/__init__.py
- tests/fixtures/sample_data.py (test fixtures)

### Files to Keep
- README.md (project overview)
- MODULE_CHECKING_GUIDE.md (codebase understanding)
- CLAUDE.md (development notes)
- examples/scheduler.py (main CLI entry)
- examples/basic_example.py (usage example)

### Files to Remove (Old Location)
- All files listed in "Files to Move" from their old locations

---

## Execution Steps

### Phase 1: Create New Structure
```bash
mkdir -p docs/SCHEDULER docs/FAKE_RESPONSE docs/AGENTS docs/DEVELOPMENT
mkdir -p tests/fixtures
touch tests/__init__.py tests/fixtures/__init__.py
```

### Phase 2: Move Documentation Files
```bash
# Create consolidated SETUP.md (combining setup info)
# Move scheduler docs
mv SCHEDULER_SETUP.md docs/SCHEDULER/SETUP.md
mv docs/SCHEDULER_COMPLETE_GUIDE.md docs/SCHEDULER/GUIDE.md
mv docs/SCHEDULER_SETTINGS.md docs/SCHEDULER/SETTINGS.md
mv docs/SCHEDULER.md docs/SCHEDULER/README.md

# Move feature docs
mv FAKE_RESPONSE_MANUAL.md docs/FAKE_RESPONSE/MANUAL.md
mv docs/README_NEW_ARCHITECTURE.md docs/ARCHITECTURE.md
mv docs/IMPLEMENTATION_SUMMARY.md docs/DEVELOPMENT/IMPLEMENTATION_SUMMARY.md
```

### Phase 3: Move Test Files
```bash
mv examples/test_fake_response.py tests/
mv examples/test_scheduler_settings.py tests/
```

### Phase 4: Create New Overview Documents
- [ ] Create QUICK_START.md
- [ ] Create SETUP.md
- [ ] Create docs/API_REFERENCE.md
- [ ] Create docs/SCHEDULER/README.md
- [ ] Create docs/AGENTS/ARCHITECTURE.md
- [ ] Create docs/AGENTS/IMPLEMENTATION.md
- [ ] Create docs/AGENTS/BOCHA.md
- [ ] Create docs/DEVELOPMENT/CONTRIBUTING.md
- [ ] Create docs/DEVELOPMENT/TESTING.md
- [ ] Create tests/README.md
- [ ] Create tests/fixtures/sample_data.py

### Phase 5: Update Documentation Links
- Update internal links in moved .md files
- Update README.md with new documentation structure

---

## Impact on Test Running

### Before (Old)
```bash
python -m examples.test_fake_response
python -m examples.test_scheduler_settings
```

### After (New)
```bash
python -m tests.test_fake_response
python -m tests.test_scheduler_settings

# Or using pytest (recommended)
pytest tests/
```

---

## Recommendation

**Proceed with this organization** to:
1. Keep root level clean and uncluttered
2. Group related documentation together
3. Follow Python best practices for test organization
4. Make the project more professional and maintainable
5. Simplify navigation for new contributors

---

## Questions to Consider

Before proceeding, confirm:

1. ✅ Agree to move test files from examples/ to tests/?
2. ✅ Agree to move documentation to docs/ subdirectories?
3. ✅ Want to create new overview documents (QUICK_START.md, etc.)?
4. ✅ Want to keep CLAUDE.md at root level for development notes?
5. ✅ Ready to proceed with all file movements?

---

## Next Steps

1. **Review this plan** with the team/user
2. **Confirm all items** above
3. **Execute Phase 1-5** in order
4. **Update internal links** in documentation
5. **Verify tests still run** from new location
6. **Clean up** - remove old empty files/directories
7. **Commit** - single commit with all organization changes

