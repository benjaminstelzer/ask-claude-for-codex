from __future__ import annotations

from argparse import Namespace
import contextlib
import importlib.util
import io
import subprocess
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "ask-claude-for-codex"
    / "scripts"
    / "ask_claude.py"
)
SPEC = importlib.util.spec_from_file_location("ask_claude", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
ask_claude = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ask_claude)


class RecordingStream:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def reconfigure(self, **kwargs: str) -> None:
        self.calls.append(kwargs)


class AskClaudeTests(unittest.TestCase):
    def run_with_claude_output(self, stdout: str) -> tuple[int, str]:
        completed = subprocess.CompletedProcess(
            args=["claude"],
            returncode=0,
            stdout=stdout,
            stderr="",
        )
        stderr = io.StringIO()
        with (
            mock.patch.object(ask_claude, "parse_args", return_value=object()),
            mock.patch.object(ask_claude, "read_prompt", return_value="prompt"),
            mock.patch.object(
                ask_claude,
                "resolve_claude_command",
                return_value=["claude"],
            ),
            mock.patch.object(
                ask_claude,
                "build_command",
                return_value=["claude"],
            ),
            mock.patch.object(ask_claude.subprocess, "run", return_value=completed),
            contextlib.redirect_stderr(stderr),
        ):
            return ask_claude.run(), stderr.getvalue()

    def test_standard_streams_are_configured_for_utf8(self) -> None:
        streams = [RecordingStream(), RecordingStream(), RecordingStream()]
        with (
            mock.patch.object(ask_claude.sys, "stdin", streams[0]),
            mock.patch.object(ask_claude.sys, "stdout", streams[1]),
            mock.patch.object(ask_claude.sys, "stderr", streams[2]),
        ):
            ask_claude.configure_standard_streams()

        self.assertEqual(
            streams[0].calls,
            [{"encoding": "utf-8-sig", "errors": "replace"}],
        )
        for stream in streams[1:]:
            self.assertEqual(
                stream.calls,
                [{"encoding": "utf-8", "errors": "replace"}],
            )

    def test_json_result_must_be_an_object(self) -> None:
        for raw_output in ('["answer"]', '"answer"', "null"):
            with self.subTest(raw_output=raw_output):
                with self.assertRaisesRegex(ValueError, "not an object"):
                    ask_claude.parse_claude_result(raw_output)

    def test_invalid_json_uses_wrapper_error_convention(self) -> None:
        with self.assertRaisesRegex(ValueError, "Claude returned invalid JSON"):
            ask_claude.parse_claude_result("not-json")

    def test_error_payload_uses_cli_error_messages(self) -> None:
        payload = {
            "is_error": True,
            "subtype": "error_max_budget_usd",
            "terminal_reason": "budget_exhausted",
            "errors": ["Reached maximum budget ($0.000001)"],
        }
        self.assertEqual(
            ask_claude.claude_error_details(payload),
            "Reached maximum budget ($0.000001)",
        )

    def test_run_rejects_error_payload_with_zero_exit_code(self) -> None:
        exit_code, stderr = self.run_with_claude_output(
            '{"is_error":true,"subtype":"error_max_budget_usd",'
            '"errors":["Reached maximum budget"]}'
        )
        self.assertEqual(exit_code, 1)
        self.assertIn("Claude returned an error: Reached maximum budget", stderr)

    def test_run_rejects_non_object_json_without_a_traceback(self) -> None:
        exit_code, stderr = self.run_with_claude_output('["answer"]')
        self.assertEqual(exit_code, 1)
        self.assertIn("Claude returned JSON that is not an object", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_error_subtype_is_rejected_without_is_error(self) -> None:
        payload = {"subtype": "error_max_turns", "terminal_reason": "max_turns"}
        self.assertEqual(ask_claude.claude_error_details(payload), "max_turns")

    def test_success_payload_is_not_an_error(self) -> None:
        payload = {"is_error": False, "subtype": "success", "result": "OK"}
        self.assertIsNone(ask_claude.claude_error_details(payload))

    def test_command_exposes_read_and_web_tools_but_no_mutating_tools(self) -> None:
        args = Namespace(
            model="claude-fable-5",
            effort="high",
            max_budget_usd=10,
            fresh=True,
            resume=None,
            continue_session=False,
            persistent=False,
            session_persistence_default=True,
            session_name=None,
            customizations_enabled=False,
        )

        command = ask_claude.build_command(args, ["claude"])
        expected_tools = "Read,Grep,Glob,WebSearch,WebFetch"
        self.assertEqual(command[command.index("--tools") + 1], expected_tools)
        self.assertEqual(
            command[command.index("--allowed-tools") + 1], expected_tools
        )
        for mutating_tool in ("Bash", "Edit", "Write"):
            self.assertNotIn(mutating_tool, expected_tools)

    def test_help_survives_a_configuration_error(self) -> None:
        with (
            mock.patch.object(
                ask_claude,
                "resolve_config",
                side_effect=ValueError("invalid config"),
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            with self.assertRaises(SystemExit) as raised:
                ask_claude.parse_args(["--help"])
        self.assertEqual(raised.exception.code, 0)

    def test_configuration_error_still_blocks_normal_calls(self) -> None:
        with mock.patch.object(
            ask_claude,
            "resolve_config",
            side_effect=ValueError("invalid config"),
        ):
            with self.assertRaisesRegex(ValueError, "invalid config"):
                ask_claude.parse_args([])


if __name__ == "__main__":
    unittest.main()
