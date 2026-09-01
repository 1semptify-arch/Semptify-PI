/**
 * Node-based test runner for the browser extension API client.
 *
 * Usage:
 *   CORE_URL=http://127.0.0.1:9000 SESSION_TOKEN=sess_test node browser_extension/test-node.mjs
 */

import { SemptifyBrowserClient } from "./api-client.mjs";

const coreUrl = process.env.CORE_URL || "http://127.0.0.1:9000";
const sessionToken = process.env.SESSION_TOKEN || "sess_test";
const pluginId = process.env.PLUGIN_ID || "example-document-organizer";

function assert(condition, message) {
  if (!condition) throw new Error(`ASSERT FAILED: ${message}`);
}

function log(label, data) {
  console.log(`\n--- ${label} ---`);
  console.log(JSON.stringify(data, null, 2));
}

async function main() {
  const client = new SemptifyBrowserClient(coreUrl);

  // 1. List plugins
  const list = await client.listPlugins("browser_extension");
  log("list_plugins", list);
  assert(list.plugins.some((p) => p.plugin_id === pluginId), "expected plugin in list");

  // 2. Get plugin manifest
  const manifest = await client.getPlugin(pluginId);
  log("get_plugin", manifest);
  assert(manifest.plugin_id === pluginId, "manifest plugin_id mismatch");
  assert(manifest.packaging.includes("browser_extension"), "plugin must support browser_extension");

  // 3. Connect
  const connected = await client.connect(pluginId, sessionToken, "browser_extension", "node test");
  log("connect", connected);
  assert(connected.plugin_id === pluginId, "connect plugin_id mismatch");
  assert(connected.token.startsWith("pl_"), "token must start with pl_");
  assert(connected.scopes.includes("vault:read"), "expected vault:read scope");

  // 4. me
  const me = await client.me();
  log("me", me);
  assert(me.plugin_id === pluginId, "me plugin_id mismatch");

  // 5. Download capability per provider
  for (const provider of ["google_drive", "dropbox", "onedrive"]) {
    const dl = await client.downloadUrl("doc_123", provider);
    log(`download_url (${provider})`, dl);
    assert(dl.expires_at, "download capability must expire");

    if (provider === "google_drive") {
      assert(dl.direct_request, "google_drive download must return direct_request");
      assert(dl.direct_request.endpoint.includes("drive/v3/files/"), "google_drive endpoint mismatch");
      assert(dl.direct_request.query.alt === "media", "google_drive alt mismatch");
      assert(dl.direct_request.headers.Authorization.startsWith("Bearer "), "google_drive auth header missing");
    } else {
      assert(dl.download_url, `${provider} download must return download_url`);
      assert(!dl.direct_request, `${provider} download must not return direct_request`);
    }
  }

  // 6. Upload capability per provider
  for (const provider of ["google_drive", "dropbox", "onedrive"]) {
    const ul = await client.uploadUrl("notice.pdf", "/Semptify5.0/Inbox", provider);
    log(`upload_url (${provider})`, ul);
    assert(ul.completion_token, "upload must return completion_token");
    assert(ul.expires_at, "upload capability must expire");

    if (provider === "google_drive") {
      assert(ul.direct_request, "google_drive upload must return direct_request");
      assert(ul.direct_request.endpoint.includes("upload/drive/v3/files"), "google_drive upload endpoint mismatch");
      assert(ul.direct_request.query.uploadType === "resumable", "google_drive uploadType mismatch");
      assert(ul.direct_request.body.name === "notice.pdf", "google_drive filename mismatch");
    } else if (provider === "dropbox") {
      assert(ul.direct_request, "dropbox upload must return direct_request");
      assert(ul.direct_request.endpoint.includes("content.dropboxapi.com"), "dropbox upload endpoint mismatch");
      assert(ul.direct_request.headers["Dropbox-API-Arg"], "dropbox Dropbox-API-Arg header missing");
    } else {
      assert(ul.upload_url, "onedrive upload must return upload_url");
      assert(!ul.direct_request, "onedrive upload must not return direct_request");
    }
  }

  // 7. Complete an upload using the Google Drive-shaped response
  const upload = await client.uploadUrl("notice.pdf", "/Semptify5.0/Inbox", "google_drive");
  const complete = await client.completeUpload(
    upload.completion_token,
    "provider_abc",
    "notice.pdf",
    1024
  );
  log("complete_upload", complete);
  assert(complete.filename === "notice.pdf", "complete filename mismatch");
  assert(complete.vault_path === "/Semptify5.0/Inbox/notice.pdf", "complete vault_path mismatch");
  assert(complete.size === 1024, "complete size mismatch");

  console.log("\nAll browser_extension tests passed.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
