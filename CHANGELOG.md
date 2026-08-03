# Changelog

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
