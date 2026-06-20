"""Tests for output normalization and comparison."""

from dojo_judge.compare import normalize_output, outputs_match


def test_trailing_whitespace_and_newlines_are_ignored() -> None:
    assert outputs_match("4\n", "4")
    assert outputs_match("4  \n", "4")
    assert outputs_match("4\n\n\n", "4")
    assert outputs_match("hello \nworld\n", "hello\nworld")


def test_crlf_normalized() -> None:
    assert outputs_match("a\r\nb\r\n", "a\nb")


def test_real_mismatch_is_detected() -> None:
    assert not outputs_match("4", "5")
    assert not outputs_match("1 2", "1  2")  # internal whitespace differs


def test_normalize_output_examples() -> None:
    assert normalize_output("  a \n b \n\n") == "  a\n b"
    assert normalize_output("") == ""
