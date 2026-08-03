# Ask Claude for Codex

Give Codex a second opinion from Claude without leaving the task.

Ask Claude for Codex is an Agent Skill that calls the locally authenticated
Claude Code CLI from Codex. It is useful for independent reviews, critiques,
comparisons and alternative analyses of the current workspace. The consulted
Claude session is read-only, isolated from Claude customizations and discarded
after the answer.

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
| Budget ceiling | USD 4 |
| Claude tools | `Read,Grep,Glob` |
| Session persistence | Disabled |
| Claude customizations | Disabled with safe mode |

Model values are passed to Claude Code as aliases or full IDs. For example,
`opus` selects the current Opus alias. Effort accepts `low`, `medium`, `high`,
`xhigh` or `max`.

## Run the wrapper directly

The bundled Python wrapper keeps the prompt on standard input rather than in a
shell argument. From PowerShell:

```powershell
@'
Review the current repository. Return only concrete findings with paths,
mechanisms, impact and the smallest sufficient correction. Do not edit files.
'@ | python ./ask-claude-for-codex/scripts/ask_claude.py
```

Override the defaults when needed:

```powershell
$prompt | python ./ask-claude-for-codex/scripts/ask_claude.py `
  --model opus `
  --effort max `
  --max-budget-usd 6
```

The wrapper returns Claude's answer with the requested model, requested effort,
reported model when available, turns, duration, cost and permission denials as
JSON.

## Safety boundary

Claude receives only `Read`, `Grep` and `Glob`. Bash, Edit and Write are not
available. Safe mode disables Claude skills, plugins, hooks, MCP servers,
custom commands and project instructions, which keeps the second opinion
independent from the local Claude setup. Sessions are not persisted.

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
    ├── agents/
    │   └── openai.yaml
    └── scripts/
        └── ask_claude.py
```

The outer files document and license the repository. Install only the inner
`ask-claude-for-codex/` directory.

## License

MIT - see [LICENSE](LICENSE).
