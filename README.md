# Access DB → Power Apps Code App (Dataverse) — Copilot Studio Skill

This repo packages a reusable skill/reference for converting a Microsoft Access
database (`.accdb`/`.mdb`) into a **Power Apps Code App** (PCF/React + TypeScript,
built with the Power Platform CLI) backed by **Dataverse tables**, for use in
**Government Community Cloud (GCC) / GCC High** environments.

It is written to be imported or referenced by a **Microsoft Copilot Studio**
custom agent (as knowledge, a topic's instructions, or grounding content for a
generative action) so the agent can guide a maker or pro-dev through the
conversion with GCC-appropriate guardrails.

## Contents

- [`SKILL.md`](./SKILL.md) — the primary instruction set: step-by-step
  conversion process from Access schema → Dataverse tables → Power Apps Code
  App, written for an LLM-driven agent to follow.
- [`reference/datatype-mapping.md`](./reference/datatype-mapping.md) — Access →
  Dataverse column type mapping table.
- [`reference/gcc-considerations.md`](./reference/gcc-considerations.md) — GCC /
  GCC High specific constraints: environment regions, licensing, connector
  availability, compliance boundaries.
- [`reference/code-app-architecture.md`](./reference/code-app-architecture.md) —
  Power Apps Code App project structure and Dataverse data-source wiring via
  the Power Platform CLI (`pac code`).
- [`scripts/extract_schema.py`](./scripts/extract_schema.py) — pyodbc-based
  Access schema extractor producing `schema.json` (tables, columns, types,
  relationships, indexes) as the working document for the conversion.

## Using this with Copilot Studio (GCC)

1. Add this repo's raw file URLs (or an exported copy of `SKILL.md` +
   `reference/*.md`) as a **knowledge source** on a Copilot Studio custom
   agent/topic dedicated to Power Platform modernization.
2. Instruct the agent's topic/prompt to follow `SKILL.md` step-by-step and to
   ask the maker clarifying questions (scope, environment, licensing) before
   generating a migration plan.
3. Because generative/agentic connectors and knowledge sources available in
   GCC/GCC High differ from commercial cloud, verify each referenced
   connector or capability against `reference/gcc-considerations.md` and your
   tenant's Power Platform admin center before use.

## License

Proprietary internal reference. Adjust licensing before external distribution.
