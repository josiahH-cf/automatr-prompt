# Tests

This project uses `pytest` for tests and `pytest-qt` for UI-focused behavior.

## Layout

- Put all new tests under `/tests/`.
- Name files `test_*.py`.
- Keep tests deterministic (no flaky timing assumptions).

## Commands

- Run all tests: `pytest`
- Run one file: `pytest tests/test_example.py`
- Run one test: `pytest tests/test_example.py::test_case_name`

## Agent Notes

- For feature work, write failing tests first when practical.
- Map tests to spec acceptance criteria in `/specs/[feature-name].md`.
- Prefer focused unit/widget tests before broader integration coverage.
