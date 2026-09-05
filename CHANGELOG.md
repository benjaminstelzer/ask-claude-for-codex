# Changelog

## Unreleased - 2026-09-05 audit fixes

- Shortened the README, moved contributor layout notes to docs/maintenance.md, and made agent installation the primary path. Safety and evidence limits remain explicit.
- Rejected missing, blank, or non-text Claude answers instead of reporting success.
- Documented the standalone package and development-test layout and removed generated working caches.
- Added the optional --timeout-seconds CLI setting, disabled by default. Expiry returns exit 124 without retry or budget escalation.
- Documented direct-child termination limits and removed the retired system-prompt link.
- Included the repository license in the copied package. All 20 tests passed on Windows and WSL Ubuntu without a provider call.

## 2026-09-01: Fable 5.1 default (v1.0.4)

### Changed

- Raised the shipped Claude default from Fable 5 to Fable 5.1 while preserving
  `high` reasoning effort, the USD 10 budget ceiling, persistent sessions, and
  safe mode.
- Updated `config.default.json`, the wrapper fallback, Skill contract, README,
  and regression coverage to request `claude-fable-5-1` consistently.

### Validation

- The deterministic wrapper tests and Agent Skill package validation passed.
- A live default consultation on Claude Code 2.1.257 requested
  `claude-fable-5-1` with `high` effort and returned successfully without
  permission denials.

## 2026-08-11: README voice and structure (v1.0.2)

### Changed

- Reworked the public README in Benjamin's voice while preserving the model,
  effort, budget, persistence, customization, tool, and authority boundaries.
- Aligned its section order with the Scoville project READMEs: purpose, use,
  installation, contract, mechanism, related projects, status, sources, and
  license.
- Updated the Codex Skill-list description to use the same public voice.

### Validation

- The deterministic wrapper tests and Agent Skill package validation passed.
- No live model-behavior benchmark was run because the Skill instructions and
  wrapper behavior did not change.

## 2026-08-06: Read-only web research

### Fixed

- Added Claude's `WebSearch` and `WebFetch` tools to the fixed read-only tool
  surface so an independent consultation can research current external sources.
- Kept Bash, Edit and Write unavailable and documented that search queries and
  fetched URLs leave the local machine.

### Validation

- Added a command-construction regression test for the exact read and web tool
  surface and the absence of Bash, Edit and Write.
- Verified a live Fable 5 consultation can search the web and cite the source it
  found without receiving a mutating tool.

## 2026-08-04: Public wrapper verification

### Added

- Added a GitHub Actions workflow that runs the deterministic Python wrapper
  tests on Linux and Windows.
- Added the workflow status to the README without presenting it as a test of
  Claude response quality.

## 2026-08-03: Windows PowerShell UTF-8 input

### Fixed

- Set PowerShell's native pipeline output encoding to BOM-less UTF-8 before
  every prompt pipe in the skill instructions and examples.
- Prevented Windows PowerShell 5.1 from replacing German umlauts and other
  non-ASCII prompt characters before the wrapper receives them.
- Made wrapper input tolerate and remove the UTF-8 preamble that Windows
  PowerShell 5.1 still emits at the start of a native pipeline.

### Validation

- Verified the documented setting and wrapper input together with
  `powershell.exe` by piping German umlauts and a Unicode arrow into Python and
  comparing their code points without a leading preamble.

## 2026-08-03: Robust Windows I/O and result handling

### Fixed

- Configured the wrapper's standard streams as UTF-8 so non-ASCII prompts and
  Claude answers do not become mojibake or fail under the Windows code page.
- Rejected Claude JSON error payloads even when the CLI process exits with code
  zero.
- Rejected valid JSON that is not an object with a concise wrapper error instead
  of an `AttributeError` traceback.
- Kept command help available when a personal configuration is missing or
  malformed; normal calls still fail on the configuration error.

### Validation

- Added focused regression tests for UTF-8 stream configuration, JSON shape,
  error payloads and configuration-independent help.
- Verified an exact UTF-8 stdin/stdout round trip for German umlauts and a
  Unicode arrow while Python was forced to start with `cp1252`.
- Confirmed the installed Claude Code 2.1.220 error payload uses `is_error`, an
  `error_*` subtype, `terminal_reason` and an `errors` list.

## 2026-08-03: Skill-focused README

### Changed

- Removed direct wrapper commands, wrapper flags, JSON output details, internal
  configuration resolution, the repository tree and license boilerplate from
  the README.
- Replaced implementation-level controls with natural-language examples for
  model selection, one-time overrides, conversation handling and Claude
  customizations.
- Kept only installation, skill usage, editable defaults and user-relevant
  safety boundaries.

## 2026-08-03: Configuration template and fallback

### Changed

- Added a versioned `config.default.json` that documents all supported settings.
- Added optional personal `config.json` support and excluded that file from Git.
- Resolved configuration in a defined order: explicit file, personal file,
  shipped default file, then internal fallback values only when both local files
  are absent.
- Clarified in the README that command-line options affect one invocation and
  never modify configuration files.

### Validation

- The shipped default file supplied the documented Fable 5, high-effort,
  USD 10, persistent and safe-mode defaults.
- A temporary personal `config.json` took precedence without changing the
  shipped file; command-line options changed the parsed call without changing
  either file.
- With both local configuration paths absent, the wrapper selected its internal
  fallback values. A missing explicit `--config` path still failed visibly.

## 2026-08-03: Configurable conversations and customizations

### Changed

- Enabled persistent Claude sessions by default and included the returned
  `session_id` in wrapper output.
- Added explicit `--resume`, `--continue-session` and `--fresh` conversation
  modes so follow-ups can preserve context without mixing independent threads.
- Added `--session-name` for new persistent conversations.
- Added opt-in `--with-customizations`; safe mode remains the default.
- Moved model, effort, budget, persistence and customization defaults into an
  editable `config.json`, with `--config` support for alternative profiles.
- Added explicit CLI overrides for persistent sessions and safe mode when a
  custom configuration changes those defaults.
- Raised the default per-call budget ceiling from USD 4 to USD 10.
- Expanded the README with the differences between persistence, resuming,
  stateless calls and Claude customizations.

### Validation

- Command-construction checks covered the shipped defaults, all four session
  modes, both customization overrides and an alternative configuration file.
- Invalid session-option combinations were rejected by the argument parser.
- A live two-turn Fable 5 consultation returned a persistent `session_id`,
  resumed that exact ID and recalled a token supplied only in the first turn.
  Both calls completed without permission denials.

## 2026-08-03: Initial release

### Added

- Added the `ask-claude-for-codex` Agent Skill for read-only Claude Code
  consultations from Codex.
- Added configurable Claude model and reasoning effort with Fable 5 and high
  effort as defaults.
- Added a Python wrapper that sends prompts through standard input, disables
  session persistence and Claude customizations, exposes only read tools and
  returns answer and run metadata as JSON.
- Added installation, usage, safety and direct-wrapper documentation.

### Validation

- The installable directory passed the canonical Agent Skill validator.
- Python syntax, empty-prompt rejection and invalid-model rejection passed.
- A live default invocation requested `claude-fable-5` with `high` effort and
  returned the exact expected answer in one turn without permission denials.
  Claude's JSON omitted the resolved model field, so no backend model identity
  is claimed beyond the requested full model ID.
