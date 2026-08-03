#!/usr/bin/env python3
"""Ask Claude Code for an isolated, read-only second opinion."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
DEFAULT_MODEL = "claude-fable-5"
DEFAULT_EFFORT = "high"
DEFAULT_BUDGET_USD = 4.0
READ_ONLY_TOOLS = "Read,Grep,Glob"
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")


def positive_amount(value: str) -> float:
    amount = float(value)
    if amount <= 0:
        raise argparse.ArgumentTypeError("budget must be greater than zero")
    return amount


def model_name(value: str) -> str:
    if not MODEL_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "model must be a Claude alias or full model ID"
        )
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pipe a prompt from stdin to the Claude Code CLI in isolated, "
            "read-only print mode."
        )
    )
    parser.add_argument(
        "--model",
        type=model_name,
        default=DEFAULT_MODEL,
        help=f"Claude model alias or full ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--effort",
        choices=EFFORT_LEVELS,
        default=DEFAULT_EFFORT,
        help=f"reasoning effort (default: {DEFAULT_EFFORT})",
    )
    parser.add_argument(
        "--max-budget-usd",
        type=positive_amount,
        default=DEFAULT_BUDGET_USD,
        help=f"hard request budget ceiling (default: {DEFAULT_BUDGET_USD:g})",
    )
    return parser.parse_args()


def resolve_claude_command() -> list[str]:
    executable = shutil.which("claude")
    if executable is None:
        raise RuntimeError("Claude Code CLI was not found on PATH")

    path = Path(executable)
    if path.suffix.lower() == ".ps1":
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell is None:
            raise RuntimeError("Claude resolves to a PowerShell script, but no PowerShell executable was found")
        return [powershell, "-NoProfile", "-File", str(path)]

    return [str(path)]


def read_prompt() -> str:
    prompt = sys.stdin.read()
    if not prompt.strip():
        raise ValueError("prompt must be provided through stdin")
    return prompt


def optional_field(payload: dict[str, Any], name: str) -> Any:
    value = payload.get(name)
    return value if value not in ("", None) else None


def run() -> int:
    args = parse_args()

    try:
        prompt = read_prompt()
        command = resolve_claude_command()
    except (RuntimeError, ValueError) as error:
        print(f"ask-claude: {error}", file=sys.stderr)
        return 2

    command.extend(
        [
            "-p",
            "--model",
            args.model,
            "--effort",
            args.effort,
            "--output-format",
            "json",
            "--no-session-persistence",
            "--safe-mode",
            "--permission-mode",
            "dontAsk",
            "--tools",
            READ_ONLY_TOOLS,
            "--allowed-tools",
            READ_ONLY_TOOLS,
            "--max-budget-usd",
            format(args.max_budget_usd, "g"),
        ]
    )

    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        if completed.stderr:
            print(completed.stderr.rstrip(), file=sys.stderr)
        if completed.stdout:
            print(completed.stdout.rstrip(), file=sys.stderr)
        return completed.returncode

    try:
        claude_result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        print(f"ask-claude: Claude returned invalid JSON: {error}", file=sys.stderr)
        return 1

    output = {
        "requested_model": args.model,
        "requested_effort": args.effort,
        "reported_model": optional_field(claude_result, "model"),
        "num_turns": optional_field(claude_result, "num_turns"),
        "duration_ms": optional_field(claude_result, "duration_ms"),
        "total_cost_usd": optional_field(claude_result, "total_cost_usd"),
        "permission_denials": claude_result.get("permission_denials") or [],
        "answer": claude_result.get("result"),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
