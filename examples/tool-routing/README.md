# How to route agent tools using Jev

The [request](request.json) asks for one available search tool, with `review` as the
escape hatch. It uses synthetic text and does not access Gmail or other services.

From the repository root, after [configuration](../../docs/configuration.md):

```bash
python skills/system-one-router/scripts/decide.py examples/tool-routing/request.json > decision.json
python examples/tool-routing/route.py decision.json
```

Check that the first command exits successfully before consuming its output.
The route demonstration defaults to main-agent review, even for high confidence.
Once you have evaluated your policy, supply its two cutoffs:

```bash
python examples/tool-routing/route.py decision.json --medium 0.5 --high 0.9
```

Those numbers illustrate the interface; they are not validated recommendations.
The script returns a proposed route and the raw probabilities. It never calls a tool.
Your application must map the label to an actual allowlisted function and check
authorization. The model selects a tool; the agent still builds valid search arguments.

Use the same pattern to choose among candidate files or records after retrieval has
provided a bounded shortlist. For [rubric ranking](../classification/README.md), use Score.
See [decision policy](../../docs/decision-policy.md) and [Codex integration](../../docs/codex-integration.md).
