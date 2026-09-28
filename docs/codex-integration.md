# How to use Jev and Kev with Codex

Install the skill with the commands in the [quickstart](../README.md#integrating-jev-with-codex-and-claude-code).
The optional official TypeSafe companion teaches judgment design; keep its folder separate.

For manual project installation, copy the complete `skills/system-one-router` directory
to `<your-project>/.agents/skills/system-one-router`. For user-wide Codex installation,
use `~/.agents/skills/system-one-router`. These are the locations documented in
[OpenAI's current skill guide](https://learn.chatgpt.com/docs/build-skills).
Claude Code's corresponding locations are `.claude/skills/` and `~/.claude/skills/`;
see its [skill documentation](https://code.claude.com/docs/en/skills).

Use a Python 3.10+ virtual environment and install the copied `requirements.txt` there.
The agent must call that interpreter, or inherit its activated environment. Scripts
resolve their sibling imports independently of the current working directory.

Set `SYSTEM_ONE_BASE_URL`, `SYSTEM_ONE_API_KEY`, and `SYSTEM_ONE_MODEL` in the process
that runs the agent's shell. A desktop app does not necessarily inherit variables
set later in a separate terminal. Configure its launch environment and start a fresh
session if needed. Do not put a real key in `SKILL.md` or `AGENTS.md`.

Ask:

> Use $system-one-router to triage these synthetic support messages with my configured Kev server. Return the raw judgments, flag uncertain cases for your review, and do not send replies.

The agent writes `{state, questions}`, invokes the installed helper by its actual path,
and reads JSON stdout and the exit status. It should invoke `--validate-only` to check
a request without sending data, or `health.py` to test inference. Failed records must
remain visible, not disappear into an “ignore” bucket.

This is a tool-using skill, not a model replacement, background service, MCP server,
or Codex settings override. Installing it does not redirect every Codex decision.
Ordinary deterministic work and open-ended reasoning remain with the appropriate executor.
See [tool routing](../examples/tool-routing/README.md) and [decision policy](decision-policy.md).
