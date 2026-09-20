# Power Apps Code App + Dataverse — Architecture & Scaffolding

Power Apps Code Apps are pro-dev, source-controlled apps (React/TypeScript,
using PCF component infrastructure) built and deployed with the **Power
Platform CLI** (`pac`). This reference covers the concrete scaffolding
pattern for wiring a Code App to Dataverse tables.

> Verify exact `pac` command syntax against the current Microsoft Learn
> documentation for Power Apps Code Apps before running — CLI commands and
> flags evolve across releases, and GCC/GCC High tenants may require
> specific auth/cloud flags (see `gcc-considerations.md`).

## Typical workflow

1. **Authenticate against the target (GCC/GCC High/DoD) Dataverse
   environment:**
   ```bash
   pac auth create --environment <environment-id-or-url>
   ```
   Confirm the correct cloud/authority flag for the tenant tier; do not
   reuse commercial-cloud auth profiles.

2. **Initialize a Code App project:**
   ```bash
   pac code init --displayName "MyAccessMigrationApp"
   ```
   This scaffolds a React/TypeScript project with the Power Platform code
   app SDK wired in.

3. **Add each Dataverse table as a typed data source:**
   ```bash
   pac code add-data-source --dataSource dataverse --table <logical-name>
   ```
   This generates typed TypeScript models and CRUD/query methods for the
   table — use these generated methods rather than hand-writing direct
   Dataverse Web API calls, so query shaping, delegation, and typing stay
   consistent and maintainable.

4. **Build the UI as React components,** one per former Access Form:
   - Data-entry forms → a component bound to the generated data source's
     create/update methods, with client-side validation supplementing
     (not replacing) Dataverse business rules.
   - Subforms/master-detail → child components receiving the parent
     record's primary key as a prop, querying the related table filtered by
     that key.
   - Navigation/switchboard forms → top-level routing/menu components.

5. **Re-implement queries** using the generated data source's query API
   (filter, sort, expand related/lookup fields, pagination) instead of
   loading whole tables into client memory.

6. **Push/deploy:**
   ```bash
   pac code push
   ```
   Confirm the target environment is correct (GCC/GCC High/DoD, not a
   commercial sandbox) before pushing.

## Project structure guidance

- Keep one folder per former Access Form/table domain (e.g.,
  `src/features/customers/`), containing the component(s), any
  feature-specific hooks, and tests.
- Keep the generated Dataverse data-source/model code separate from
  hand-written business logic so regenerating a data source doesn't clobber
  custom code.
- Centralize environment-specific configuration (Dataverse environment URL,
  app registration client ID) in environment variables / configuration
  files that are excluded from source control or use connection references,
  never hard-coded secrets.

## Testing and validation

- Unit test TypeScript business logic (validation, calculated display
  values) independent of the Dataverse connection.
- Integration-test CRUD flows against a **non-production** Dataverse
  environment before promoting to production.
- Validate the app under the least-privileged security role a real end user
  will have — do not test only with an admin/maker connection.
