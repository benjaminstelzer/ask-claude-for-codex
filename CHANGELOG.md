# Changelog

## v1.1.0 - 2026-09-05

- Reject missing, blank, or non-text Claude answers instead of reporting
  success.
- Added an optional timeout. Expiry returns exit 124 without retrying or
  raising the budget.

## v1.0.4 - 2026-09-01

- Changed the default Claude model from Fable 5 to Fable 5.1 while keeping
  `high` effort, the USD 10 budget ceiling, persistent sessions, and safe mode.

## 2026-08-06: Read-only web research

- Added `WebSearch` and `WebFetch` to Claude's fixed read-only tool surface.
  Bash, Edit, and Write remain unavailable.
- Search queries and fetched URLs can leave the local machine.

## 2026-08-03: Windows PowerShell UTF-8 input

- Prevented Windows PowerShell 5.1 from corrupting umlauts and other non-ASCII
  prompt characters.
- Accept and remove the UTF-8 preamble that PowerShell 5.1 can add to piped
  input.

## 2026-08-03: Robust Windows I/O and result handling

- Use UTF-8 for wrapper input and output on Windows.
- Reject Claude error payloads even when the CLI exits successfully, and reject
  unexpected JSON shapes without exposing a traceback.
- Keep command help available when personal configuration is missing or
  malformed.

## 2026-08-03: Configuration and conversations

- Added persistent conversations, exact-session resume, continuation, fresh
  calls, and names for new sessions.
- Added opt-in Claude customizations while keeping safe mode as the default.
- Added shipped defaults, an ignored personal configuration file, alternative
  profiles, and one-call overrides that never modify saved settings.
- Raised the default per-call budget ceiling from USD 4 to USD 10.

## 2026-08-03: Initial release

- Added read-only Claude Code consultations from Codex with configurable model,
  reasoning effort, budget, and session handling.
- Return the answer and run metadata as structured JSON.
