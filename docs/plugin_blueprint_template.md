# Plugin Blueprint: `{plugin_id}`

Use this template for every new plugin **before** implementation starts. Filling
it out is a check that the plugin's identity, scope, security posture, and
rollback path are understood.

---

## Identity / versioning

| Field | Value |
|-------|-------|
| `plugin_id` | Unique, URL-safe identifier (e.g. `example-document-organizer`). |
| `plugin_version` | SemVer for this blueprint (e.g. `0.1.0` for a reference plugin). |
| `platform` | `local_script`, `browser_extension`, or `desktop_app`. |
| `status` | `internal-reference`, `public`, `experimental`, or `deprecated`. |
| `name` | Short human-readable name. |
| `author` | Author or organization. |
| `license` | License the plugin code is released under. |
| `homepage_url` | Public landing page for the plugin. |
| `icon_url` | Optional icon URL. |

## Narrative

### Short description

One line describing what the plugin does.

### Long description

Plain-language explanation for a non-technical tenant. What problem does it
solve? What does the user see? What does the plugin touch in the tenant's cloud
storage?

## Compatibility

- **Providers:** Which cloud storage providers are supported (`google_drive`,
  `dropbox`, `onedrive`)?
- **Roles:** Which tenant roles are expected to use it? (If uncertain, flag it
  here rather than guessing.)
- **API version:** Which PI API version does it target (`v1`)?
- **Packagings supported:** If the same logical plugin has multiple packagings,
  list them.

## Technical contract

- **Core endpoints used:** List the PI endpoints the plugin calls.
- **Connection flow:** How the plugin gets a plugin token from Core.
- **Capability usage:** How it uses `download_url`, `upload_url`, and
  `direct_request` responses, including any provider-specific handling.
- **Containment:** How it stays inside the configured vault folder.
- **Data the plugin sends to Core:** Metadata only. Document bytes never transit
  Core.
- **Zero-transfer rule:** How the plugin proves it does not send document bytes
  to Core.

## Security

- **Token storage:** Where the plugin token is persisted and how it is protected.
- **Secret handling:** How OAuth client secrets, session tokens, and provider
  capability headers are handled.
- **Scope usage:** Which plugin-token scopes the plugin requests and why.
- **Sandbox / isolation:** Browser extension permissions, local file system
  access, etc.

## Tests

- **Automated tests:** Which tests exercise this plugin.
- **Manual test steps:** Minimum steps to verify a connect / download / upload
  round-trip against `mock_core` or a real Core instance.

## Governance

- **Approval status:** Who can approve this plugin? (Core plugin directory,
  admin, community review.)
- **Code signing:** Is code signing required? For which packagings?
- **Update cadence / versioning policy:** How the plugin version is bumped.

## Rollback

- **Token revocation:** How a tenant or admin can revoke the plugin token.
- **Disable / uninstall:** How the plugin is disabled or removed from a tenant.
