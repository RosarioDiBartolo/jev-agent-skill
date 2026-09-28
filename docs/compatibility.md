# Compatibility research

Inspected on **2026-09-28** before implementation. These are contract findings, not
live model-quality results. Recheck upstream when updating the pinned dependency.

| Source | Finding and v1 decision |
| --- | --- |
| [Official TypeSafe skill](https://github.com/typesafe-ai/skills/blob/65a39f393687675ce170e6094757de20370365b9/skills/typesafe-ai/SKILL.md) | Judgment design and composition belong upstream; recommend installing it separately. No files copied or modified. |
| [TypeSafe HTTP API](https://docs.typesafe.ai/api) | POST `/v1/systemone`, with state, model, and named questions; answers are Choice, Noul, or Score. Use these native shapes. |
| [Python client](https://github.com/typesafe-ai/typesafe-sdk-python/blob/f078f1e208a0d885154dc758344ae4fce77ac168/src/typesafe_sdk/_core/client/sync/client.py) | Public `base_url`, `api_key`, `model`, `timeout`, and `retry` arguments make custom endpoints straightforward. Use the official `typesafe-sdk==0.7.2`. |
| [JavaScript client options](https://docs.typesafe.ai/sdk/javascript/api/interfaces/TypeSafeClientConfig) | Also supports custom `baseURL`, `apiKey`, and `defaultModel`. Python alone is sufficient for the small v1 CLI. |
| [Kev server](https://github.com/jaredpalmer/kev/blob/3e1cd3bb588a388a06827443380befece23e68c7/kev/serve.py) and [API mapping](https://github.com/jaredpalmer/kev/blob/3e1cd3bb588a388a06827443380befece23e68c7/kev/api.py) | Compatible route, bearer auth via `KEV_API_KEY`, and `kev-latest`/`jev-latest` aliases for loaded weights. Its broader accepted inputs do not widen this companion's common contract. |
| [Agent Skills specification](https://agentskills.io/specification) | Named folder with matching frontmatter, concise instructions, and optional scripts/references. The skill stays portable and self-contained. |
| [OpenAI skill guide](https://learn.chatgpt.com/docs/build-skills) and [Claude Code guide](https://code.claude.com/docs/en/skills) | Document the appropriate manual installation directories and automatic/explicit invocation. |

## Coupling avoided and retained

The official SDK defaults to TypeSafe's host/model and requires a key. This companion
requires all three `SYSTEM_ONE_*` settings and passes them explicitly. No accidental
provider fallback occurs; an open local Kev server needs an explicit dummy key.
There is no TypeSafe account requirement when using your own compatible backend.

Remaining intentional coupling is to the System One v1 wire contract and its Python SDK.
The package pin makes reviewed behavior reproducible at the direct-dependency level;
transitive dependencies are resolved by pip. Gateway-specific headers, OpenAI chat
completions adapters, training, server deployment automation, and provider-native bulk
APIs are outside v1. Custom endpoint support does not imply every service implements
the contract, nor that Jev and Kev have equivalent outputs or calibration.

The wrapper retains distributions and backend confidence rather than recalculating
confidence. It checks answer IDs, types, option sets, numeric ranges, and distribution
sums (within 0.02 to allow wire rounding). Testing found that the SDK alone accepts
some out-of-range numeric responses, so the adapter checks those explicitly.

## Validation boundary

Automated tests use the installed official SDK with mock transport and a local HTTP
server. They cover endpoint composition, bearer headers, all three primitives, CLI
execution outside the repository, batch record errors, and service failures. No live
Jev or Kev inference was performed during initial implementation. Run `health.py`
against your deployment and evaluate representative labeled cases before automatic use.

See [configuration](configuration.md), [Kev setup](kev-setup.md), and [architecture](architecture.md).
