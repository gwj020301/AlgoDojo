"""Per-language adapters: how to compile and run a submission.

Each adapter answers three questions for the in-container runner:

- ``source_filename``: what to name the user's source file.
- ``compile_commands``: commands to run before execution. An empty list means
  "no separate compile step". A non-zero exit from any compile command is a
  Compile Error (CE).
- ``run_command``: the argv used to execute the (compiled) program. The program
  reads a test case from stdin and writes its answer to stdout.

The execution model is whole-program stdin -> stdout (design.md 3.3):
- Python: a quick ``py_compile`` syntax check (SyntaxError -> CE), then run
  ``python3 solution.py``.
- TypeScript: type-check + transpile with the TypeScript compiler (``tsc``)
  to JS (errors -> CE), then run ``node solution.js``.
"""

from __future__ import annotations

from dataclasses import dataclass

from dojo_judge.types import Language


@dataclass(frozen=True)
class LanguageAdapter:
    name: str
    source_filename: str

    def compile_commands(self, work_dir: str, out_dir: str) -> list[list[str]]:
        raise NotImplementedError

    def run_command(self, work_dir: str, out_dir: str) -> list[str]:
        raise NotImplementedError


class PythonAdapter(LanguageAdapter):
    def __init__(self) -> None:
        super().__init__(name=Language.PYTHON, source_filename="solution.py")

    def compile_commands(self, work_dir: str, out_dir: str) -> list[list[str]]:
        src = f"{work_dir}/{self.source_filename}"
        # Syntax check WITHOUT writing bytecode (the /work mount is read-only, and
        # py_compile would try to create /work/__pycache__). ast.parse raises
        # SyntaxError (non-zero exit) which the runner classifies as CE.
        return [
            [
                "python3",
                "-c",
                "import ast,sys; ast.parse(open(sys.argv[1]).read(), sys.argv[1])",
                src,
            ]
        ]

    def run_command(self, work_dir: str, out_dir: str) -> list[str]:
        return ["python3", f"{work_dir}/{self.source_filename}"]


class TypeScriptAdapter(LanguageAdapter):
    def __init__(self) -> None:
        super().__init__(name=Language.TYPESCRIPT, source_filename="solution.ts")

    def compile_commands(self, work_dir: str, out_dir: str) -> list[list[str]]:
        src = f"{work_dir}/{self.source_filename}"
        # Type-check + transpile to JS in the writable out_dir. Type errors fail
        # compilation (-> CE). @types/node is installed in the image so beginner
        # solutions can use node globals (require / process / stdin / console).
        return [
            [
                "tsc",
                src,
                "--outDir",
                out_dir,
                "--target",
                "ES2020",
                "--module",
                "commonjs",
                "--moduleResolution",
                "node",
                "--types",
                "node",
                "--typeRoots",
                "/usr/local/lib/node_modules/@types",
                "--skipLibCheck",
                "--lib",
                "ES2020",
            ]
        ]

    def run_command(self, work_dir: str, out_dir: str) -> list[str]:
        return ["node", f"{out_dir}/solution.js"]


_ADAPTERS: dict[str, LanguageAdapter] = {
    Language.PYTHON: PythonAdapter(),
    Language.TYPESCRIPT: TypeScriptAdapter(),
}


def get_adapter(language: str) -> LanguageAdapter:
    """Return the adapter for a language, or raise ValueError if unsupported."""
    try:
        return _ADAPTERS[language]
    except KeyError:
        raise ValueError(f"Unsupported language: {language!r}") from None
