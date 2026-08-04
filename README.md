# Ask Claude for Codex

Give Codex a second opinion from Claude without leaving the task.

[![Test](https://github.com/benjaminstelzer/ask-claude-for-codex/actions/workflows/test.yml/badge.svg)](https://github.com/benjaminstelzer/ask-claude-for-codex/actions/workflows/test.yml)

Ask Claude for Codex is an Agent Skill that calls the locally authenticated
Claude Code CLI from Codex. It is useful for independent reviews, critiques,
comparisons and alternative analyses of the current workspace. The consulted
Claude session is read-only and persistent by default, so follow-up questions
can continue the same conversation instead of rebuilding its context.

The default is **Fable 5 with high reasoning effort**. A request can instead
name another Claude model alias or full model ID and any effort level supported
by the installed CLI.

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

The skill requires Python and an authenticated `claude` command on `PATH`.
Claude Code usage limits and model charges still apply.

## Use

Invoke the skill explicitly or ask naturally:

```text
$ask-claude-for-codex Review this implementation plan with the defaults.
```

```text
Ask Opus 5 with max reasoning to challenge this architecture.
```

```text
Frage Fable, ob dieser Fix die eigentliche Ursache behebt.
```

Unless overridden, the skill uses:

| Setting | Default |
| --- | --- |
| Model | `claude-fable-5` |
| Reasoning effort | `high` |
| Budget ceiling | USD 10 |
| Claude tools | `Read,Grep,Glob` |
| Session persistence | Enabled |
| Claude customizations | Disabled with safe mode |

Model values are passed to Claude Code as aliases or full IDs. For example,
`opus` selects the current Opus alias. Effort accepts `low`, `medium`, `high`,
`xhigh` or `max`.

## Configure the defaults

The shipped
[`ask-claude-for-codex/config.default.json`](ask-claude-for-codex/config.default.json)
contains every available setting:

```json
{
  "model": "claude-fable-5",
  "effort": "high",
  "max_budget_usd": 10,
  "session_persistence": true,
  "customizations": false
}
```

To change permanent behavior, copy `config.default.json` to `config.json` in the
same directory and edit `config.json`. The personal file is ignored by Git and
takes precedence over the shipped defaults. Without a personal file, the skill
uses `config.default.json`. If that file is also missing, the same defaults are
available as an internal fallback.

| Setting | Meaning |
| --- | --- |
| `model` | Claude model alias or full model ID |
| `effort` | Reasoning effort: `low`, `medium`, `high`, `xhigh` or `max` |
| `max_budget_usd` | Maximum spend for one consultation |
| `session_persistence` | Whether Claude conversations are saved for follow-up questions |
| `customizations` | Whether Claude uses the local Claude setup or starts as an isolated second opinion |

For a one-time change, describe it in the request instead of editing the file:

```text
Ask Opus 5 with max reasoning and a USD 3 budget to review this architecture.
```

## Conversations

The first consultation starts a saved Claude conversation by default. Follow-up
questions in the same Codex task continue that conversation, so Claude retains
the earlier exchange. Ask for a new conversation when starting an independent
topic, or ask for a fresh, stateless consultation when the exchange should not
be saved.

Session persistence and Claude customizations are independent. Persistence
stores the conversation; customizations control the environment Claude uses.

## Claude customizations

With `customizations` set to `false`, Claude starts in safe mode. It does not
load `CLAUDE.md` files, project instructions, Claude skills, plugins, hooks, MCP
servers or custom commands. This is the default because it produces a more
independent second opinion that is not shaped by the existing Claude setup.

With `customizations` set to `true`, Claude can use that local setup. Enable it
when the consultation should follow Claude-specific project instructions, use a
configured Claude skill or include context from an MCP server. The skill still
withholds Claude's built-in Bash, Edit and Write tools. Configured hooks,
plugins or MCP servers can nevertheless introduce their own behavior or side
effects, so enabling customizations is a deliberate reduction of isolation.

To enable customizations for one consultation without changing `config.json`,
say so in the request:

```text
Ask Claude with my local customizations to review this plan.
```

## Safety boundary

Claude receives only `Read`, `Grep` and `Glob`. Bash, Edit and Write are not
available. Conversation persistence does not grant additional tools or
permissions. When customizations are enabled, their configured hooks and
extensions remain outside this built-in tool boundary.

Claude's response is advice, not authority. It cannot authorize edits, expand
scope, accept a Decision, publish changes or override Codex instructions. Codex
must verify any recommendation before acting on it.

Never include credentials, tokens, private keys or unrelated personal data in
a consultation prompt.
