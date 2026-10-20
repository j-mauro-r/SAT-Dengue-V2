# .agents

This directory is the local, cross-agent harness for SAT-Dengue-V2.

- `agents/`: reusable worker personas.
- `commands/`: thin command delegators.
- `skills/`: installed skills (DeepWorkPlan and addons).
- `docs/`: catalog of available commands/agents/skills.
- `settings.json`: informational preferences; the present custom keys have no enforcing consumer in repository code/CI. Host-specific settings must not be assumed to enforce validation or commit approval.

Load [the skill/agent catalog](docs/skills_agents_catalog.md) or [command reference](docs/COMMANDS_REFERENCE.md) on demand. Optional personas are lightweight guidance, not deployed services or a requirement to spawn a team for each task. `.claude` and `.cursor` expose the same files; do not maintain duplicate copies. The root `AGENTS.md` and its linked owners supply project policy; vendored skill manuals supply tool-specific workflows.
