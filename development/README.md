# Development

The only installable package is [`ask-claude-for-codex/`](../ask-claude-for-codex/). Tests and maintenance material in this directory are not installed with the Skill.

## Validate

Run the deterministic adapter suite from the repository root:

```text
python -B -m unittest discover -s development/tests -v
```

Static tests do not prove live Claude availability, cancellation behavior, or model quality.

## Retention

Keep current tests and this maintenance summary. Put ad-hoc audits, live traces, transcripts, benchmark runs, and generated reviews in temporary storage. Retain a concise evaluation summary only when it explains a useful result or
development lesson and a published release links it. Routine checks and
inconclusive miniature runs stay temporary.
