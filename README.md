# Ask Claude for Codex

A second opinion is useful only when it is actually a second opinion.

Ask Claude for Codex is an Agent Skill that lets Codex consult the locally
authenticated Claude Code CLI without leaving the current task. The Claude
session is read-only and isolated from local Claude customizations by default.
It can still persist across follow-up questions, because rebuilding the same
context for every objection is independence taken a little too literally.

The default is **Fable 5.1 with high reasoning effort**. A request can select
another Claude model alias or full model ID, change the effort level and budget,
or deliberately enable the local Claude setup.

## Why this Skill?

Asking another model can expose a weak assumption, an overlooked failure path,
or a genuinely different reading. But another model inside the same
instructions, plugins and project framing is not as independent as the phrase
"second opinion" suggests. This Skill keeps the consultation separate by
default, gives it a fixed read-only tool surface, and makes the remaining
choices explicit.

Claude's answer is still advice. Codex must verify it before the answer becomes
an edit, a decision, or the wonderfully confident announcement that everything
is now fixed.

## How to use

Invoke the Skill explicitly or ask naturally:

```text
$ask-claude-for-codex Review this implementation plan with the defaults.
```

```text
Ask Claude using model alias opus with max effort to challenge this architecture.
```

```text
Ask Fable whether this fix addresses the root cause.
```

Unless overridden, the Skill uses:

| Setting | Default |
| --- | --- |
| Model | `claude-fable-5-1` |
| Reasoning effort | `high` |
| Budget ceiling | USD 10 |
| Claude tools | `Read,Grep,Glob,WebSearch,WebFetch` |
| Session persistence | Enabled |
| Claude customizations | Disabled with safe mode |

Model values are passed to Claude Code as aliases or full IDs. For example,
`opus` selects the current Opus alias. Effort accepts `low`, `medium`, `high`,
`xhigh` or `max`.

Explicit `$ask-claude-for-codex` invocation works on hosts that support named
Skill invocation.

## Install

In a local Codex session, ask:

```text
Install this Agent Skill for all my projects from this exact package directory:
https://github.com/benjaminstelzer/ask-claude-for-codex/tree/main/ask-claude-for-codex
Preserve existing customizations and ask before overwriting conflicting files.
Report the installed location and whether the host discovers the Skill.
```

The agent needs source access and permission to write to its personal Skills
location. Manual fallback: [Codex Skills guide](https://learn.chatgpt.com/docs/build-skills).

Requires Python 3.9 or newer and an authenticated Claude Code 2.1.255 or newer.
Claude usage limits and model charges apply.

## What it enforces

- **A deliberate second opinion.** Model, reasoning effort and budget are
  explicit instead of being hidden inside the wrapper.
- **Read-only consultation.** Claude receives `Read`, `Grep`, `Glob`,
  `WebSearch` and `WebFetch`, but not Bash, Edit or Write.
- **Isolation by default.** `CLAUDE.md`, Claude Skills, plugins, hooks, MCP
  servers and custom commands stay disabled unless the request enables them.
- **Persistent follow-up when useful.** The first consultation starts a saved
  conversation by default, while a request can start fresh or remain stateless.
- **Advice without borrowed authority.** Claude cannot authorize edits, expand
  scope, accept a Decision, publish changes or override Codex instructions.
- **An explicit data boundary.** Search queries and fetched URLs leave the
  local machine. Secrets and unrelated private data do not belong in prompts.

The complete contract is in
[`SKILL.md`](ask-claude-for-codex/SKILL.md).

## How it works

The adapter starts Claude Code with the selected model, effort, budget, and
fixed tool list. It reports an answer only when Claude returns a usable result.
Missing, blank, or malformed answers remain errors.

### Configuration

For personal defaults, copy [config.default.json](ask-claude-for-codex/config.default.json)
to `config.json` beside it. This ignored personal file overrides the shipped
defaults. Without either file, the same defaults remain available internally.

The fields are `model`, `effort`, `max_budget_usd`, `session_persistence`, and
`customizations`. For a one-off override, name the model, effort, or budget in
the request instead of editing the file.

### Follow-ups

Conversations are saved by default, so follow-ups in the same Codex task retain
the earlier exchange. Ask for a new conversation when the topic changes, or a
fresh stateless consultation when it should not be saved. Persistence grants
no additional tools or permissions.

### Optional Claude deadline

The optional `--timeout-seconds <positive-number>` applies to one Claude call
and is disabled by default. Expiry returns exit 124 without an automatic retry,
budget increase, or success answer. A known resume ID survives the error, but an
interrupted turn is not guaranteed to be saved.

It terminates and waits for the direct child, not a whole process tree or remote
job. Startup and inherited pipes can delay return. Synthetic direct-child tests
passed on Windows and WSL Ubuntu. Live provider cancellation was not tested.

### Customizations and safety

Safe mode disables local Claude instructions, Skills, plugins, hooks, MCP
servers, and custom commands. Enable `customizations` only when the consultation
needs that setup. The adapter still withholds built-in Bash, Edit, and Write,
but extensions and hooks can introduce side effects outside that boundary.

Read-only tools do not make private content safe to disclose. Queries and URLs
leave the machine. Do not include credentials, keys, secret-bearing URLs,
private source text, or unrelated personal data in the consultation.

Repository structure and contributor detail are in the
[maintenance notes](docs/maintenance.md).

## Related projects

- [Scoville Code](https://github.com/benjaminstelzer/scoville-code-anti-ai-slop)
  keeps implementation, scope and validation with Codex after the consultation.
- [Scoville Scribe](https://github.com/benjaminstelzer/scoville-scribe-anti-ai-slop)
  protects meaning and terminology when the second opinion concerns writing.

## Status

Deterministic adapter tests cover configuration, UTF-8, result parsing,
explicit error handling, the fixed read-and-web tool surface, and synthetic
deadlines on Windows and WSL Ubuntu. Live cancellation was not tested.

Model quality depends on the selected Claude model and available evidence.
The adapter can create distance, not omniscience.

## Sources

- [`SKILL.md`](ask-claude-for-codex/SKILL.md) defines activation, authority and
  the consultation workflow.
- [`ask_claude.py`](ask-claude-for-codex/scripts/ask_claude.py) implements the
  Claude Code wrapper.
- [`test_ask_claude.py`](tests/test_ask_claude.py) defines the deterministic
  regression coverage.

## License

MIT. See [LICENSE](LICENSE).
