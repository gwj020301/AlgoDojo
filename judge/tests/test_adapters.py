"""Tests for language adapters."""

import pytest
from dojo_judge.adapters import PythonAdapter, TypeScriptAdapter, get_adapter
from dojo_judge.types import Language


def test_get_adapter_returns_correct_type() -> None:
    assert isinstance(get_adapter(Language.PYTHON), PythonAdapter)
    assert isinstance(get_adapter(Language.TYPESCRIPT), TypeScriptAdapter)


def test_unsupported_language_raises() -> None:
    with pytest.raises(ValueError):
        get_adapter("ruby")


def test_python_adapter_commands() -> None:
    a = PythonAdapter()
    assert a.source_filename == "solution.py"
    compile_cmds = a.compile_commands("/work", "/tmp/judge")
    # Single syntax-check command that does not write bytecode, ending in the src.
    assert len(compile_cmds) == 1
    assert compile_cmds[0][0] == "python3"
    assert compile_cmds[0][-1] == "/work/solution.py"
    assert "ast.parse" in compile_cmds[0][2]
    assert a.run_command("/work", "/tmp/judge") == ["python3", "/work/solution.py"]


def test_typescript_adapter_commands() -> None:
    a = TypeScriptAdapter()
    assert a.source_filename == "solution.ts"
    compile_cmds = a.compile_commands("/work", "/tmp/judge")
    # Single tsc invocation producing JS into the writable out dir.
    assert len(compile_cmds) == 1
    assert compile_cmds[0][0] == "tsc"
    assert "/work/solution.ts" in compile_cmds[0]
    assert a.run_command("/work", "/tmp/judge") == ["node", "/tmp/judge/solution.js"]
