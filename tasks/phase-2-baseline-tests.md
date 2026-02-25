# Tasks: Phase 2 — Baseline Tests for automatr-prompt

**Spec:** /specs/app-split-refactor.md

## Status

- Total: 6
- Complete: 6
- Remaining: 0

## Prerequisites

- Phase 1 complete (Espanso code removed, clean app launches)

## Task List

### Task 1: Set up test infrastructure

- **Files:** `tests/conftest.py`, `tests/__init__.py`
- **Done when:** `conftest.py` exists with shared fixtures: (1) `tmp_config_dir` (temporary config directory with default config.json), (2) `tmp_templates_dir` (temporary templates directory with 2-3 sample template JSON files), (3) `sample_template` (a `Template` object with variables for testing). `pytest` discovers and runs an empty test. CI workflow runs tests
- **Criteria covered:** AC-4 (infrastructure)
- **Status:** [x] Complete

### Task 2: Test TemplateManager CRUD and versioning

- **Files:** `tests/test_templates.py`
- **Done when:** Tests exist and pass for: (1) load templates from directory, (2) save a new template (creates JSON file), (3) update an existing template, (4) delete a template, (5) version creation on save, (6) version listing and restore, (7) folder creation and template movement, (8) `Template.render()` with variable substitution, (9) template with unknown fields (e.g., `"trigger"`) loads without error. Minimum 9 test functions
- **Criteria covered:** AC-4
- **Status:** [x] Complete — 17 tests

### Task 3: Test ConfigManager

- **Files:** `tests/test_config.py`
- **Done when:** Tests exist and pass for: (1) default config creation when no file exists, (2) load existing config.json, (3) save config and verify JSON output, (4) `update()` with dotted keys (e.g., `llm.model_path`), (5) unknown keys in JSON are ignored (backward compat), (6) platform detection returns valid values. Minimum 6 test functions
- **Criteria covered:** AC-4
- **Status:** [x] Complete — 13 tests. Bug documented: unknown nested keys inside 'llm'/'ui' sections cause TypeError (caught by ConfigManager.load(), returns defaults).

### Task 4: Test LLMClient (mocked HTTP)

- **Files:** `tests/test_llm_client.py`
- **Done when:** Tests exist and pass (using `unittest.mock.patch` on `requests`) for: (1) health check returns connected/disconnected, (2) completion request sends correct payload, (3) completion response parsed correctly, (4) streaming response handled (mocked SSE chunks), (5) connection error handled gracefully (no crash). Minimum 5 test functions
- **Criteria covered:** AC-4
- **Status:** [x] Complete — 9 tests

### Task 5: Test LLMServerManager (mocked filesystem)

- **Files:** `tests/test_llm_server.py`
- **Done when:** Tests exist and pass for: (1) `find_server_binary()` finds binary at configured path, (2) `find_server_binary()` falls back through search locations, (3) `find_server_binary()` returns None when nothing found, (4) `find_models()` discovers `.gguf` files in model directory, (5) `find_models()` returns empty list when no models exist. Minimum 5 test functions
- **Criteria covered:** AC-4
- **Status:** [x] Complete — 9 tests. Note: tests patch Path.home() to avoid finding real host binaries.

### Task 6: Test FeedbackManager and prompt builders

- **Files:** `tests/test_feedback.py`
- **Done when:** Tests exist and pass for: (1) save feedback entry to disk, (2) load feedback entries, (3) `build_improvement_prompt()` returns non-empty string with template content embedded, (4) `build_generation_prompt()` returns non-empty string with description embedded. Minimum 4 test functions
- **Criteria covered:** AC-4
- **Status:** [x] Complete — 10 tests

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-4 | All tasks: `pytest` runs all tests, all pass, CI green |

## Definition of Done

- `pytest` runs ≥29 test functions with 0 failures
- `ruff check .` passes (no lint errors in test files)
- All tests are deterministic — no temp file leaks, no timing dependencies
- Each test file has a module docstring describing what it covers

## Rollback Strategy

Tests are additive — they don't change production code. If a test reveals a bug, document it as a separate issue; don't fix production code in this phase.

## Session Log

<!-- Append after each session: date, completed, blockers -->

### 2026-02-25
- Completed all 6 tasks in a single session.
- 58 tests total, all passing. ruff clean.
- Bug documented in Task 3: `Config.from_dict()` passes `**data` to dataclass
  constructors — unknown nested keys in 'llm'/'ui' sections raise TypeError;
  `ConfigManager.load()` catches this and returns defaults. Needs a separate fix.
- Task 5 required patching `Path.home()` because a real `llama-server` binary
  was installed on the dev machine at `~/.local/share/automatr/llama.cpp/...`.
