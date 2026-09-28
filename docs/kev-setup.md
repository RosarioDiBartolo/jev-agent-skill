# Using Kev as a Jev-compatible server

[Kev](https://github.com/jaredpalmer/kev) supplies its own training and serving tools.
This repository installs only the client skill; it does not download models or provision GPUs.

Current upstream local serving example (requires Kev's Python/GPU environment and `uv`):

```bash
git clone https://github.com/jaredpalmer/kev.git
cd kev
uv sync --extra serve
uv run --extra serve python -m kev.serve --run jaredpalmer/kev-4b --port 8009
```

Follow upstream requirements before running this; its server dependencies differ from
this client's Python 3.10+ requirement. The inspected server supports `POST /v1/systemone`
and `GET /v1/models`. `kev-latest` and `jev-latest` are aliases for the loaded checkpoint;
they do not dynamically select different weights. Model selection happens at server startup.

In a separate client environment set:

```bash
export SYSTEM_ONE_BASE_URL="http://localhost:8009"
export SYSTEM_ONE_API_KEY="local-unused"
export SYSTEM_ONE_MODEL="kev-latest"
```

For a public tunnel or remote GPU, set `KEV_API_KEY` on the **server** and supply the
matching value as `SYSTEM_ONE_API_KEY` on the **client**. The current Kev server checks
bearer authentication when `KEV_API_KEY` is set. With it unset, the server is open;
the SDK still requires an explicit nonempty dummy key. A tunnel alone does not add authentication.

Kaggle + Cloudflare Tunnel, a VPS, RunPod, and other GPU hosts require no client code
changes: expose the same API contract over HTTPS, configure its API root, and account
for cold starts and tunnel expiry. A provider that exposes only `/v1/chat/completions`
requires its own System One adapter. This project does not assume compatibility from
the model name alone.

Run the [quickstart probe](../README.md#quickstart). Then evaluate representative decisions;
wire compatibility is not equivalent accuracy, latency, or calibration. See the
[dated compatibility findings](compatibility.md) and [configuration](configuration.md).
