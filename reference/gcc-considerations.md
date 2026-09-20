# GCC / GCC High Considerations for Copilot Studio + Power Apps Code Apps

This file lists the constraints an agent (or human) must check before
recommending or implementing any part of the Access → Power Apps Code App
(Dataverse) conversion inside a **Government Community Cloud** tenant.

## Tenant tiers — confirm which one applies

| Tier | Typical use | Compliance | Notes |
|---|---|---|---|
| GCC | US government contractors / agencies, moderate impact data | FedRAMP Moderate | Closest to commercial cloud feature-wise, but still lags on new releases. |
| GCC High | DoD IL4/5-adjacent, ITAR/CUI data | FedRAMP High, DoD IL4/5 | Physically/logically isolated US-only datacenters and personnel; narrower connector/feature set than GCC. |
| DoD | Department of Defense | DoD IL5/IL6 | Most restrictive; smallest feature/connector surface. |

Always ask which tier applies — do not assume GCC when the user says
"government cloud"; GCC High and DoD have materially fewer available
features and different endpoints.

## Endpoints and identity

- GCC/GCC High/DoD environments use **distinct service endpoints and
  regions** from commercial cloud (e.g., `.us` / government-specific
  Dataverse and Power Platform admin center URLs). Never copy commercial
  cloud URLs, sample app registrations, or redirect URIs into a GCC project.
- Entra ID (Azure AD) app registrations for the Code App's authentication
  must be created in the **same GCC/GCC High/DoD tenant** as the target
  Dataverse environment.
- Use `pac auth create` with the correct `--cloud` / environment flag for
  the tenant tier being targeted; verify the currently supported CLI syntax
  against the Microsoft Learn documentation for the tenant's Power Platform
  CLI version, since exact flags change across releases.

## Connector and feature availability

- **Do not assume feature parity with commercial Power Platform.** Copilot
  Studio's generative AI features, many premium/standard connectors, and
  newly released Power Platform capabilities are frequently unavailable or
  released later in GCC, and are more restricted still in GCC High/DoD.
- Before recommending a specific connector (e.g., Power Automate premium
  connectors, custom connectors, AI Builder, generative Copilot Studio
  actions) confirm its current availability for the specific tenant tier via
  the Power Platform admin center and official Microsoft GCC service
  description documentation — do not rely on general/commercial-cloud
  documentation alone.
- Prefer standard, natively supported Dataverse and Power Platform CLI
  capabilities over premium/custom connectors when an equivalent exists, to
  reduce licensing and availability risk in GCC High/DoD.

## Compliance and data handling

- Respect data residency: GCC/GCC High/DoD environments are US-based;
  ensure the Dataverse environment, backups, and any Power BI/reporting
  workspace used for the migrated data are provisioned in the matching
  government cloud instance, not a commercial tenant.
- Treat CUI/ITAR-flagged data (common in GCC High/DoD scenarios) as requiring
  explicit review of column-level security, sharing, and export controls
  before building any report, export, or integration.
- Never embed tenant IDs, client secrets, connection strings, or credentials
  in Code App source, Power Automate flows, or exported solution packages —
  use environment variables, connection references, and an approved
  identity (service principal / managed identity) consistent with the
  tenant's security requirements.

## ALM and licensing

- Confirm Dataverse and any premium connector licensing is actually
  provisioned in the target GCC/GCC High/DoD tenant before designing a
  solution around it — license SKUs and availability differ from commercial
  cloud.
- Use solutions (unmanaged in dev, managed on promotion) and an approved
  ALM/DevOps pipeline compatible with the tenant tier; confirm Azure DevOps
  or GitHub Actions connectivity/availability for the specific GCC/GCC
  High/DoD environment rather than assuming commercial-cloud CI/CD patterns
  apply unchanged.

## Checklist before implementation

1. Confirmed tenant tier (GCC / GCC High / DoD).
2. Confirmed Dataverse environment region/URL and that it is provisioned.
3. Confirmed Entra ID app registration exists in the same tenant.
4. Verified availability of every connector/feature referenced in the plan
   against current Microsoft GCC service description docs.
5. Confirmed licensing for Dataverse/premium connectors/Power BI/Copilot
   Studio features actually in the tenant.
6. Confirmed data residency and compliance requirements (FedRAMP tier,
   ITAR/CUI handling) are satisfied by the chosen design.
