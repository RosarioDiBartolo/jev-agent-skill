# Architecture

An agent loads `system-one-router`, constructs bounded questions, invokes a Python
helper, and consumes the typed response. The helper configures the official TypeSafe
Python SDK, which sends `POST /v1/systemone` to the selected API root. A Jev/Kev backend
returns an answer per question; the agent applies policy and continues its workflow.

`common.py` contains configuration, input checks, SDK invocation, and response-ID/option
checks. `decide.py` processes one request. `batch_decide.py` streams records sequentially
through one persistent client. `health.py` tests real inference with a tiny Noul.
The skill folder is self-contained when installed without the rest of the repository.

The SDK owns HTTP transport, typed schema validation, timeout behavior, and optional
bounded retries. The project supplies no alternate HTTP stack or provider registry.
All three main configuration variables are required: it never silently falls back
to TypeSafe's hosted endpoint or inherits an unrelated `TYPESAFE_API_KEY`.

Several questions about the same state share one call. Separate records use separate
calls; v1's batch helper is deliberately sequential. It saves orchestration overhead
through connection reuse but makes no claim of GPU batching or measured speedup.

The boundary is a judgment, not a tool call. A selected tool must be mapped to an
existing allowlist and remain within the original task's authorization. Untrusted
documents cannot add tool permissions. Errors stay explicit, and uncertain or incomplete
cases return to the main agent. No automatic agent-to-agent recursion is used.

See [decision policy](decision-policy.md), [configuration](configuration.md),
[compatibility](compatibility.md), and [the overview](../README.md).
