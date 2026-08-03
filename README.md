# Ask Claude for Codex

Give Codex a second opinion from Claude without leaving the task.

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

The editable
[`ask-claude-for-codex/config.json`](ask-claude-for-codex/config.json) is the
source of the wrapper defaults:

```json
{
  "model": "claude-fable-5",
  "effort": "high",
  "max_budget_usd": 10,
  "session_persistence": true,
  "customizations": false
}
```

Edit this file to change permanent behavior. Every key is required; unknown
keys and invalid values stop the call with a concrete configuration error.
Model, effort and budget CLI options override the file for one invocation.
`--fresh` or `--persistent` override its persistence setting, while
`--with-customizations` or `--without-customizations` override its
customization setting.

The read-only Claude tool list and `dontAsk` permission mode are intentionally
not configurable. They define the skill's safety boundary rather than a user
preference; changing them would turn this into a different capability.

An alternative profile can be selected without modifying the installed skill:

```powershell
$prompt | python ./ask-claude-for-codex/scripts/ask_claude.py `
  --config C:/path/to/opus-review.json
```

## Conversation and isolation modes

Session persistence and Claude customizations solve different problems. A
persistent session stores the conversation. Customizations control which local
Claude configuration participates in it. Persistence is enabled by default;
customizations are not.

| Mode | Command | What it does | Use it when |
| --- | --- | --- | --- |
| New persistent conversation | No option with the shipped config, or `--persistent` | Creates a saved Claude session and returns its `session_id` | Starting a new topic or independent line of discussion |
| Resume a conversation | `--resume <session_id>` | Loads the exact saved conversation and appends the new question | Asking a follow-up that should retain earlier questions and answers |
| Continue the latest session | `--continue-session` | Loads the most recent Claude session for the current working directory | The latest session is known to be the intended one and its ID is unavailable |
| Fresh one-off call | `--fresh` | Neither saves nor resumes a session | Context must not persist or the question is deliberately stateless |

The wrapper does not automatically guess which saved conversation belongs to a
follow-up. Codex keeps the returned `session_id` for each active Claude
conversation and passes it explicitly with `--resume`. This permits several
independent Claude conversations in one Codex task without mixing their
contexts. Explicit IDs are preferable to `--continue-session`, whose meaning
depends on whichever Claude session was most recently used in that directory.

Safe mode is a separate default. It prevents Claude's local customizations from
participating, including project instructions, skills, plugins, hooks, MCP
servers and custom commands. `--with-customizations` disables safe mode for a
call while the wrapper still limits Claude's built-in tools to `Read`, `Grep`
and `Glob`. Configured hooks or other customizations can nevertheless introduce
additional behavior, so this option is never enabled implicitly.

If `session_persistence` is `false`, calls without a session option become fresh
one-off calls; `--persistent` still starts a saved conversation. If
`customizations` is `true`, safe mode is omitted unless
`--without-customizations` is passed. These values affect new calls only. A
saved session's conversation history is selected separately with `--resume`.

## Run the wrapper directly

The bundled Python wrapper keeps the prompt on standard input rather than in a
shell argument. The first call starts a new persistent conversation:

```powershell
@'
Review the current repository. Return only concrete findings with paths,
mechanisms, impact and the smallest sufficient correction. Do not edit files.
'@ | python ./ask-claude-for-codex/scripts/ask_claude.py
```

The JSON result contains a `session_id`. Use it for follow-up questions:

```powershell
$followUp | python ./ask-claude-for-codex/scripts/ask_claude.py `
  --resume 12345678-1234-1234-1234-123456789abc
```

Override the defaults when needed:

```powershell
$prompt | python ./ask-claude-for-codex/scripts/ask_claude.py `
  --model opus `
  --effort max `
  --max-budget-usd 6
```

Start a stateless call or opt into local Claude customizations only when those
behaviors are intended:

```powershell
$prompt | python ./ask-claude-for-codex/scripts/ask_claude.py --fresh
$prompt | python ./ask-claude-for-codex/scripts/ask_claude.py --with-customizations
```

The wrapper returns Claude's answer with the selected configuration path,
requested model, requested effort, reported model when available, session mode,
session ID, customization state, turns, duration, cost and permission denials
as JSON.

## Safety boundary

Claude receives only `Read`, `Grep` and `Glob`. Bash, Edit and Write are not
available. Safe mode disables Claude skills, plugins, hooks, MCP servers,
custom commands and project instructions, which keeps the second opinion
independent from the local Claude setup. Conversation persistence is enabled
by default, but it does not grant additional tools or permissions.

Passing `--with-customizations` reduces that isolation. Configured hooks and
other extensions may have effects beyond the wrapper's read-only built-in tool
list. Enable the option only when those customizations are intentionally part
of the consultation.

Claude's response is advice, not authority. It cannot authorize edits, expand
scope, accept a Decision, publish changes or override Codex instructions. Codex
must verify any recommendation before acting on it.

Never include credentials, tokens, private keys or unrelated personal data in
a consultation prompt.

## Repository contents

```text
ask-claude-for-codex/
├── CHANGELOG.md
├── LICENSE
├── README.md
└── ask-claude-for-codex/
    ├── SKILL.md
    ├── config.json
    ├── agents/
    │   └── openai.yaml
    └── scripts/
        └── ask_claude.py
```

The outer files document and license the repository. Install only the inner
`ask-claude-for-codex/` directory.

## License

MIT - see [LICENSE](LICENSE).
