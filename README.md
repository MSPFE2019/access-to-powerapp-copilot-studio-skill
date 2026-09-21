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
- [`reference/copilot-studio-integration.md`](./reference/copilot-studio-integration.md) —
  **required reading**: Copilot Studio cannot parse a binary `.accdb`/`.mdb`
  chat attachment directly. This explains the Azure Function + Power
  Automate flow pattern that actually extracts real schema data for the
  agent to use, instead of it fabricating a "typical" schema.
- [`azure-function/function_app.py`](./azure-function/function_app.py) —
  HTTP-triggered Azure Function (pyodbc primary, mdbtools fallback) that
  performs the real server-side schema extraction called by the flow.
- [`scripts/extract_schema.py`](./scripts/extract_schema.py) — pyodbc-based
  local/CLI Access schema extractor producing `schema.json` (tables,
  columns, types, relationships, indexes), for use outside Copilot Studio
  (e.g., in a coding session with direct file access).

## Using this with Copilot Studio (GCC)

1. Add this repo's raw file URLs (or an exported copy of `SKILL.md` +
   `reference/*.md`) as a **knowledge source** on a Copilot Studio custom
   agent/topic dedicated to Power Platform modernization.
2. Deploy `azure-function/function_app.py` and build the "Extract Access
   Schema" Power Automate flow per
   `reference/copilot-studio-integration.md`, then add that flow as a
   **tool** on the agent. This is required for the agent to get a real
   schema from an attached `.accdb`/`.mdb` file instead of guessing.
3. Instruct the agent's topic/prompt to follow `SKILL.md` step-by-step, to
   call the schema-extraction tool for any attached Access file, and to
   never fabricate placeholder schema data if extraction fails.
4. Because generative/agentic connectors and knowledge sources available in
   GCC/GCC High differ from commercial cloud, verify each referenced
   connector or capability against `reference/gcc-considerations.md` and your
   tenant's Power Platform admin center before use.

## License

Proprietary internal reference. Adjust licensing before external distribution.
