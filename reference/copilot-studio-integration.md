# Copilot Studio Integration — Server-Side Schema Extraction

Copilot Studio chat file attachments are ingested as text/OOXML content for
grounding, not as raw binary files. A `.accdb`/`.mdb` file is a proprietary
binary format, so an agent **cannot** read table/column/relationship
structure directly from an attached Access file. Any agent that tries will
fabricate plausible-looking but fictional schema details — this must be
avoided.

The supported pattern is: **attachment → Power Automate flow → Azure
Function (does the real parsing) → schema JSON → agent uses it as ground
truth.**

## Components

1. **`azure-function/function_app.py`** — an HTTP-triggered Azure Function
   that accepts a base64-encoded `.accdb`/`.mdb` file and returns the same
   `schema.json` shape as `scripts/extract_schema.py` (tables, columns,
   types, primary/foreign keys, indexes), plus a `warnings` array. It tries
   `pyodbc` + the Microsoft Access Database Engine driver first, and falls
   back to `mdbtools` CLI output if pyodbc/the driver isn't available.
2. **A Power Automate flow** ("Extract Access Schema") — a thin pass-through
   triggered by Copilot Studio's "When an agent calls the flow" trigger,
   which forwards the attached file to the Azure Function and returns the
   JSON response back to the agent as a tool output.
3. **The Copilot Studio agent** — calls the flow as a **tool**, whenever a
   `.accdb`/`.mdb` file is attached, and treats the returned JSON as the
   only valid source of schema information.

## Deploying the Azure Function

- Host on an Azure Function App in the appropriate government cloud region
  (Azure Government for GCC/GCC High/DoD workloads — do not deploy this to
  a commercial Azure subscription if the source data is government-
  controlled).
- **Windows Function App + pyodbc path (recommended):** install the
  "Microsoft Access Database Engine" redistributable on the host (via
  deployment script or custom image) so `pyodbc` can open `.accdb`/`.mdb`
  files directly. This path preserves primary keys, foreign keys, and
  indexes.
- **Linux Function App + mdbtools path (fallback):** build a custom
  container with `mdbtools` installed. This path extracts tables/columns
  but weakens relationship/key detail — the function flags this with a
  per-table `note` field, and the agent must surface that limitation to the
  user rather than presenting it as complete.
- Set the function's auth level to **Function key** (already configured in
  the code) and keep the key out of source control — store it in the flow
  connection/action configuration, not hard-coded in the repository.

## Building the Power Automate flow

1. Trigger: **Microsoft Copilot Studio** connector → *"When an agent calls
   the flow"*. Add a **File** input parameter (e.g., `file`).
2. Action: **HTTP** (or the **Azure Functions** connector where available in
   your Power Platform region) → `POST` to the function URL with header
   `x-functions-key: <key>` and body:
   ```json
   {
     "fileName": "@{triggerBody()?['file']?['name']}",
     "fileContentBase64": "@{base64(triggerBody()?['file']?['content'])}"
   }
   ```
3. Action: **Respond to Copilot Studio** → return the HTTP response body as
   a string/JSON output (e.g., `schemaJson`).
4. Publish the flow to the same GCC/GCC High/DoD environment as the
   Copilot Studio agent and Dataverse target.

## Wiring the agent

In Copilot Studio: **Tools → Add a tool → Flow**, select "Extract Access
Schema." Then include the following behavior in the agent's instructions:

```text
FILE HANDLING

When the user attaches an .accdb or .mdb file, do not attempt to read it
directly and do not fabricate schema details. Instead, call the "Extract
Access Schema" tool, passing the attached file. Use the returned schema
JSON as the authoritative source for all table, column, relationship, and
index information in your report.

If the tool returns an error, a non-empty warnings array, or an empty
tables list, tell the user exactly what failed (e.g., unsupported file,
corrupt file, extraction driver unavailable) and ask them to confirm the
file or try again — do not invent placeholder schema data as a substitute.

Note: this tool extracts table/column/relationship/index structure only.
Queries, forms, reports, macros, and VBA code are not recoverable from the
binary file this way — continue to ask the user to describe or paste that
logic when needed.
```

## What this does not solve

- **Queries, forms, reports, macros, and VBA** are still not extractable
  this way (neither ODBC nor mdbtools expose them). The agent must keep
  asking the user to describe or paste that logic — do not assume the
  Azure Function's schema JSON is a complete picture of the application.
- This pattern only fixes *schema* discovery. Data migration still requires
  a separate export (e.g., CSV) and import step — see `SKILL.md` Step 3.
