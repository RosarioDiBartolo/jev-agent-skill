# Custom System One endpoints

The [execution reference](../skills/system-one-router/references/execution.md#configuration)
is the canonical variable and CLI reference. Copy [.env.example](../.env.example) for
your own environment manager; the scripts do not load it automatically. Never commit
the resulting `.env` or share credentials in request JSON.

| Deployment | `SYSTEM_ONE_BASE_URL` | `SYSTEM_ONE_MODEL` | Key |
| --- | --- | --- | --- |
| Local Kev | `http://localhost:8009` | `kev-latest` | Explicit dummy only when auth is disabled |
| Remote Kev / Kaggle tunnel / GPU provider | Your HTTPS API root | Name accepted by that server | Server bearer token |
| TypeSafe hosted Jev | `https://api.typesafe.ai` | `jev-latest` or evaluated version | TypeSafe API key |
| Future compatible backend | Its documented API root | Its documented name | Its bearer token |

The SDK appends `/v1/systemone`. Root paths behind a reverse proxy are supported when
the proxy exposes `<root>/v1/systemone`. Trailing slashes are removed. Endpoint URLs
with embedded credentials, queries, or fragments are rejected. Remote HTTP is possible
but does not encrypt the state or bearer token; use HTTPS for hosted deployments.

Authentication is bearer-only in v1. Cloudflare Access service-token headers and
browser login cookies are not configured by these scripts. Put a compatible
authentication layer in front of the server or extend the adapter explicitly.
Changing tunnel URLs must be reflected in the process environment.

Timeout defaults to 30 seconds per HTTP operation; it is not a wall-clock batch limit.
Retries default to zero to keep interactive delegation bounded. Set
`SYSTEM_ONE_MAX_RETRIES` to 1–5 if the workload benefits from the SDK's backoff policy.
A retry after an uncertain network failure can repeat inference and incur cost.

The helpers return safe error messages without dumping backend bodies or keys. Avoid
enabling SDK debug logging for private state. Keep generated batch output outside
Git (the `results*.jsonl` pattern is ignored) and apply your application's data policy.

Run `python skills/system-one-router/scripts/health.py` after configuration. It verifies
a valid Noul response, not model quality or calibrated correctness. A generic `/health`
route is not required. See [Kev setup](kev-setup.md) and [troubleshooting](../skills/system-one-router/references/execution.md#troubleshooting).
