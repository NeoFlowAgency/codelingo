from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass

FORBIDDEN = ["import os", "import sys", "subprocess", "open(", "eval(", "exec(", "__import__"]


@dataclass
class EvaluationResult:
    is_correct: bool
    output: str
    feedback: str


def execute_python(code: str) -> tuple[bool, str]:
    lower = code.lower()
    for item in FORBIDDEN:
        if item in lower:
            return False, f"Instruction interdite détectée: {item}"

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=True) as temp:
        temp.write(code)
        temp.flush()
        try:
            run = subprocess.run(["python", temp.name], capture_output=True, text=True, timeout=2, check=False)
        except subprocess.TimeoutExpired:
            return False, "Le programme a dépassé la limite de temps (2s)."

    output = (run.stdout or "").strip()
    if run.returncode != 0:
        err = (run.stderr or "Erreur inconnue").strip()
        return False, err
    return True, output


def grade_submission(user_code: str, expected_output: str) -> EvaluationResult:
    success, output = execute_python(user_code)
    if not success:
        return EvaluationResult(False, output, "Ton code contient une erreur, corrige puis réessaie.")

    if output.strip() == expected_output.strip():
        return EvaluationResult(True, output, "Parfait ! Exercice validé ✅")

    return EvaluationResult(False, output, f"Sortie attendue: {expected_output!r}.")
