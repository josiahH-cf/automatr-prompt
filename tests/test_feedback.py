"""Tests for automatr.core.feedback — FeedbackManager and prompt builder functions.

Covers: saving a feedback entry to disk, loading entries back, and verifying
that build_improvement_prompt() and build_generation_prompt() return non-empty
strings containing the expected input content.

FeedbackManager is isolated by patching automatr.core.feedback.get_config_dir
so it writes to a tmp_path instead of the real ~/.config/automatr directory.
"""

from pathlib import Path
from unittest.mock import patch

from automatr.core.feedback import (
    FeedbackManager,
    build_generation_prompt,
    build_improvement_prompt,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_manager(tmp_path: Path) -> FeedbackManager:
    """Return a FeedbackManager that stores feedback.json inside tmp_path."""
    with patch("automatr.core.feedback.get_config_dir", return_value=tmp_path):
        mgr = FeedbackManager()
    return mgr


# ---------------------------------------------------------------------------
# 1. Save feedback entry to disk
# ---------------------------------------------------------------------------


def test_add_feedback_creates_json_file(tmp_path: Path) -> None:
    """FeedbackManager.add() persists a feedback entry to feedback.json."""
    mgr = _make_manager(tmp_path)
    mgr.add(
        template_name="Code Review",
        prompt="Review this code: x = 1",
        output="Looks good.",
        rating="up",
    )

    feedback_file = tmp_path / "feedback.json"
    assert feedback_file.exists()


def test_add_feedback_stores_entry_fields(tmp_path: Path) -> None:
    """add() stores template_name, rating, and output_snippet correctly."""
    mgr = _make_manager(tmp_path)
    entry = mgr.add(
        template_name="Summarize",
        prompt="Summarize: lorem ipsum",
        output="Short summary.",
        rating="down",
        correction="Too brief.",
    )

    assert entry.template_name == "Summarize"
    assert entry.rating == "down"
    assert entry.correction == "Too brief."
    assert entry.output_snippet == "Short summary."


def test_add_multiple_feedback_entries(tmp_path: Path) -> None:
    """Multiple add() calls accumulate entries."""
    mgr = _make_manager(tmp_path)
    mgr.add("T1", "prompt A", "output A", "up")
    mgr.add("T2", "prompt B", "output B", "down")

    entries = mgr.get_all()
    assert len(entries) == 2


# ---------------------------------------------------------------------------
# 2. Load feedback entries
# ---------------------------------------------------------------------------


def test_load_feedback_on_new_manager_reads_persisted_entries(tmp_path: Path) -> None:
    """A second FeedbackManager instance reads entries saved by the first."""
    mgr1 = _make_manager(tmp_path)
    mgr1.add("Review", "prompt", "output", "up")

    # Construct a fresh manager pointing at the same directory
    with patch("automatr.core.feedback.get_config_dir", return_value=tmp_path):
        mgr2 = FeedbackManager()

    entries = mgr2.get_all()
    assert len(entries) == 1
    assert entries[0].template_name == "Review"
    assert entries[0].rating == "up"


def test_get_by_template_filters_correctly(tmp_path: Path) -> None:
    """get_by_template() returns only entries matching the given template name."""
    mgr = _make_manager(tmp_path)
    mgr.add("TemplateA", "p1", "o1", "up")
    mgr.add("TemplateB", "p2", "o2", "down")
    mgr.add("TemplateA", "p3", "o3", "up")

    a_entries = mgr.get_by_template("TemplateA")
    assert len(a_entries) == 2
    assert all(e.template_name == "TemplateA" for e in a_entries)


def test_feedback_survives_empty_correction(tmp_path: Path) -> None:
    """add() with an empty correction string stores None, not an empty string."""
    mgr = _make_manager(tmp_path)
    entry = mgr.add("T", "p", "o", "down", correction="   ")

    assert entry.correction is None


# ---------------------------------------------------------------------------
# 3. build_improvement_prompt() returns non-empty string with template content
# ---------------------------------------------------------------------------


def test_build_improvement_prompt_contains_template_content() -> None:
    """build_improvement_prompt() returns a prompt embedding the template content."""
    content = "Write a summary of {{text}}"
    result = build_improvement_prompt(
        template_content=content,
        refinements=["Make it shorter"],
    )

    assert isinstance(result, str)
    assert len(result) > 0
    assert content in result


def test_build_improvement_prompt_embeds_refinements() -> None:
    """build_improvement_prompt() includes the supplied refinement feedback."""
    result = build_improvement_prompt(
        template_content="Some template",
        refinements=["Add more detail", "Fix grammar"],
    )

    assert "Add more detail" in result
    assert "Fix grammar" in result


# ---------------------------------------------------------------------------
# 4. build_generation_prompt() returns non-empty string with description
# ---------------------------------------------------------------------------


def test_build_generation_prompt_contains_description() -> None:
    """build_generation_prompt() returns a prompt embedding the description."""
    description = "A template for writing commit messages"
    result = build_generation_prompt(
        description=description,
        expected_variables=["branch", "changes"],
    )

    assert isinstance(result, str)
    assert len(result) > 0
    assert description in result


def test_build_generation_prompt_with_no_variables_returns_string() -> None:
    """build_generation_prompt() handles empty variables list gracefully."""
    result = build_generation_prompt(
        description="Generic helper template",
        expected_variables=[],
    )

    assert isinstance(result, str)
    assert len(result) > 0
