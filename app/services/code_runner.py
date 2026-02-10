from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass

BLOCKED_PATTERNS = [
    "import os",
    "import sys",
    "subprocess",
    "open(",
    "__import__",
    "eval(",
    "exec(",
]


@dataclass
class RunResult:
    success: bool
    output: str
    error: str | None = None


def run_python_sandbox(code: str) -> RunResult:
    lowered = code.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lowered:
            return RunResult(False, "", f"Instruction interdite détectée: {pattern}")

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=True) as tmp:
        tmp.write(code)
        tmp.flush()
        try:
            proc = subprocess.run(
                ["python", "-I", tmp.name],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return RunResult(False, "", "Temps dépassé (2s max).")

    if proc.returncode != 0:
        return RunResult(False, proc.stdout.strip(), proc.stderr.strip() or "Erreur d'exécution")
    return RunResult(True, proc.stdout.strip(), None)


def validate_exercise(code: str, exercise: dict) -> tuple[bool, str, str]:
    result = run_python_sandbox(code)
    if not result.success:
        return False, result.output, result.error or "Erreur"

    validator = exercise.get("validator")
    if validator == "expect_output":
        expected = exercise.get("expected_output", "").strip()
        if result.output.strip() == expected:
            return True, result.output, "Bravo, bonne réponse !"
        return False, result.output, f"Sortie attendue: {expected}"

    if validator == "expect_lines":
        expected_lines = [line.strip() for line in exercise.get("expected_lines", [])]
        got_lines = [line.strip() for line in result.output.splitlines() if line.strip()]
        if got_lines == expected_lines:
            return True, result.output, "Parfait, les lignes sont correctes."
        return False, result.output, f"Lignes attendues: {expected_lines}"

    return False, result.output, "Validateur inconnu"
