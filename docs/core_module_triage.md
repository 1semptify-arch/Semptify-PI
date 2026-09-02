# Core Module Inventory + PI Plugin Triage

**Date:** 2026-09-02

**Scope:** planning only. This document inventories Semptify Core's product-manifest modules and triages each one for possible conversion to a Semptify-PI plugin. It does **not** implement any plugins.

**Method:** Source is `app/core/product_manifest.py` in Semptify Core. Modules are grouped by package. Triage categories are:

- **Plugin-suitable** — general-purpose, not case/evidence/UPL/court-sensitive, reasonable to expose through an external plugin.
- **Core-only** — touches case-specific tenant data, UPL-sensitive output, evidentiary chain-of-custody, or court-facing filings.
- **Unclear** — genuinely ambiguous; needs Brad's judgment before conversion.

## Triage summary

| Category | Count |
|---|---|
| Plugin-suitable | 9 |
| Core-only | 89 |
| Unclear | 20 |

## Full inventory and triage

| Module package | Tier(s) | Routers / tags | Flags | Triage | Rationale |
|---|---|---|---|---|---|
| `actions` | extended | Smart Actions | case_data, upl | Unclear | Smart actions; could be automation or legal actions. |
| `admin_console` | admin | Admin Console, Module Flags | — | Core-only | Admin console and module flags. |
| `advanced` | admin | Advanced / Dev Tools | — | Core-only | Admin dev/audit tools. |
| `advocate` | advocate | Advocate, Case Management, Clients | case_data | Core-only | Advocate case management. |
| `agent_orchestrator` | dev | Agent Orchestrator | — | Core-only | Agent orchestrator. |
| `analytics` | admin | Analytics | — | Core-only | Usage/performance analytics. |
| `auth` | core | Authentication | identity | Core-only | Authentication / session status. |
| `batch` | admin | Batch Operations | case_data | Core-only | Bulk document operations. |
| `briefcase` | core | Briefcase | case_data | Core-only | Document annotations and briefcase. |
| `calendar` | dev | Calendar | case_data | Core-only | Calendar aggregating case/tenant data. |
| `campaign` | research | Campaign Orchestration | — | Unclear | Campaign orchestration; not clearly cloud-storage related. |
| `capabilities` | admin | Capabilities | — | Core-only | Capability/overlay management. |
| `case_builder` | extended | Case Builder | upl, case_data | Core-only | Case builder (UPL MEDIUM). |
| `cloud_sync` | research | Cloud Sync | case_data, pii | Unclear | User-controlled data sync; overlaps PI's purpose and may move too much PII. |
| `communication` | advocate | Communications | case_data, pii | Core-only | Tenant/advocate communications. |
| `complaints` | extended | Complaint Wizard | upl, court | Core-only | Regulatory complaint-filing wizard. |
| `contacts` | core | Contact Manager | case_data, pii | Core-only | Tenant contact manager. |
| `context_engine` | core | Context Engine, Facts, Stories | case_data | Core-only | Verified facts and tenant stories. |
| `context_loop` | dev | Context Loop | — | Core-only | Runtime state/event loop. |
| `core_system` | core | Core System | — | Core-only | Core system router. |
| `correspondence` | admin | Correspondence | case_data | Core-only | Admin correspondence. |
| `court_forms` | extended | Court Forms | upl, court | Core-only | Court form generation (HIGH UPL). |
| `court_packet` | extended | Court Packet | upl, court | Core-only | Court packet assembly. |
| `crawler` | research | Crawler | — | Unclear | Web crawler; not clearly aligned with tenant cloud storage. |
| `dashboard` | admin | Unified Dashboard | — | Core-only | Unified dashboard. |
| `data_freshness` | core | Data Freshness | — | Unclear | Resource staleness tracker; may be internal or a public monitoring plugin. |
| `dev_lab` | dev | Dev Ideas, Dev Lab | — | Core-only | Dev lab / incubator. |
| `development` | dev | Development Tools | — | Core-only | Development tools. |
| `dispute_tracker` | extended | Dispute Tracker | case_data | Core-only | Property-management dispute tracking. |
| `document_center` | dev | Document Center | case_data | Core-only | 3-pane document viewer GUI. |
| `document_converter` | core | Document Converter | — | Plugin-suitable | Document format conversion operating on provider-stored files. |
| `document_delivery` | advocate | Document Delivery | case_data | Unclear | Document delivery to third parties; high privacy sensitivity. |
| `documentation` | dev | API Documentation | — | Core-only | API documentation. |
| `documents` | core | Documents | case_data | Core-only | Tenant document metadata and upload. |
| `emotion` | research | Emotion Engine | — | Core-only | Experimental emotion engine. |
| `enterprise_dashboard` | admin | Enterprise Dashboard | — | Core-only | Enterprise dashboard. |
| `eviction_defense` | extended | Eviction Defense Toolkit | upl, court | Core-only | Eviction defense toolkit (HIGH UPL). |
| `eviction_timeline` | core | Eviction Timeline | case_data | Core-only | Eviction case timeline (T2). |
| `example_payment_tracking` | dev | Payment Tracking | — | Core-only | Dev-only payment tracking. |
| `export_import` | dev | Data Export/Import | pii | Core-only | GDPR data export/import. |
| `external_mappings` | extended | Agencies, Court Cases, External Mappings, Properties | case_data | Core-only | Cross-system case/property/agency ID mappings. |
| `extraction` | research | Form Field Extraction | case_data | Unclear | Form field extraction; same tension as recognition. |
| `fems` | extended | FEMS | evidence | Core-only | Forensic evidence management (chain of custody). |
| `filedored` | dev | Filedored | — | Unclear | Virtual document organization; concept undefined. |
| `form_data` | research | Form Data Hub | case_data | Core-only | Form data hub for cases. |
| `fraud_exposure` | research | Fraud Exposure | case_data | Unclear | Fraud exposure; may publish case data. |
| `free_api` | core | Free APIs | public_data | Unclear | Mixed public lookups (property, violations, statutes) with court scraper. Needs split decision. |
| `functionx` | research | FunctionX | — | Core-only | Undefined FunctionX concept. |
| `funding_mgmt` | admin | Funding Management | — | Core-only | Admin funding prospectus. |
| `funding_search` | research | Funding & Tax Credit Search | public_data | Plugin-suitable | Public funding and tax-credit search; plugin can save results to provider storage. |
| `guided_intake` | extended | Guided Intake | case_data | Core-only | Guided case/document intake. |
| `health` | core | Health | — | Core-only | System health/status endpoints. |
| `housing_accountability` | extended | Housing Accountability, Pattern History | upl, case_data | Core-only | Fee-pattern detection and legal basis. |
| `hud_funding` | research | HUD Funding Guide | public_data | Plugin-suitable | HUD funding guide; plugin can export guide snippets or bookmarks. |
| `intake` | extended | Document Intake | case_data | Core-only | Document intake. |
| `inventory` | dev | Inventory Management | — | Unclear | File rotation/dating; unclear tenant value and PII implications. |
| `invite_codes` | advocate | Invite Codes | identity | Core-only | Advocate/collaboration invite system. |
| `journal` | core | Journal | case_data | Core-only | Tenant journal and contemporaneous notes. |
| `judge` | dev | Deprecated, Judge, Merged Into Legal | — | Core-only | Deprecated judge role stub. |
| `law_library` | core | Law Library | public_data | Plugin-suitable | Public law reference; plugin can bookmark/annotate references in provider storage. |
| `legal` | extended | Court Filing, Discovery, Exhibits, Legal, Workspace | upl, court | Core-only | Legal workspace (filings, discovery, exhibits). |
| `legal_analysis` | core | Legal Analysis | upl | Core-only | Legal analysis output (UPL risk). |
| `legal_filing_module` | dev | Legal Filing | court | Core-only | Legal filing router. |
| `legal_trails` | extended | Legal Trails | upl, court | Core-only | Legal trails / evidence tracking. |
| `litigation_intelligence` | research | Litigation Intelligence | upl, court | Core-only | Litigation intelligence. |
| `location` | research | Location | public_data | Plugin-suitable | Property/location lookup; plugin can save location research to provider storage. |
| `manager` | admin | Bulk Ops, Case Assignment, Manager, Reporting | case_data | Core-only | Case assignment and bulk ops. |
| `mndes` | core | MNDES | court | Core-only | MN court exhibit system. |
| `module_hub` | research | Module Hub | — | Core-only | Experimental module hub. |
| `onboarding` | core | Onboarding, Reconnect | identity | Core-only | Onboarding and storage reconnect. |
| `packet_builder` | core | Packet Builder | case_data, evidence | Core-only | Curated case/evidence packet export. |
| `page_composer` | core | Case, Facts, Page Composer, Stories | case_data | Core-only | Unified page/case view. |
| `page_editor` | dev | Page Editor | — | Core-only | Static/Jinja2 template editor. |
| `page_index` | dev | Page Index | — | Core-only | Page index. |
| `page_shell` | core | Page Shell, Pillar Mixer | — | Core-only | Pillar-mixer rendering engine. |
| `pdf_tools` | core | PDF Tools | — | Plugin-suitable | PDF manipulation utilities operating on provider-stored files. |
| `plan_maker` | extended | Plan Maker | upl | Unclear | Plan maker; could be generic task planning or legal/case planning. |
| `portal` | core | Portal, Public, SEO, Services | — | Core-only | Public guest portal. |
| `preamble` | core | Preamble | — | Core-only | Entry point / preamble routing. |
| `preview` | core | Document Preview | case_data | Unclear | Document preview; could be a provider-side plugin but currently a Core UI component. |
| `progress` | extended | Progress Tracker | case_data | Unclear | Progress tracker; could be generic but currently tied to case workflows. |
| `public_exposure` | research | Public Exposure | case_data | Unclear | Public exposure tool; may publish case data. |
| `public_forms` | core | Public Forms | upl | Unclear | Public forms; may generate legal documents from case data or be reference-only. |
| `recognition` | research | Document Recognition | case_data | Unclear | Document recognition; could run locally on provider files but is case-data-adjacent. |
| `registry` | admin | Document Registry | case_data | Core-only | Document registry. |
| `rent` | core | Rent Ledger | case_data, pii | Core-only | Tenant rent ledger with financial data. |
| `research` | research | Research Module | public_data | Plugin-suitable | Landlord/property research; plugin can save reports to provider storage. |
| `resource_directory` | core | Resource Directory | public_data | Plugin-suitable | Community resource directory; plugin can export curated resource lists to provider storage. |
| `risc` | core | RISC | — | Core-only | Internal routing/role intake. |
| `role_ui` | core | Role UI | — | Core-only | Tenant role UI. |
| `role_upgrade` | extended | Role Management | identity | Core-only | Role management. |
| `run_modules` | admin | Run Modules | — | Core-only | Admin execution surface. |
| `search` | core | Global Search | case_data | Core-only | Global search across tenant case data. |
| `security` | core | Advanced Security | identity | Core-only | 2FA and session management. |
| `setup` | dev | Setup Wizard | — | Core-only | Dev setup wizard. |
| `state_laws` | core | State Laws | public_data | Plugin-suitable | State law reference; plugin can save summaries to provider storage. |
| `storage` | core | Storage Auth | — | Core-only | Cloud storage auth and credential management. |
| `system_health` | admin | System Health | — | Core-only | Admin system health. |
| `tactics` | dev | Tactics | upl, court | Core-only | Legal tactics recommendations and evidence checklists. |
| `tenancy_hub` | admin | Tenancy Hub | — | Core-only | Tenancy hub. |
| `tenant_feed` | core | RECORD, Tenant Feed | case_data | Core-only | Aggregated tenant case feed. |
| `testing` | dev | Automated Testing | — | Core-only | Automated testing router. |
| `timeline` | core | Unified Timeline | case_data | Core-only | Case timeline events. |
| `tools_api` | extended | Tools | — | Unclear | Generic tools API; scope too broad to classify. |
| `ui_composer` | core | GUI, UI Composer | — | Core-only | Self-assembling tenant GUI. |
| `unified_overlays` | research | Unified Overlays | case_data | Unclear | Annotations on case documents; annotation data may be case-specific. |
| `user` | core | User | identity | Core-only | User identity / impersonation. |
| `user_concerns` | admin | User Concerns | case_data | Core-only | Admin user-concern tracking. |
| `vault` | core | Document Vault | case_data, evidence | Core-only | Canonical case/evidence document vault. |
| `vault_engine` | core | Access Control, Vault Engine | case_data | Core-only | Vault access control and audit. |
| `vault_installer` | dev | Vault Installer | — | Core-only | Vault installation endpoints. |
| `versioning` | core | System | — | Core-only | Internal system/versioning router. |
| `voice` | core | Voice | — | Unclear | Voice-to-text utility; unclear cloud-storage alignment and data handling. |
| `websocket` | core | WebSocket Events | — | Core-only | Real-time event transport. |
| `workflow` | core | Workflow | case_data | Core-only | Deterministic case routing engine. |
| `workflow_validator` | core | Admin | — | Core-only | Workflow validation admin. |
| `zoom_court` | extended | Zoom Courtroom | court | Core-only | Zoom courtroom integration. |
| `zoom_court_prep` | extended | Zoom Court Prep | court | Core-only | Zoom court prep. |

## Unclear modules — decision needed

The modules below are flagged as **Unclear**. Each needs a specific judgment call before any blueprint is written:

- `actions` — Smart actions; could be automation or legal actions.
- `campaign` — Campaign orchestration; not clearly cloud-storage related.
- `cloud_sync` — User-controlled data sync; overlaps PI's purpose and may move too much PII.
- `crawler` — Web crawler; not clearly aligned with tenant cloud storage.
- `data_freshness` — Resource staleness tracker; may be internal or a public monitoring plugin.
- `document_delivery` — Document delivery to third parties; high privacy sensitivity.
- `extraction` — Form field extraction; same tension as recognition.
- `filedored` — Virtual document organization; concept undefined.
- `fraud_exposure` — Fraud exposure; may publish case data.
- `free_api` — Mixed public lookups (property, violations, statutes) with court scraper. Needs split decision.
- `inventory` — File rotation/dating; unclear tenant value and PII implications.
- `plan_maker` — Plan maker; could be generic task planning or legal/case planning.
- `preview` — Document preview; could be a provider-side plugin but currently a Core UI component.
- `progress` — Progress tracker; could be generic but currently tied to case workflows.
- `public_exposure` — Public exposure tool; may publish case data.
- `public_forms` — Public forms; may generate legal documents from case data or be reference-only.
- `recognition` — Document recognition; could run locally on provider files but is case-data-adjacent.
- `tools_api` — Generic tools API; scope too broad to classify.
- `unified_overlays` — Annotations on case documents; annotation data may be case-specific.
- `voice` — Voice-to-text utility; unclear cloud-storage alignment and data handling.

## Draft blueprints for plugin-suitable modules

These are `status: draft` sketches for review. No implementation has started.

## Draft blueprint: document-converter

**Source Core module:** `document_converter`

### Identity / versioning

- `plugin_id`: `document-converter`
- `plugin_version`: `0.1.0`
- `platform`: `local_script`
- `status`: `draft`
- `name`: Document Converter
- `author`: Semptify
- `license`: TBD
- `homepage_url`: TBD
- `icon_url`: TBD

### Narrative

**Short description:** Convert documents between formats in the tenant's cloud storage.

**Long description:** A local script that downloads a document from the tenant's provider folder, converts it (e.g. DOCX to PDF, images to PDF), and uploads the converted file back to the provider. All bytes move directly between the local machine and the provider.

### Compatibility

- **Providers:** google_drive, dropbox, onedrive
- **Roles:** tenant, advocate
- **API version:** v1
- **Packagings supported:** local_script, desktop_app

### Technical contract

- **Core endpoints used:** POST /connect, POST /issue-token, POST /download_url, POST /upload_url
- **Connection flow:** Token after provider consent.
- **Capability usage:** POST /download_url to fetch source file; local conversion; POST /upload_url to write converted file.
- **Containment:** Source and destination paths are inside the vault folder.
- **Data the plugin sends to Core:** Token, file IDs, source/destination paths, and mimetype. File bytes go directly to the provider.
- **Zero-transfer rule:** Document bytes are transferred only between the local script and the provider. Semptify-PI/Core never handle the bytes.

### Security

- **Token storage:** Local secure storage.
- **Secret handling:** Provider secrets remain in Semptify-PI.
- **Scope usage:** provider:read, provider:write, tenant:own
- **Sandbox / isolation:** Local script runs in the tenant's own environment; browser extension uses extension sandbox.

### Tests

- **Automated tests:** Mock Core connect / download_url / upload_url round-trip.
- **Manual test steps:** Authorize provider, create a small file, verify it appears in provider vault folder, revoke token.

### Governance

- **Approval status:** `draft` — requires Core plugin directory review.
- **Code signing:** TBD.
- **Update cadence / versioning policy:** SemVer.

### Rollback

- **Token revocation:** POST /revoke or dashboard revoke.
- **Disable / uninstall:** Delete local config / remove browser extension.

---

## Draft blueprint: funding-search-export

**Source Core module:** `funding_search`

### Identity / versioning

- `plugin_id`: `funding-search-export`
- `plugin_version`: `0.1.0`
- `platform`: `local_script`
- `status`: `draft`
- `name`: Funding & Tax Credit Search Export
- `author`: Semptify
- `license`: TBD
- `homepage_url`: TBD
- `icon_url`: TBD

### Narrative

**Short description:** Search public funding programs and save results to tenant cloud storage.

**Long description:** A script that searches public funding and tax-credit databases and writes the result summary to the tenant's provider folder for budgeting or case-support documentation.

### Compatibility

- **Providers:** google_drive, dropbox, onedrive
- **Roles:** tenant, advocate
- **API version:** v1
- **Packagings supported:** local_script, browser_extension

### Technical contract

- **Core endpoints used:** POST /connect, POST /issue-token, POST /upload_url
- **Connection flow:** Plugin token issued after provider OAuth consent.
- **Capability usage:** POST /upload_url to save result summaries. Public funding data is fetched from the funding_search data source.
- **Containment:** Results stored under vault folder.
- **Data the plugin sends to Core:** Token and file path only. Result file goes directly to provider.
- **Zero-transfer rule:** Upload bytes bypass Semptify-PI/Core.

### Security

- **Token storage:** Local secure storage.
- **Secret handling:** Provider secrets remain in Semptify-PI.
- **Scope usage:** provider:write, tenant:own
- **Sandbox / isolation:** Local script runs in the tenant's own environment; browser extension uses extension sandbox.

### Tests

- **Automated tests:** Mock Core connect / download_url / upload_url round-trip.
- **Manual test steps:** Authorize provider, create a small file, verify it appears in provider vault folder, revoke token.

### Governance

- **Approval status:** `draft` — requires Core plugin directory review.
- **Code signing:** TBD.
- **Update cadence / versioning policy:** SemVer.

### Rollback

- **Token revocation:** POST /revoke or dashboard revoke.
- **Disable / uninstall:** Delete local config / remove browser extension.

---

## Draft blueprint: hud-funding-guide

**Source Core module:** `hud_funding`

### Identity / versioning

- `plugin_id`: `hud-funding-guide`
- `plugin_version`: `0.1.0`
- `platform`: `local_script`
- `status`: `draft`
- `name`: HUD Funding Guide Export
- `author`: Semptify
- `license`: TBD
- `homepage_url`: TBD
- `icon_url`: TBD

### Narrative

**Short description:** Export HUD funding guide sections to tenant cloud storage.

**Long description:** A reference plugin that lets tenants pull sections of the Semptify HUD funding guide and save them as a note or PDF in their own cloud storage.

### Compatibility

- **Providers:** google_drive, dropbox, onedrive
- **Roles:** tenant, advocate
- **API version:** v1
- **Packagings supported:** local_script

### Technical contract

- **Core endpoints used:** POST /connect, POST /issue-token, POST /upload_url
- **Connection flow:** Token after provider consent.
- **Capability usage:** POST /upload_url to store guide excerpts.
- **Containment:** Vault folder.
- **Data the plugin sends to Core:** Token and metadata only.
- **Zero-transfer rule:** Direct provider upload.

### Security

- **Token storage:** Local secure storage.
- **Secret handling:** No provider secrets locally.
- **Scope usage:** provider:write, tenant:own
- **Sandbox / isolation:** Local script runs in the tenant's own environment; browser extension uses extension sandbox.

### Tests

- **Automated tests:** Mock Core connect / download_url / upload_url round-trip.
- **Manual test steps:** Authorize provider, create a small file, verify it appears in provider vault folder, revoke token.

### Governance

- **Approval status:** `draft` — requires Core plugin directory review.
- **Code signing:** TBD.
- **Update cadence / versioning policy:** SemVer.

### Rollback

- **Token revocation:** POST /revoke or dashboard revoke.
- **Disable / uninstall:** Delete local config / remove browser extension.

---

## Draft blueprint: law-library-bookmarks

**Source Core module:** `law_library`

### Identity / versioning

- `plugin_id`: `law-library-bookmarks`
- `plugin_version`: `0.1.0`
- `platform`: `browser_extension`
- `status`: `draft`
- `name`: Law Library Bookmarks
- `author`: Semptify
- `license`: TBD
- `homepage_url`: TBD
- `icon_url`: TBD

### Narrative

**Short description:** Bookmark and annotate public law references, storing notes in the tenant's cloud vault.

**Long description:** A browser extension or desktop plugin that lets a tenant save references from the Semptify law library or external legal sources. It stores only metadata, notes, and links in the tenant's own Google Drive, Dropbox, or OneDrive folder. Document bytes (e.g. downloaded PDFs) go directly to the provider, never through Semptify Core.

### Compatibility

- **Providers:** google_drive, dropbox, onedrive
- **Roles:** tenant, advocate
- **API version:** v1
- **Packagings supported:** browser_extension

### Technical contract

- **Core endpoints used:** POST /connect, POST /issue-token, GET /capabilities, POST /download_url, POST /upload_url
- **Connection flow:** Tenant starts browser extension, is redirected to Semptify-PI for consent, and receives a scoped plugin token. The plugin uses the token on every subsequent request.
- **Capability usage:** Uses POST /upload_url to save law-reference notes (small JSON or markdown files) into the configured vault folder. Uses POST /download_url to load previously saved notes.
- **Containment:** All writes are scoped to the tenant's configured vault folder (e.g. /Semptify5.0/Inbox for Dropbox). The plugin normalizes paths and rejects escapes.
- **Data the plugin sends to Core:** Only plugin-token metadata, file IDs, and path strings are sent to Semptify-PI. Law PDF bytes are uploaded directly to the provider.
- **Zero-transfer rule:** The plugin uploads notes and downloaded law PDFs by calling the provider URL returned by Semptify-PI. The bytes never pass through Semptify-PI or Semptify Core.

### Security

- **Token storage:** Plugin token is stored in the browser extension's secure storage (or OS keychain for desktop) with an expiration reminder.
- **Secret handling:** OAuth client secrets live only in Semptify-PI. The plugin never sees provider client secrets or refresh tokens.
- **Scope usage:** provider:read, provider:write, tenant:own
- **Sandbox / isolation:** Local script runs in the tenant's own environment; browser extension uses extension sandbox.

### Tests

- **Automated tests:** Mock Core connect / download_url / upload_url round-trip.
- **Manual test steps:** Authorize provider, create a small file, verify it appears in provider vault folder, revoke token.

### Governance

- **Approval status:** `draft` — requires Core plugin directory review.
- **Code signing:** TBD.
- **Update cadence / versioning policy:** SemVer.

### Rollback

- **Token revocation:** POST /revoke or dashboard revoke.
- **Disable / uninstall:** Delete local config / remove browser extension.

---

## Draft blueprint: location-research

**Source Core module:** `location`

### Identity / versioning

- `plugin_id`: `location-research`
- `plugin_version`: `0.1.0`
- `platform`: `local_script`
- `status`: `draft`
- `name`: Location Research
- `author`: Semptify
- `license`: TBD
- `homepage_url`: TBD
- `icon_url`: TBD

### Narrative

**Short description:** Look up property/location information and save research notes to tenant cloud storage.

**Long description:** A local script or desktop plugin that runs property or address lookups and saves the resulting research notes (and any attached public records) to the tenant's own provider folder.

### Compatibility

- **Providers:** google_drive, dropbox, onedrive
- **Roles:** tenant, advocate
- **API version:** v1
- **Packagings supported:** local_script, desktop_app

### Technical contract

- **Core endpoints used:** POST /connect, POST /issue-token, POST /upload_url
- **Connection flow:** Token after provider consent.
- **Capability usage:** POST /upload_url to save location-research notes. May use POST /download_url to load prior notes.
- **Containment:** Vault folder.
- **Data the plugin sends to Core:** Token, file path, and note metadata only. Note content goes to provider.
- **Zero-transfer rule:** Direct provider upload of note files.

### Security

- **Token storage:** Local secure storage.
- **Secret handling:** No provider secrets locally.
- **Scope usage:** provider:read, provider:write, tenant:own
- **Sandbox / isolation:** Local script runs in the tenant's own environment; browser extension uses extension sandbox.

### Tests

- **Automated tests:** Mock Core connect / download_url / upload_url round-trip.
- **Manual test steps:** Authorize provider, create a small file, verify it appears in provider vault folder, revoke token.

### Governance

- **Approval status:** `draft` — requires Core plugin directory review.
- **Code signing:** TBD.
- **Update cadence / versioning policy:** SemVer.

### Rollback

- **Token revocation:** POST /revoke or dashboard revoke.
- **Disable / uninstall:** Delete local config / remove browser extension.

---

## Draft blueprint: pdf-tools

**Source Core module:** `pdf_tools`

### Identity / versioning

- `plugin_id`: `pdf-tools`
- `plugin_version`: `0.1.0`
- `platform`: `local_script`
- `status`: `draft`
- `name`: PDF Tools
- `author`: Semptify
- `license`: TBD
- `homepage_url`: TBD
- `icon_url`: TBD

### Narrative

**Short description:** Merge, split, and inspect PDFs stored in the tenant's cloud storage.

**Long description:** A local script that operates directly on PDFs in the tenant's provider folder. It downloads the PDF via a direct provider URL, processes it locally, and uploads the result back to the provider. No PDF bytes pass through Semptify Core.

### Compatibility

- **Providers:** google_drive, dropbox, onedrive
- **Roles:** tenant, advocate
- **API version:** v1
- **Packagings supported:** local_script, desktop_app

### Technical contract

- **Core endpoints used:** POST /connect, POST /issue-token, POST /download_url, POST /upload_url
- **Connection flow:** Token after provider consent.
- **Capability usage:** POST /download_url to fetch an existing PDF; local processing; POST /upload_url to write the result (e.g. merged.pdf, split pages).
- **Containment:** Input and output paths are constrained to the vault folder.
- **Data the plugin sends to Core:** Token, file IDs, and source/destination paths. PDF bytes are fetched and uploaded directly to the provider.
- **Zero-transfer rule:** PDF bytes travel between the local script and the provider only. Semptify-PI/Core see only signed URLs and file metadata.

### Security

- **Token storage:** Local secure storage.
- **Secret handling:** Provider secrets remain in Semptify-PI.
- **Scope usage:** provider:read, provider:write, tenant:own
- **Sandbox / isolation:** Local script runs in the tenant's own environment; browser extension uses extension sandbox.

### Tests

- **Automated tests:** Mock Core connect / download_url / upload_url round-trip.
- **Manual test steps:** Authorize provider, create a small file, verify it appears in provider vault folder, revoke token.

### Governance

- **Approval status:** `draft` — requires Core plugin directory review.
- **Code signing:** TBD.
- **Update cadence / versioning policy:** SemVer.

### Rollback

- **Token revocation:** POST /revoke or dashboard revoke.
- **Disable / uninstall:** Delete local config / remove browser extension.

---

## Draft blueprint: research-report-export

**Source Core module:** `research`

### Identity / versioning

- `plugin_id`: `research-report-export`
- `plugin_version`: `0.1.0`
- `platform`: `local_script`
- `status`: `draft`
- `name`: Research Report Export
- `author`: Semptify
- `license`: TBD
- `homepage_url`: TBD
- `icon_url`: TBD

### Narrative

**Short description:** Run landlord/property research and export the report to tenant cloud storage.

**Long description:** A local script that calls the Semptify research module and writes the generated report to the tenant's provider folder. The report may contain public records and public-source data assembled for the tenant.

### Compatibility

- **Providers:** google_drive, dropbox, onedrive
- **Roles:** tenant, advocate
- **API version:** v1
- **Packagings supported:** local_script

### Technical contract

- **Core endpoints used:** POST /connect, POST /issue-token, POST /upload_url
- **Connection flow:** Token after provider consent.
- **Capability usage:** POST /upload_url to store the research report.
- **Containment:** Report saved under the configured vault folder.
- **Data the plugin sends to Core:** Token and path. The report file goes directly to provider.
- **Zero-transfer rule:** Report bytes uploaded via direct provider URL.

### Security

- **Token storage:** Local secure storage.
- **Secret handling:** No provider secrets locally.
- **Scope usage:** provider:write, tenant:own
- **Sandbox / isolation:** Local script runs in the tenant's own environment; browser extension uses extension sandbox.

### Tests

- **Automated tests:** Mock Core connect / download_url / upload_url round-trip.
- **Manual test steps:** Authorize provider, create a small file, verify it appears in provider vault folder, revoke token.

### Governance

- **Approval status:** `draft` — requires Core plugin directory review.
- **Code signing:** TBD.
- **Update cadence / versioning policy:** SemVer.

### Rollback

- **Token revocation:** POST /revoke or dashboard revoke.
- **Disable / uninstall:** Delete local config / remove browser extension.

---

## Draft blueprint: resource-directory-export

**Source Core module:** `resource_directory`

### Identity / versioning

- `plugin_id`: `resource-directory-export`
- `plugin_version`: `0.1.0`
- `platform`: `local_script`
- `status`: `draft`
- `name`: Resource Directory Export
- `author`: Semptify
- `license`: TBD
- `homepage_url`: TBD
- `icon_url`: TBD

### Narrative

**Short description:** Export a curated community resource list to the tenant's cloud storage.

**Long description:** A local script that reads the Semptify community resource directory and exports a tenant-curated subset (CSV, JSON, or PDF) directly to the tenant's provider folder for sharing or offline use.

### Compatibility

- **Providers:** google_drive, dropbox, onedrive
- **Roles:** tenant, advocate
- **API version:** v1
- **Packagings supported:** local_script

### Technical contract

- **Core endpoints used:** POST /connect, POST /issue-token, POST /upload_url
- **Connection flow:** Script obtains a plugin token from Semptify-PI after provider consent.
- **Capability usage:** POST /upload_url to save the curated resource list. The list is built from public resource-directory data.
- **Containment:** Exported file lives under the vault folder.
- **Data the plugin sends to Core:** Token, file name, and path. The exported file contents go direct to provider.
- **Zero-transfer rule:** Export bytes are uploaded to the provider URL. Semptify-PI/Core never see the file contents.

### Security

- **Token storage:** Token stored in a local dotfile with restrictive permissions.
- **Secret handling:** No provider secrets in the script.
- **Scope usage:** provider:write, tenant:own
- **Sandbox / isolation:** Local script runs in the tenant's own environment; browser extension uses extension sandbox.

### Tests

- **Automated tests:** Mock Core connect / download_url / upload_url round-trip.
- **Manual test steps:** Authorize provider, create a small file, verify it appears in provider vault folder, revoke token.

### Governance

- **Approval status:** `draft` — requires Core plugin directory review.
- **Code signing:** TBD.
- **Update cadence / versioning policy:** SemVer.

### Rollback

- **Token revocation:** POST /revoke or dashboard revoke.
- **Disable / uninstall:** Delete local config / remove browser extension.

---

## Draft blueprint: state-law-snapshots

**Source Core module:** `state_laws`

### Identity / versioning

- `plugin_id`: `state-law-snapshots`
- `plugin_version`: `0.1.0`
- `platform`: `local_script`
- `status`: `draft`
- `name`: State Law Snapshots
- `author`: Semptify
- `license`: TBD
- `homepage_url`: TBD
- `icon_url`: TBD

### Narrative

**Short description:** Save jurisdiction-specific law summaries to tenant cloud storage.

**Long description:** A local script or desktop plugin that fetches state law overviews from Semptify's state_laws reference and stores a snapshot (markdown or PDF) in the tenant's own cloud folder. Useful for offline research and case prep.

### Compatibility

- **Providers:** google_drive, dropbox, onedrive
- **Roles:** tenant, advocate
- **API version:** v1
- **Packagings supported:** local_script, desktop_app

### Technical contract

- **Core endpoints used:** POST /connect, POST /issue-token, POST /upload_url
- **Connection flow:** Tenant runs the script, authorizes the provider via the Semptify-PI browser flow, and receives a scoped plugin token.
- **Capability usage:** Uses POST /upload_url to store a generated state-law snapshot in the provider vault. May use POST /download_url to read an existing snapshot.
- **Containment:** Snapshots are written under the configured vault folder and cannot escape it.
- **Data the plugin sends to Core:** Only the plugin token, file name, and provider path are sent to Semptify-PI. The law summary content is uploaded directly to the provider.
- **Zero-transfer rule:** Generated snapshot bytes are uploaded via the direct provider URL returned by /upload_url. Semptify-PI and Core never handle the bytes.

### Security

- **Token storage:** Token is written to a local config file with 0600 permissions or to the OS credential store.
- **Secret handling:** Provider secrets are held by Semptify-PI. The local script only has the plugin token.
- **Scope usage:** provider:write, tenant:own
- **Sandbox / isolation:** Local script runs in the tenant's own environment; browser extension uses extension sandbox.

### Tests

- **Automated tests:** Mock Core connect / download_url / upload_url round-trip.
- **Manual test steps:** Authorize provider, create a small file, verify it appears in provider vault folder, revoke token.

### Governance

- **Approval status:** `draft` — requires Core plugin directory review.
- **Code signing:** TBD.
- **Update cadence / versioning policy:** SemVer.

### Rollback

- **Token revocation:** POST /revoke or dashboard revoke.
- **Disable / uninstall:** Delete local config / remove browser extension.

---

