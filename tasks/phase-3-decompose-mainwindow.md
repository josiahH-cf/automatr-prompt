# Tasks: Phase 3 — Decompose MainWindow

**Spec:** /specs/app-split-refactor.md

## Status

- Total: 6
- Complete: 6
- Remaining: 0

## Prerequisites

- Phase 2 complete (baseline tests provide safety net)

## Task List

### Task 1: Extract TemplateTreeWidget

- **Files:** New: `automatr/ui/template_tree.py`. Modified: `automatr/ui/main_window.py`
- **Done when:** A new `TemplateTreeWidget(QWidget)` class exists containing: tree view setup, context menu (edit, improve, version history, delete), folder operations, template selection signal, drag-and-drop (if any). `MainWindow` creates a `TemplateTreeWidget` instance instead of inline tree setup. All tree-related private methods moved out of `MainWindow`. Widget emits signals: `template_selected(Template)`, `template_deleted(str)`, `edit_requested(Template)`, `improve_requested(Template)`. File ≤300 lines. All existing tests pass
- **Criteria covered:** AC-5
- **Status:** [x] Complete

### Task 2: Extract VariableFormWidget

- **Files:** New: `automatr/ui/variable_form.py`. Modified: `automatr/ui/main_window.py`
- **Done when:** A new `VariableFormWidget(QWidget)` class exists containing: dynamic form generation from `Template.variables`, value collection, form clearing, "Render with AI" and "Copy Template" buttons (or signals for them). `MainWindow` replaces inline variable panel setup with this widget. Widget provides: `get_values() -> dict`, `set_template(Template)`, signals for render/copy actions. File ≤300 lines. All existing tests pass
- **Criteria covered:** AC-5
- **Status:** [x] Complete

### Task 3: Extract OutputPaneWidget

- **Files:** New: `automatr/ui/output_pane.py`. Modified: `automatr/ui/main_window.py`
- **Done when:** A new `OutputPaneWidget(QWidget)` class exists containing: text display area, copy/clear/stop buttons, streaming text append method, progress indication. `GenerationWorker` QThread either lives in this module or in a separate `automatr/ui/workers.py`. Widget provides: `append_text(str)`, `clear()`, `set_streaming(bool)`, signals: `stop_requested()`. File ≤300 lines. All existing tests pass
- **Criteria covered:** AC-5
- **Status:** [x] Complete

### Task 4: Extract LLM toolbar/status widget

- **Files:** New: `automatr/ui/llm_toolbar.py`. Modified: `automatr/ui/main_window.py`
- **Done when:** A new `LLMToolbar(QWidget)` or `LLMStatusBar(QWidget)` class encapsulates: start/stop server buttons, status indicator (Connected/Not Running), model selection combo. Widget provides: `set_status(str)`, `set_models(list)`, signals: `start_requested()`, `stop_requested()`, `model_selected(str)`. `ModelCopyWorker` moves here or to `workers.py`. File ≤300 lines. All existing tests pass
- **Criteria covered:** AC-5
- **Status:** [x] Complete

### Task 5: Slim down MainWindow to ≤300 lines

- **Files:** `automatr/ui/main_window.py`
- **Done when:** `MainWindow` is a thin shell that: (1) creates the 4 extracted widgets, (2) wires their signals together, (3) sets up menus (File, LLM, Help), (4) manages window state persistence (geometry, splitter sizes), (5) handles font scaling. Total file ≤300 lines. `run_gui()` still works. All existing tests pass
- **Criteria covered:** AC-5
- **Status:** [x] Complete

### Task 6: Add widget-level tests

- **Files:** `tests/test_widgets.py` (or split per widget)
- **Done when:** Tests exist for: (1) `TemplateTreeWidget` populates from template list, emits `template_selected`, (2) `VariableFormWidget` generates correct form fields from template variables, `get_values()` returns entered values, (3) `OutputPaneWidget` appends text correctly, emits `stop_requested`. Minimum 6 test functions. Uses `pytest-qt` `qtbot` for widget testing. All tests pass
- **Criteria covered:** AC-5, AC-4
- **Status:** [x] Complete

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-5 | Tasks 1-5: `wc -l` on each new file ≤300. `wc -l` on `main_window.py` ≤300 |
| AC-5 | Task 6: widget-level tests confirm extracted components work independently |

## Definition of Done

- `automatr` launches and all features work identically to pre-decomposition
- No Python file in `ui/` exceeds 300 lines (except possibly `template_generate.py` and `template_improve.py` which are untouched in this phase)
- `MainWindow` delegates to widgets via signals/slots — no direct manipulation of child widget internals
- All Phase 2 tests + new widget tests pass
- `ruff check .` passes

## Rollback Strategy

Each task is one commit. If a widget extraction breaks something, revert that commit and the wiring. The baseline tests from Phase 2 catch regressions immediately.

## Notes

- The `_setup_template_panel()`, `_setup_variable_panel()`, `_setup_output_panel()` method groups in `MainWindow` map naturally to the extracted widgets — follow the existing code groupings
- `template_generate.py` (604 lines) and `template_improve.py` (436 lines) are dialog-based and not part of `MainWindow`'s monolith problem — leave them for a future cleanup pass
- Font scaling (`_update_font_size()`) should remain in `MainWindow` since it applies globally across all widgets

## Session Log

<!-- Append after each session: date, completed, blockers -->
