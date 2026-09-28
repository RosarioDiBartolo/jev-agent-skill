# System One versus LLM reasoning

Use deterministic code for exact rules, dates, calculations, and known mappings.
Use System One for semantic judgments with known outcomes and enough supplied evidence.
Use the main agent for planning, writing, resolving unclear intent, and gathering missing
context. The delegation itself has a cost: a single obvious selection may not justify
a network call, while repeated semantic triage may.

For tool routing, supply actual available tools and an explicit review/no-match option.
An allowlisted result selects a handler; application code still checks permissions and
valid arguments. Do not execute arbitrary model-provided commands or treat a high
confidence score as user approval.

For ranking, distinguish selecting one candidate (Choice) from evaluating each candidate
against the same rubric (Score). A Score's magnitude measures the requested dimension,
such as relevance or urgency; it does not measure certainty.

## Confidence and escalation

Choice and Score return a confidence statistic derived from their probability distributions.
Preserve it rather than replacing it with the highest probability. Noul reports the
probability of yes and has no confidence property; near 0.5 means the yes/no decision
is unclear. Keep this distinct from medium severity or urgency.

Use three outcomes in your application: continue within authorization, main-agent review,
and main-agent/human handling. The precise thresholds depend on the model, decision,
error costs, and deployment. With no validated policy, return results for agent review.
The [tool-routing example](../examples/tool-routing/README.md) has an opt-in threshold
demonstration; it defaults to review and never runs a tool.

Before enabling automatic routing, label representative held-out cases, measure error
rates and review coverage at candidate thresholds, inspect consequential false positives
and false negatives, and recheck after model/rubric changes. Pin an evaluated model
version or checkpoint when reproducibility matters. Model confidence cannot reveal all
missing evidence or confidently wrong answers.

For email triage, ask independently about reply need, urgency, category, and deeper-review
need. Combine those answers in code; one question cannot read another's output. Send
uncertain cases and failed records to the larger model instead of dropping them.
This may reduce larger-model work, but measure end-to-end latency and cost locally.

See [TypeSafe's confidence guidance](https://docs.typesafe.ai/confidence),
[architecture](architecture.md), and [email triage](../examples/email-triage/README.md).
