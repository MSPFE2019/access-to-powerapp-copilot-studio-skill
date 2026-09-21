---
name: access-to-powerapp-codeapp-dataverse-gcc
description: >
  Convert a Microsoft Access database (.accdb/.mdb) into a Power Apps Code App
  (PCF/React + TypeScript, built with the Power Platform CLI) backed by
  Dataverse tables, in a Government Community Cloud (GCC/GCC High) tenant.
  Use whenever a maker or pro-dev asks to modernize/replace an Access
  database with a Power Apps Code App on Dataverse inside a GCC environment.
  Covers schema extraction, Dataverse table/relationship design, data
  migration, Power Fx/TypeScript logic re-implementation, and GCC-specific
  licensing/connector/compliance constraints. Do NOT use for SharePoint-only
  or Canvas App targets, or for commercial (non-GCC) tenants without
  re-checking availability of referenced features.
license: Proprietary internal reference.
---

# Access Database → Power Apps Code App (Dataverse, GCC)

## Overview

Access apps are made of: **Tables** (schema + relationships), **Queries**
(saved SQL/QBE), **Forms** (UI + VBA/macro logic), **Reports** (print
layouts), and **Macros/VBA** (automation). This skill re-platforms all of
that onto **Dataverse** (schema/data/business rules) plus a **Power Apps Code
App** (pro-dev, source-controlled, React/TypeScript + PCF, built and deployed
with the Power Platform CLI — `pac code`), specifically for a **GCC or GCC
High** tenant.

Always read `reference/gcc-considerations.md` before making feature or
connector recommendations — GCC/GCC High have a materially different set of
available connectors, AI/generative capabilities, and compliance boundaries
than the commercial cloud.

## Step 0 — Clarify scope with the user

Ask (don't assume) before proceeding:
1. **Tenant type**: GCC, GCC High, or DoD? (Confirms which connectors/regions/
   compliance rules apply — see `reference/gcc-considerations.md`.)
2. **Access to the source file**: is the `.accdb`/`.mdb` available, or only a
   description of it?
3. **Scope**: full app (all tables/forms/reports) or a specific subset?
4. **Existing Dataverse environment**: does a target GCC Dataverse
   environment already exist, or does one need to be provisioned?
5. **Identity/auth model** for the Code App (Entra ID app registration in the
   GCC tenant, service principal vs. interactive user auth).

## Step 1 — Extract the Access schema

Collect: table list, columns (name, type, size, required, default, validation
rule), relationships (PK/FK, cascade rules), indexes/unique constraints,
lookup fields, query SQL text, and an inventory of forms/reports/macros/VBA
modules.

**Copilot Studio agents cannot parse a binary `.accdb`/`.mdb` file from a
chat attachment directly** — chat file ingestion extracts text/OOXML
content, not proprietary Access binary structures. Never fabricate table,
column, or relationship details when a file can't be read; treat that as a
hard stop, not something to guess around.

There are two supported ways to get a real schema:

1. **Copilot Studio (recommended for this skill's primary scenario):** wire
   up the **"Extract Access Schema"** Power Automate flow, which forwards
   the attached file to an Azure Function that runs `pyodbc`/`mdbtools`
   server-side and returns a `schema.json`-shaped result. See
   `reference/copilot-studio-integration.md` and `azure-function/` for the
   full setup. The agent must call this tool for any attached `.accdb`/
   `.mdb` file — it must not attempt to read the file itself, and must not
   invent placeholder schema data if the tool errors or returns no tables.
2. **Local/CLI use (when working directly in a coding session, not through
   Copilot Studio):** if the `.accdb` file and a Windows + Access/ODBC
   driver (or `mdbtools` cross-platform) are available, run:
   ```bash
   python scripts/extract_schema.py "C:\path\to\database.accdb" --out schema.json
   ```
   This produces the same `schema.json` shape as the Azure Function.

In both cases:
- VBA/macros are not exposed via ODBC or mdbtools; inspect them in the
  Access VBA editor (Alt+F11) or via `Application.SaveAsText`, or have the
  user paste the logic. Neither extraction path recovers VBA/macro code —
  always say so explicitly rather than guessing at form logic.
- If no extraction path is available and the file can't be provided, ask the
  user to export/describe table structures, relationships, and the business
  logic behind key forms/macros instead of assuming a "typical" schema.

## Step 2 — Design Dataverse tables

- One Dataverse table per Access table (skip Access system tables `MSys*`).
- Map data types using `reference/datatype-mapping.md`.
- Recreate relationships as native Dataverse 1:N / N:N relationships;
  explicitly set relationship behavior (Referential / Parental / Cascade) to
  match Access's `Cascade Update/Delete` rather than defaulting.
- Recreate Access unique indexes as Dataverse **alternate keys**.
- Recreate Access validation rules as Dataverse **business rules** or
  server-side plugins, not client-only checks.
- Build all schema changes in a **solution** (unmanaged in dev, managed on
  promotion) and deploy through an approved ALM pipeline appropriate for the
  GCC tenant (see `reference/gcc-considerations.md` for GCC pipeline/DevOps
  connector availability).

## Step 3 — Migrate data

1. Export each Access table to CSV (Access "Export" wizard or `mdb-export`).
2. Import into Dataverse (maker portal "Import from Excel/CSV", or the
   Dataverse Web API/SDK for larger volumes) inside the target GCC
   environment.
3. Do a two-pass import: rows first, then set lookup/relationship values,
   since Dataverse-generated GUIDs differ from Access AutoNumber PKs — keep an
   Access-PK → Dataverse-GUID mapping table during import.
4. Make imports idempotent and resumable; log rejects/duplicates/orphans and
   reconcile row counts against the source.

## Step 4 — Scaffold the Power Apps Code App

Use the Power Platform CLI to scaffold and wire the app to Dataverse — see
`reference/code-app-architecture.md` for the concrete `pac code` commands,
project layout, and generated data-source/model pattern. Key points:

- `pac auth create` against the GCC/GCC High Dataverse environment endpoint
  (note: GCC/GCC High use distinct service endpoints — do not assume
  commercial-cloud URLs).
- `pac code init` / `pac code add-data-source` to generate typed
  TypeScript models and CRUD methods per Dataverse table — do not hand-write
  direct Web API calls when the generated data layer covers the need.
- Structure the React app with one component/page per former Access Form;
  subforms become child components receiving the parent record's key as a
  prop.

## Step 5 — Convert queries, validation, and logic

- Simple `SELECT ... WHERE` → Dataverse **views** with filter criteria, or
  typed query calls in the generated data layer (`filter`, `orderBy`,
  pagination) from TypeScript.
- Queries with JOINs → resolved via Dataverse relationship/lookup expansion
  in the generated API (`$expand`-style), not client-side manual joins.
- Aggregate queries (`GROUP BY`, `SUM`, `COUNT`) → Dataverse calculated/rollup
  columns for persisted aggregates, or aggregate API queries.
- Field/table validation rules → Dataverse business rules (preferred,
  server-side) plus TypeScript-side form validation for immediate UX
  feedback; don't rely on client-only validation as the source of truth.
- VBA event handlers (`Button_Click`, `Form_Load`) → TypeScript event
  handlers in the corresponding component.
- Multi-step processes, scheduled tasks, or external-system logic → Power
  Automate cloud flows (confirm GCC/GCC High availability of the specific
  connector first) or a Dataverse plugin/custom API, not embedded in the
  Code App's client code.
- Large bulk operations (Access `DoCmd.RunSQL` bulk updates) → server-side
  Dataverse batch operations or a flow with batching/retry, not an
  unbounded client-side loop.

## Step 6 — Reports

- Access Reports → Power BI (GCC/GCC High-licensed workspace) for
  grouping/subtotals/charts, or a printable Code App view/export using the
  Dataverse data, or Power Automate "Create file" (PDF) for structured
  printable outputs.

## Step 7 — Validate

- Row counts match between Access tables and migrated Dataverse data.
- Relationships/lookups resolve correctly.
- Re-test key business logic scenarios (validation rules, calculated
  columns, top user workflows) in the Code App.
- Confirm the Dataverse **security role** model (table/column/row-level
  security) — Access had no equivalent; this must be deliberately designed,
  least-privilege, and reviewed, not assumed.
- Test CRUD boundaries as representative users, not just as an admin/maker
  connection.
- Test throttling/retry behavior, Dataverse service protection limits,
  concurrency/conflict handling, and accessibility (keyboard, screen reader,
  contrast).
- Confirm the app registration / auth flow works end-to-end against the GCC
  tenant's Entra ID and Dataverse endpoints before calling migration done.

## GCC-specific guardrails (see `reference/gcc-considerations.md` for detail)

- Verify every connector, AI/Copilot feature, and Power Automate action
  against GCC/GCC High/DoD availability — parity with commercial cloud is
  **not** guaranteed and lags in availability.
- Use GCC-specific service endpoints and regions; never assume commercial
  cloud URLs, app registrations, or DNS suffixes.
- Respect data residency/compliance boundaries (FedRAMP High, DoD IL levels)
  when choosing where data, backups, and logs live.
- Never embed tenant IDs, client secrets, passwords, or endpoint credentials
  in app code, flows, or exported solution packages — use environment
  variables, connection references, and approved identities (service
  principal or managed identity) consistent with GCC security requirements.
- Confirm licensing (Dataverse, premium connectors, Power BI, Copilot Studio
  features) is available and provisioned in the specific GCC/GCC High tenant
  before designing around it.

## Reference files

- `reference/datatype-mapping.md` — Access → Dataverse column type table.
- `reference/gcc-considerations.md` — GCC/GCC High constraints and checklist.
- `reference/code-app-architecture.md` — Power Apps Code App + Dataverse
  scaffolding via `pac code`.
- `reference/copilot-studio-integration.md` — how to wire a Copilot Studio
  agent to the Azure Function + Power Automate flow so attached `.accdb`
  files are actually parsed instead of guessed at.
- `azure-function/function_app.py` — HTTP-triggered Azure Function that
  extracts schema server-side (pyodbc primary, mdbtools fallback), called
  by the Power Automate flow.
- `scripts/extract_schema.py` — local/CLI pyodbc-based schema extractor,
  used outside of Copilot Studio (e.g., in a coding session).

## Notes for the agent

- Always produce a `schema.json` (or equivalent) before proposing table
  designs — never guess at the Access schema. In Copilot Studio, this means
  calling the "Extract Access Schema" tool on any attached `.accdb`/`.mdb`
  file, not reading the attachment directly.
- If schema extraction fails or returns no tables, tell the user exactly
  what failed and ask them to confirm/retry the file. Do not fabricate a
  "typical" or placeholder schema as a substitute — that produces a report
  that looks authoritative but is fiction.
- Always confirm GCC vs. GCC High vs. DoD, and confirm the target Dataverse
  environment, before generating a full migration plan — these are
  foundational and hard to reverse.
- When actually creating Dataverse tables, solutions, or the Code App
  project, hand off to a coding session with the Power Platform CLI (`pac`)
  rather than attempting UI-only creation, unless the user only wants a
  migration plan/document.
