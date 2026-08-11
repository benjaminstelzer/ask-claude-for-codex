# Ask Claude for Codex

A second opinion is useful only when it is actually a second opinion.

[![Test](https://github.com/benjaminstelzer/ask-claude-for-codex/actions/workflows/test.yml/badge.svg)](https://github.com/benjaminstelzer/ask-claude-for-codex/actions/workflows/test.yml)

Ask Claude for Codex is an Agent Skill that lets Codex consult the locally
authenticated Claude Code CLI without leaving the current task. The Claude
session is read-only and isolated from local Claude customizations by default.
It can still persist across follow-up questions, because rebuilding the same
context for every objection is independence taken a little too literally.

The default is **Fable 5 with high reasoning effort**. A request can select
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
Ask Opus 5 with max reasoning to challenge this architecture.
```

```text
Frage Fable, ob dieser Fix die eigentliche Ursache behebt.
```

Unless overridden, the Skill uses:

| Setting | Default |
| --- | --- |
| Model | `claude-fable-5` |
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

The repository contains one installable Agent Skill directory. Usually, let
Codex install it with this prompt:

```text
Install this Agent Skill from GitHub and make it available for all my projects:
https://github.com/benjaminstelzer/ask-claude-for-codex/tree/main/ask-claude-for-codex
```

For a manual installation, copy the repository's `ask-claude-for-codex/`
directory so the final path is:

```text
<skills-dir>/ask-claude-for-codex/SKILL.md
```

The Skill requires Python and an authenticated `claude` command on `PATH`.
Claude Code usage limits and model charges still apply.

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

The wrapper starts Claude Code with the selected model, effort, budget and
fixed tool list. Its configuration, conversation state and customization mode
are separate concerns: changing one does not quietly change the others.

### Configuration

The shipped
[`config.default.json`](ask-claude-for-codex/config.default.json) contains every
available setting:

```json
{
  "model": "claude-fable-5",
  "effort": "high",
  "max_budget_usd": 10,
  "session_persistence": true,
  "customizations": false
}
```

To change permanent behavior, copy `config.default.json` to `config.json` in
the same directory and edit the personal file. It is ignored by Git and takes
precedence over the shipped defaults. Without either file, the same defaults
remain available as an internal fallback.

| Setting | Meaning |
| --- | --- |
| `model` | Claude model alias or full model ID |
| `effort` | Reasoning effort: `low`, `medium`, `high`, `xhigh` or `max` |
| `max_budget_usd` | Maximum spend for one consultation |
| `session_persistence` | Whether Claude conversations are saved for follow-up questions |
| `customizations` | Whether Claude uses the local Claude setup or starts as an isolated second opinion |

For a one-time change, put the choice in the request instead of editing the
file:

```text
Ask Opus 5 with max reasoning and a USD 3 budget to review this architecture.
```

### Conversations

The first consultation starts a saved Claude conversation by default.
Follow-up questions in the same Codex task continue it, so Claude retains the
earlier exchange. Ask for a new conversation when the topic changes, or ask for
a fresh, stateless consultation when the exchange should not be saved.

Session persistence stores the conversation. Customizations control the
environment Claude uses. They are independent.

### Claude customizations

With `customizations` set to `false`, Claude starts in safe mode. It does not
load `CLAUDE.md` files, project instructions, Claude Skills, plugins, hooks,
MCP servers or custom commands. This is the default because it produces a more
independent second opinion than asking the existing setup to admire its own
homework.

With `customizations` set to `true`, Claude can use that local setup. Enable it
when the consultation should follow Claude-specific project instructions, use
a configured Claude Skill or include context from an MCP server. The wrapper
still withholds Claude's built-in Bash, Edit and Write tools. Configured hooks,
plugins or MCP servers can introduce their own behavior or side effects, so
enabling customizations deliberately reduces isolation.

For one consultation, say so in the request:

```text
Ask Claude with my local customizations to review this plan.
```

### Safety boundary

Read-only tools prevent direct Bash, Edit and Write use. They do not make
arbitrary content safe to disclose. Search queries and fetched URLs leave the
local machine. Prompts must not contain credentials, tokens, private keys,
secret-bearing URLs, private source text, or unrelated personal data.

Conversation persistence grants no additional tools or permissions. When
customizations are enabled, their configured hooks and extensions remain
outside the built-in tool boundary.

## Related projects

- [Scoville Code](https://github.com/benjaminstelzer/scoville-code-anti-ai-slop)
  keeps implementation, scope and validation with Codex after the consultation.
- [Scoville Scribe](https://github.com/benjaminstelzer/scoville-scribe-anti-ai-slop)
  protects meaning and terminology when the second opinion concerns writing.
- [Codex, Fable-calibrated style](https://github.com/benjaminstelzer/codex-fable-like-system-prompt-for-gpt-5.6-sol)
  supplies the broader collaboration style used by my Codex setup.

## Status

The deterministic wrapper tests run on Linux and Windows. They cover UTF-8
stream setup, Claude result parsing, error handling, configuration-error
behavior, and the exact read-and-web tool surface without Bash, Edit, or Write.
Live model quality still depends on the selected Claude model and the evidence
available in the task. The wrapper can create distance, not omniscience.

## Sources

- [`SKILL.md`](ask-claude-for-codex/SKILL.md) defines activation, authority and
  the consultation workflow.
- [`ask_claude.py`](ask-claude-for-codex/scripts/ask_claude.py) implements the
  Claude Code wrapper.
- [`test_ask_claude.py`](tests/test_ask_claude.py) defines the deterministic
  regression coverage.

## License

MIT - see [LICENSE](LICENSE).
