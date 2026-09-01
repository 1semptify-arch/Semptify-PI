import { SemptifyBrowserClient } from "./api-client.mjs";

const coreUrlInput = document.getElementById("core-url");
const sessionTokenInput = document.getElementById("session-token");
const connectBtn = document.getElementById("connect");
const meBtn = document.getElementById("me");
const downloadFileIdInput = document.getElementById("download-file-id");
const downloadProviderSelect = document.getElementById("download-provider");
const downloadUrlBtn = document.getElementById("download-url");
const uploadFilenameInput = document.getElementById("upload-filename");
const uploadParentInput = document.getElementById("upload-parent");
const uploadProviderSelect = document.getElementById("upload-provider");
const uploadUrlBtn = document.getElementById("upload-url");
const uploadTokenP = document.getElementById("upload-token");
const completeBtn = document.getElementById("complete");
const resultEl = document.getElementById("result");
const actionsEl = document.getElementById("actions");

let client = null;
let lastUpload = null;

function show(data) {
  resultEl.textContent = JSON.stringify(data, null, 2);
}

function showError(err) {
  resultEl.textContent = `Error: ${err.message}`;
}

async function loadConfig() {
  const config = await chrome.storage.local.get(["coreUrl", "pluginToken"]);
  if (config.coreUrl) coreUrlInput.value = config.coreUrl;
  if (config.pluginToken) {
    client = new SemptifyBrowserClient(config.coreUrl, config.pluginToken);
    actionsEl.classList.remove("hidden");
    resultEl.textContent = "Plugin token loaded. Click a button to call the API.";
  }
}

async function saveConfig(coreUrl, pluginToken) {
  await chrome.storage.local.set({ coreUrl, pluginToken });
}

connectBtn.addEventListener("click", async () => {
  try {
    client = new SemptifyBrowserClient(coreUrlInput.value);
    const result = await client.connect(
      "example-document-organizer",
      sessionTokenInput.value,
      "browser_extension",
      "browser extension popup"
    );
    await saveConfig(coreUrlInput.value, client.pluginToken);
    actionsEl.classList.remove("hidden");
    show(result);
  } catch (err) {
    showError(err);
  }
});

meBtn.addEventListener("click", async () => {
  try {
    const result = await client.me();
    show(result);
  } catch (err) {
    showError(err);
  }
});

downloadUrlBtn.addEventListener("click", async () => {
  try {
    const result = await client.downloadUrl(
      downloadFileIdInput.value,
      downloadProviderSelect.value
    );
    show(result);
  } catch (err) {
    showError(err);
  }
});

uploadUrlBtn.addEventListener("click", async () => {
  try {
    lastUpload = await client.uploadUrl(
      uploadFilenameInput.value,
      uploadParentInput.value,
      uploadProviderSelect.value
    );
    uploadTokenP.textContent = `completion_token: ${lastUpload.completion_token}`;
    uploadTokenP.classList.remove("hidden");
    completeBtn.classList.remove("hidden");
    show(lastUpload);
  } catch (err) {
    showError(err);
  }
});

completeBtn.addEventListener("click", async () => {
  try {
    if (!lastUpload) return;
    const result = await client.completeUpload(
      lastUpload.completion_token,
      "provider_abc",
      uploadFilenameInput.value,
      1024
    );
    show(result);
  } catch (err) {
    showError(err);
  }
});

loadConfig();
