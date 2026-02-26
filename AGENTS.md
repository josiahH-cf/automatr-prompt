# Project

- Project name: Automatr Prompt
- Description: A local-model prompt optimizer desktop app with reusable templates and llama.cpp integration. No cloud, no API keys.
- Primary language/framework: Python with PyQt6
- Scope: Local prompt optimization, template management, llama.cpp LLM runtime
- Non-goals: Espanso/text-expander integration, cloud LLM APIs, multi-tenant, mobile/web, PyPI publishing

# Build

- Install: `./install.sh` (recommended) or `pip install -e .` / `pip install -e .[dev]` for development
- Build: `not applicable` (setuptools package, no separate build step required for local development)
- Test (all): `pytest`
- Test (single): `pytest path/to/test_file.py::test_name`
- Lint: `ruff check .`
- Format: `black .`
- Type-check: `not applicable`

# Architecture

- `automatr/`: Main Python package and app entrypoint.
- `automatr/core/`: Core configuration, template handling, and user feedback utilities.
- `automatr/integrations/`: LLM runtime integration (llama.cpp server lifecycle, model management).
- `automatr/ui/`: PyQt6 user interface — decomposed into focused widgets:
  - `main_window.py`: Top-level window composing mixins for template actions, generation, and window state.
  - `template_tree.py`: Sidebar tree for browsing and selecting templates.
  - `template_editor.py`: Template content editor widget.
  - `variable_form.py`: Form for filling template variables.
  - `output_pane.py`: Generated text output display.
  - `llm_toolbar.py`: Server controls and status display.
  - `llm_settings.py`: LLM configuration dialog.
  - `template_generate.py`, `template_improve.py`: Template generation and improvement dialogs.
  - `theme.py`: Dark/light theme stylesheets.
  - `workers.py`: Background QThread workers for generation and model operations.
- `templates/`: Built-in prompt template JSON files shipped with the app.
- `scripts/`: Repository utility scripts (maintenance and template tooling).
- `.github/`: CI automation, issue/PR templates, and agent guidance files.
- `workflow/`, `tasks/`, `specs/`, `decisions/`: Development lifecycle docs, execution plans, specs, and decision records.

# Conventions

- Functions and variables: standard Python `snake_case` (classes use `PascalCase`)
- Files and directories: standard Python module naming with lowercase and `snake_case` where needed
- Prefer explicit error handling over silent failures
- No dead code — remove unused imports, variables, and functions
- Every public function has a doc comment
- No hardcoded secrets, URLs, or environment-specific values

# Testing

- Write tests before implementation
- Place tests under `/tests/` using `test_*.py` naming
- For UI behavior, use `pytest-qt` and prefer deterministic widget-level tests over timing-dependent flows
- Each acceptance criterion requires at least one test
- Do not modify existing tests to accommodate new code — fix the implementation
- Run the full test suite before committing
- Tests must be deterministic — no flaky tests in the main suite

# Planning

- Features with more than 3 implementation steps require a written plan
- Plans go in `/tasks/[feature-name].md` or as an ExecPlan per `/.codex/PLANS.md`
- Plans are living documents — update progress, decisions, and surprises as work proceeds
- A plan that cannot fit in 5 tasks indicates the feature should be split. Call this out.
- Small-fix fast path: if a change is <= 3 files and has no behavior change, a full spec/task lifecycle is optional; still document intent in the PR and run lint + relevant tests.

# Dependencies

- Add dependencies only when standard library cannot solve the problem
- Pin versions explicitly
- Security audit new dependencies before adding

# Commits

- One logical change per commit
- Present-tense imperative subject line, under 72 characters
- Reference the spec or task file in the commit body when applicable
- Commit after each completed task, not after all tasks

# Branches

- Branch from the latest target branch immediately before starting work
- One feature per branch
- Delete after merge
- Never commit directly to the target branch
- Naming: `[type]/[issue-id]-[slug]` (e.g., `feat/42-user-auth`, `fix/87-null-check`)

# Worktrees

- Use git worktrees for concurrent features across agents
- Worktree root: `.trees/[branch-name]/`
- Each worktree is isolated: agents operate only within their assigned worktree
- Artifacts (specs, tasks, decisions) live in the main worktree and are shared read-only
- Never switch branches inside a worktree — create a new one

# Pull Requests

- Link to the spec file
- Diff under 300 lines; if larger, split the feature
- All CI checks pass before requesting review
- PR description states: what changed, why, how to verify

# Review

- Reviewable in under 15 minutes
- Tests cover every acceptance criterion
- No unrelated changes in the diff
- Cross-agent review encouraged: use a different model than the one that wrote the code

# Security

- No secrets in code or instruction files
- Use environment variables for all credentials
- Sanitize all external input
- Log security-relevant events
