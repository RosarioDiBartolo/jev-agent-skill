# Contributing

Keep this project a small execution companion. Prefer the official SDK and existing
System One shapes; do not introduce an agent framework, hardcoded host, or model weights.
Keep the official TypeSafe skill separate and link to live upstream guidance.

Create a virtual environment and install `skills/system-one-router/requirements.txt`
plus `ruff==0.16.9`. Run `python -m unittest discover -s tests -v`, `ruff check .`,
and `ruff format --check .`. Tests must not require real keys or a GPU. Add meaningful
contract/error tests when changing API behavior and update copyable examples with CLI changes.

Do not include private input, endpoint tokens, or real inbox data in issues or fixtures.
Report the SDK/backend version and a synthetic reproducer when reporting compatibility failures.
Treat live quality/performance results as deployment-specific and document the measurement method.
