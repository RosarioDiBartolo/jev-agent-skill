# GitHub issue classification and prioritization with Kev or Jev

```bash
python skills/system-one-router/scripts/decide.py examples/classification/request.json
```

Run from the repository root after [configuration](../../docs/configuration.md).
The synthetic request separates category (Choice) from reported impact (Score).
The three Score levels are indexed 0, 1, and 2; an answer may lie between them.
The full probability distribution and confidence remain available for review.

To rank several issues, reuse the same impact rubric on each record, sort the returned
scores in ordinary code, and review uncertain cases. Add known business rules in code;
the model cannot infer facts absent from the issue text. No GitHub issue is modified.
See [tool selection](../tool-routing/README.md) for closed-set routing and
[batch triage](../email-triage/README.md#batch-triage) for multiple records.
