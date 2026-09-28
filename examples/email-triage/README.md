# How to classify emails with a System One model

The synthetic [request](request.json) asks independent questions about one message:
reply need, urgency, category, and deeper-review need. Urgency is a Score; reply need
and deeper review are Nouls. Do not read an urgency score as confidence.

```bash
python skills/system-one-router/scripts/decide.py examples/email-triage/request.json
```

## Batch triage

```bash
python skills/system-one-router/scripts/batch_decide.py examples/email-triage/records.jsonl > results.jsonl
```

Run from the repository root with the [environment configured](../../docs/configuration.md).
The file has three synthetic messages. Each line contains an ID, state, and questions.
The helper reuses one connection pool and calls the backend sequentially, emitting one
result envelope per record. Exit status 1 means at least one failed record or a fatal error;
inspect both output and stderr. Never discard successful earlier records or ignore failures.

For a larger inbox, build one line per message. Application policy can separate routine
messages, simple actionable cases, and uncertain/complex messages for main-agent review.
Apply your evaluated thresholds to each relevant answer and preserve all errors for review.
Until you have an evaluated policy, review the proposed triage rather than auto-archiving.
The helper does not read an inbox, send email, or apply labels.

Batching several questions within each message reduces repeated state transmission compared
with separate calls per question. Whether this beats full LLM triage depends on your hosting,
quality requirements, and escalation rate; measure on held-out messages.
See [architecture](../../docs/architecture.md) and [confidence policy](../../docs/decision-policy.md).
