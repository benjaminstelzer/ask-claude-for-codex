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
READ_ONLY_TOOLS = "Read,Grep,Glob,WebSearch,WebFetch"
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
SKILL_DIR = Path(__file__).resolve().parent.parent
USER_CONFIG_PATH = SKILL_DIR / "config.json"
DEFAULT_CONFIG_PATH = SKILL_DIR / "config.default.json"
CONFIG_KEYS = {
    "model",
    "effort",
    "max_budget_usd",
    "session_persistence",
    "customizations",
}
FALLBACK_CONFIG: dict[str, Any] = {
    "model": "claude-fable-5-1",
    "effort": "high",
    "max_budget_usd": 10,
    "session_persistence": True,
    "customizations": False,
}


def configure_standard_streams() -> None:
    input_reconfigure = getattr(sys.stdin, "reconfigure", None)
    if callable(input_reconfigure):
        input_reconfigure(encoding="utf-8-sig", errors="replace")

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def positive_amount(value: str) -> float:
    amount = float(value)
    if not math.isfinite(amount) or amount <= 0:
        raise argparse.ArgumentTypeError("budget must be greater than zero")
    return amount


def positive_timeout(value: str) -> float:
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("timeout seconds must be finite and greater than zero")
    return seconds


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


def resolve_config(explicit_path: Path | None) -> tuple[Path | None, dict[str, Any]]:
    if explicit_path is not None:
        return explicit_path, load_config(explicit_path)
    if USER_CONFIG_PATH.is_file():
        return USER_CONFIG_PATH, load_config(USER_CONFIG_PATH)
    if DEFAULT_CONFIG_PATH.is_file():
        return DEFAULT_CONFIG_PATH, load_config(DEFAULT_CONFIG_PATH)
    return None, FALLBACK_CONFIG.copy()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("--config", type=Path)
    config_args, _ = config_parser.parse_known_args(raw_argv)
    try:
        config_path, config = resolve_config(config_args.config)
    except ValueError:
        if not any(argument in ("-h", "--help") for argument in raw_argv):
            raise
        config_path, config = None, FALLBACK_CONFIG.copy()

    parser = argparse.ArgumentParser(
        description=(
            "Pipe a prompt from stdin to the Claude Code CLI in read-only "
            "print mode. Sessions persist by default."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=config_path,
        help=(
            "use a specific JSON config instead of config.json or "
            "config.default.json"
        ),
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
    parser.add_argument(
        "--timeout-seconds",
        type=positive_timeout,
        default=None,
        help="optional Claude process deadline in seconds (default: disabled)",
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

    args = parser.parse_args(raw_argv)
    args.config_path = config_path
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


def parse_claude_result(raw_output: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as error:
        raise ValueError(f"Claude returned invalid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("Claude returned JSON that is not an object")
    return payload


def claude_error_details(payload: dict[str, Any]) -> str | None:
    subtype = payload.get("subtype")
    has_error_subtype = isinstance(subtype, str) and subtype.startswith("error")
    if payload.get("is_error") is not True and not has_error_subtype:
        return None

    errors = payload.get("errors")
    if isinstance(errors, list):
        messages = [message for message in errors if isinstance(message, str)]
        if messages:
            return "; ".join(messages)

    for key in ("result", "terminal_reason", "subtype"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return "Claude reported an unspecified error"


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
            timeout=args.timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        print(f"ask-claude: Claude deadline exceeded after {args.timeout_seconds:g} seconds. No automatic retry.", file=sys.stderr)
        if args.resume:
            print(f"ask-claude: Last known resume session: {args.resume}", file=sys.stderr)
        return 124
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
        claude_result = parse_claude_result(completed.stdout)
    except ValueError as error:
        print(f"ask-claude: {error}", file=sys.stderr)
        return 1

    error_details = claude_error_details(claude_result)
    if error_details is not None:
        print(
            f"ask-claude: Claude returned an error: {error_details}",
            file=sys.stderr,
        )
        return 1

    answer = claude_result.get("result")
    if not isinstance(answer, str) or not answer.strip():
        print("ask-claude: Claude returned no answer", file=sys.stderr)
        return 1

    output = {
        "config_path": (
            str(args.config_path.resolve()) if args.config_path is not None else None
        ),
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
        "answer": answer,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    configure_standard_streams()
    raise SystemExit(run())
