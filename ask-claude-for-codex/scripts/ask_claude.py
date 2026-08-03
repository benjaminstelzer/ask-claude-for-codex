#!/usr/bin/env python3
"""Ask Claude Code for a read-only second opinion."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
READ_ONLY_TOOLS = "Read,Grep,Glob"
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
CONFIG_KEYS = {
    "model",
    "effort",
    "max_budget_usd",
    "session_persistence",
    "customizations",
}


def positive_amount(value: str) -> float:
    amount = float(value)
    if not math.isfinite(amount) or amount <= 0:
        raise argparse.ArgumentTypeError("budget must be greater than zero")
    return amount


def model_name(value: str) -> str:
    if not MODEL_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "model must be a Claude alias or full model ID"
        )
    return value


def non_empty_value(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def load_config(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"cannot read config {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in config {path}: {error}") from error

    if not isinstance(payload, dict):
        raise ValueError(f"config {path} must contain a JSON object")

    missing = CONFIG_KEYS - payload.keys()
    unknown = payload.keys() - CONFIG_KEYS
    if missing:
        raise ValueError(f"config {path} is missing: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(
            f"config {path} has unknown keys: {', '.join(sorted(unknown))}"
        )

    try:
        model_name(payload["model"])
    except (argparse.ArgumentTypeError, TypeError) as error:
        raise ValueError(f"invalid model in config {path}: {error}") from error
    if payload["effort"] not in EFFORT_LEVELS:
        raise ValueError(
            f"effort in config {path} must be one of: {', '.join(EFFORT_LEVELS)}"
        )
    budget = payload["max_budget_usd"]
    if (
        isinstance(budget, bool)
        or not isinstance(budget, (int, float))
        or not math.isfinite(budget)
        or budget <= 0
    ):
        raise ValueError(
            f"max_budget_usd in config {path} must be greater than zero"
        )
    for key in ("session_persistence", "customizations"):
        if not isinstance(payload[key], bool):
            raise ValueError(f"{key} in config {path} must be true or false")

    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    config_args, _ = config_parser.parse_known_args(argv)
    config = load_config(config_args.config)

    parser = argparse.ArgumentParser(
        description=(
            "Pipe a prompt from stdin to the Claude Code CLI in read-only "
            "print mode. Sessions persist by default."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=config_args.config,
        help=f"JSON defaults file (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--model",
        type=model_name,
        default=config["model"],
        help=f"Claude model alias or full ID (config: {config['model']})",
    )
    parser.add_argument(
        "--effort",
        choices=EFFORT_LEVELS,
        default=config["effort"],
        help=f"reasoning effort (config: {config['effort']})",
    )
    parser.add_argument(
        "--max-budget-usd",
        type=positive_amount,
        default=config["max_budget_usd"],
        help=(
            "hard request budget ceiling "
            f"(config: {config['max_budget_usd']:g})"
        ),
    )
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument(
        "--fresh",
        action="store_true",
        help="run without saving or resuming a Claude session",
    )
    session_group.add_argument(
        "--persistent",
        action="store_true",
        help="start and save a new Claude session",
    )
    session_group.add_argument(
        "--resume",
        type=non_empty_value,
        metavar="SESSION_ID_OR_NAME",
        help="resume a specific persistent Claude session",
    )
    session_group.add_argument(
        "--continue-session",
        action="store_true",
        help="continue Claude's most recent session in the working directory",
    )
    parser.add_argument(
        "--session-name",
        type=non_empty_value,
        metavar="NAME",
        help="name a newly created persistent session",
    )
    customization_group = parser.add_mutually_exclusive_group()
    customization_group.add_argument(
        "--with-customizations",
        dest="customizations_enabled",
        action="store_true",
        help="allow Claude customizations instead of using safe mode",
    )
    customization_group.add_argument(
        "--without-customizations",
        dest="customizations_enabled",
        action="store_false",
        help="use safe mode even when customizations are enabled in config",
    )
    parser.set_defaults(customizations_enabled=config["customizations"])

    args = parser.parse_args(argv)
    args.session_persistence_default = config["session_persistence"]
    if args.session_name and session_mode(args) != "persistent":
        parser.error(
            "--session-name can only be used when starting a new persistent session"
        )
    return args


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


def session_mode(args: argparse.Namespace) -> str:
    if args.fresh:
        return "fresh"
    if args.resume:
        return "resume"
    if args.continue_session:
        return "continue"
    if args.persistent or args.session_persistence_default:
        return "persistent"
    return "fresh"


def build_command(args: argparse.Namespace, claude_command: list[str]) -> list[str]:
    command = [
        *claude_command,
        "-p",
        "--model",
        args.model,
        "--effort",
        args.effort,
        "--output-format",
        "json",
        "--permission-mode",
        "dontAsk",
        "--tools",
        READ_ONLY_TOOLS,
        "--allowed-tools",
        READ_ONLY_TOOLS,
        "--max-budget-usd",
        format(args.max_budget_usd, "g"),
    ]

    mode = session_mode(args)
    if mode == "fresh":
        command.append("--no-session-persistence")
    elif mode == "resume":
        command.extend(["--resume", args.resume])
    elif mode == "continue":
        command.append("--continue")
    elif args.session_name:
        command.extend(["--name", args.session_name])

    if not args.customizations_enabled:
        command.append("--safe-mode")

    return command


def run() -> int:
    try:
        args = parse_args()
        prompt = read_prompt()
        command = build_command(args, resolve_claude_command())
    except (RuntimeError, ValueError) as error:
        print(f"ask-claude: {error}", file=sys.stderr)
        return 2

    try:
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    except OSError as error:
        print(f"ask-claude: failed to run Claude Code: {error}", file=sys.stderr)
        return 1

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
        "config_path": str(args.config.resolve()),
        "requested_model": args.model,
        "requested_effort": args.effort,
        "session_mode": session_mode(args),
        "session_id": optional_field(claude_result, "session_id"),
        "customizations_enabled": args.customizations_enabled,
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
