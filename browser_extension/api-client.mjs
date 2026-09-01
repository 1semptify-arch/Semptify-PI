/**
 * Semptify-PI browser extension API client.
 *
 * This is a plain ES module that works both in a browser extension context
 * (popup/background) and under Node for testing. It consumes the same
 * provider-differentiated contract as local_script:
 *
 * - `download_url` / `upload_url` are preauthenticated tokenless URLs.
 * - `direct_request` describes an HTTP request the plugin must make itself
 *   (endpoint, method, headers, optional query/body).
 *
 * The plugin always prefers `direct_request` when present.
 */

export class SemptifyBrowserClient {
  constructor(coreUrl, pluginToken = null) {
    this.coreUrl = (coreUrl || "http://127.0.0.1:9000").replace(/\/$/, "");
    this.pluginToken = pluginToken;
  }

  setPluginToken(token) {
    this.pluginToken = token;
  }

  async _request(method, path, options = {}) {
    const url = `${this.coreUrl}${path}`;
    const headers = { ...options.headers };
    if (options.sessionToken) {
      headers["Authorization"] = `Bearer ${options.sessionToken}`;
    } else if (this.pluginToken) {
      headers["Authorization"] = `Bearer ${this.pluginToken}`;
    }

    const fetchOptions = {
      method,
      headers,
    };
    if (options.body !== undefined) {
      fetchOptions.body = JSON.stringify(options.body);
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(url, fetchOptions);
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }
    return response.json();
  }

  async listPlugins(packaging = null) {
    const params = packaging ? `?packaging=${packaging}` : "";
    return this._request("GET", `/api/v1/plugins${params}`);
  }

  async getPlugin(pluginId) {
    return this._request("GET", `/api/v1/plugins/${pluginId}`);
  }

  async connect(pluginId, sessionToken, packaging = "browser_extension", label = null) {
    const body = { packaging };
    if (label) body.label = label;
    const result = await this._request("POST", `/api/v1/plugins/${pluginId}/connect`, {
      sessionToken,
      body,
    });
    this.pluginToken = result.token;
    return result;
  }

  async me() {
    return this._request("GET", "/api/v1/plugin/me");
  }

  async downloadUrl(fileId, provider = "google_drive") {
    return this._request(
      "POST",
      `/api/v1/plugin/files/${fileId}/download-url?provider=${provider}`
    );
  }

  async uploadUrl(filename, parentFolder = null, provider = "google_drive") {
    const body = { filename };
    if (parentFolder) body.parent_folder = parentFolder;
    return this._request(
      "POST",
      `/api/v1/plugin/files/upload-url?provider=${provider}`,
      { body }
    );
  }

  async completeUpload(completionToken, providerFileId, filename, size = null) {
    const body = { completion_token: completionToken, provider_file_id: providerFileId, filename };
    if (size !== null) body.size = size;
    return this._request("POST", "/api/v1/plugin/files/complete", { body });
  }
}
