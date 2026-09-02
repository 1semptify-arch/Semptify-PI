# Plugin Blueprint: `example-document-organizer` (`browser_extension`)

Reference Manifest V3 browser extension for the Semptify-PI
`browser_extension` packaging.

---

## Identity / versioning

| Field | Value |
|-------|-------|
| `plugin_id` | `example-document-organizer` |
| `plugin_version` | `1.0.0` |
| `platform` | `browser_extension` |
| `status` | `internal-reference` |
| `name` | Semptify Document Organizer |
| `author` | Semptify |
| `license` | `AGPL-3.0` |
| `homepage_url` | `https://semptify.org/plugins/example-document-organizer` |
| `icon_url` | `icon.svg` (bundled) |

## Narrative

### Short description

A Chrome/Firefox reference extension that connects to the Semptify-PI Core and
requests direct download/upload capabilities from the browser.

### Long description

The browser extension is a minimal Manifest V3 plugin that demonstrates the
provider-differentiated capability contract. A tenant opens the popup, enters
their Core URL and a session token, and clicks Connect. The extension obtains a
scoped plugin token, then lets the tenant request download or upload
capabilities. The actual download or upload happens between the browser and the
tenant's cloud provider; the Semptify Core only brokers the metadata and the
short-lived capability.

## Compatibility

- **Providers:** `google_drive`, `dropbox`, `onedrive` (the popup lets the user
  pick a provider for each download or upload request).
- **Roles:** Likely developers, technical advocates, agencies, and researchers
  testing the extension; tenants may use a published version later.
  **Flagged for review:** target user role for a public release.
- **API version:** `v1`.
- **Packagings supported:** `browser_extension`.

## Technical contract

- **Core endpoints used:**
  - `GET /api/v1/plugins` — list approved plugins.
  - `GET /api/v1/plugins/{plugin_id}` — get plugin manifest.
  - `POST /api/v1/plugins/{plugin_id}/connect` — obtain a scoped plugin token.
  - `GET /api/v1/plugin/me` — verify plugin context.
  - `POST /api/v1/plugin/files/{file_id}/download-url` — request a download
    capability.
  - `POST /api/v1/plugin/files/upload-url` — request an upload capability.
  - `POST /api/v1/plugin/files/complete` — record a completed upload (metadata
    only).
- **Connection flow:** The popup calls `SemptifyBrowserClient.connect` with the
  user-supplied session token and stores the returned `plugin_token` in
  `chrome.storage.local`.
- **Capability usage:** The extension passes the chosen provider as a query
  parameter. It displays the Core response and uses the returned
  `direct_request` or preauthenticated URL to call the cloud provider. The
  extension itself does not currently execute the provider request; it displays
  the capability for the user.
- **Containment:** The extension passes `parent_folder` to `upload-url`; Core
  rejects paths that escape the configured vault folder.
- **Data the plugin sends to Core:** JSON request bodies containing file IDs,
  filenames, completion tokens, and sizes. No document bytes.
- **Zero-transfer rule:** The service worker and popup never read or forward
  document bodies. They only carry capability metadata.

## Security

- **Token storage:** The plugin token is stored in `chrome.storage.local`, not in
  a web page or sync storage.
- **Secret handling:** The session token is typed into the popup and used only
  for the connect request. The plugin token is persisted in extension storage.
  Provider `Authorization` headers from `direct_request` are used once and not
  logged.
- **Scope usage:** The client uses `vault:read`, `vault:write`, and
  `documents:capability` via the `example-document-organizer` manifest.
- **Sandbox / isolation:** The extension is a Manifest V3 browser extension with
  `storage` permission and `host_permissions` for the Core origin only. It runs
  in the browser's extension sandbox and has no access to web page content.

## Tests

- **Automated tests:** `tests/test_browser_extension.py` runs
  `browser_extension/test-node.mjs` against a live `mock_core`.
- **Manual test steps:**
  1. Start `mock_core`: `uvicorn mock_core.main:app --port 9000`.
  2. Load the unpacked extension in Chrome or Firefox.
  3. Open the popup, enter `http://127.0.0.1:9000` and `sess_test`, then click
     Connect.
  4. Enter a file ID and click Download URL.
  5. Enter a filename and click Upload URL, then Complete.

## Governance

- **Approval status:** `approved` as an internal reference plugin.
- **Code signing:** Required for distribution through the Chrome Web Store and
  Mozilla Add-ons; the reference version is unsigned and loaded unpacked for
  testing.
- **Update cadence / versioning policy:** Update `manifest.json` version and the
  manifest version in `core/seeding.py` when the contract changes.

## Rollback

- **Token revocation:** The tenant can `DELETE /api/v1/plugins/tokens/{token_id}`
  from a session-authenticated client.
- **Disable / uninstall:** Remove the extension from the browser. The token
  stored in `chrome.storage.local` is deleted with the extension.
