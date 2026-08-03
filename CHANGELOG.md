# Changelog

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
