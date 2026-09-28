# Execution reference

Install with `python -m pip install -r <skill-dir>/requirements.txt`.
All scripts accept `--help`. JSON output goes to stdout; fatal errors go to stderr.
Success exits 0; configuration, input, service, or partial batch failure exits 1;
invalid CLI usage exits 2. No script executes the selected action.

## Configuration

| Variable | Meaning |
| --- | --- |
| `SYSTEM_ONE_BASE_URL` | Required API root, such as `http://localhost:8009`; no `/v1` suffix |
| `SYSTEM_ONE_API_KEY` | Required bearer token; explicitly use `local-unused` only for an unauthenticated local server |
| `SYSTEM_ONE_MODEL` | Required backend model name, such as `kev-latest` or `jev-latest` |
| `SYSTEM_ONE_TIMEOUT` | Positive seconds per HTTP operation, default 30; not a total batch deadline |
| `SYSTEM_ONE_MAX_RETRIES` | 0–5 SDK retries, default 0; retries can add latency and duplicate inference cost |

These values are explicitly passed to the official SDK and override its `TYPESAFE_*`
defaults. Nothing loads `.env` automatically. HTTPS is recommended for remote endpoints.
The SDK requires a nonempty key even when a local Kev server ignores authentication.
Keep secrets out of command arguments and request JSON. SDK debug logging can expose state.

## Request

```json
{
  "state": {"message": "Please confirm the delivery date today."},
  "questions": {
    "reply": {"type": "noul", "instructions": "Does the sender request a reply?"},
    "category": {
      "type": "choice",
      "instructions": "Which category best describes the message?",
      "criteria": {"delivery": "Shipping or delivery", "other": "Anything else"}
    },
    "urgency": {
      "type": "score",
      "instructions": "How soon does the message explicitly require action?",
      "criteria": ["No deadline stated", "Action needed this week", "Action needed today"]
    }
  }
}
```

Use 2–255 Choice options and 2–10 ordered Score levels. Noul optionally accepts
`criteria` with `"true"` and `"false"` descriptions. Instructions may be strings,
objects, or arrays. Top-level fields are exactly `state` and `questions`; the model
comes from the environment. `--validate-only` checks the local envelope and basic
shapes; the SDK/backend performs remaining semantic and schema validation.

The response retains the SDK's `model`, `answers`, and `usage` fields. Each Choice
answer has `choice`, `probabilities`, and `confidence`; each Noul has `noul`; each
Score has `score`, `legend`, `probabilities`, and `confidence`. Scores use zero-based
level indices and can fall between levels. There is no invented normalized confidence.

## Batch

Each JSONL line is the same request with an additional nonempty string `id`.
IDs should be unique in your application; line numbers disambiguate repeated IDs.
Success: `{"id":"mail-1","line":1,"ok":true,"result":{...}}`.
Failure: `{"id":"mail-1","line":1,"ok":false,"error":"..."}`.
Malformed JSON has a null ID. Blank lines are skipped. Processing is sequential,
not a provider bulk API, and retains only one record at a time. Earlier results
remain available if a later record fails. A fatal setup error produces no decisions.

## Troubleshooting

- Missing configuration: set all three required variables in the agent's process.
- 401/403: check the token and gateway access policy.
- 404: use the API root, confirm `/v1/systemone` exists and the model is accepted.
- 422: compare your questions with the backend's supported System One schema.
- 429/529: reduce rate or enable bounded SDK retries.
- Timeout: check the GPU process, cold start, and tunnel; increase the timeout if appropriate.
- HTML response: a tunnel login or gateway challenge is intercepting the request.
- Invalid response: return to agent review; do not consume unvalidated decisions.

For new backends, inspect [the current API contract](https://docs.typesafe.ai/api)
and run the inference probe. OpenAI-style chat completions alone are not compatible.
