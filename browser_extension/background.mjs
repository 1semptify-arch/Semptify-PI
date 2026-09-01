/**
 * Service worker for the Semptify-PI reference browser extension.
 *
 * Currently minimal: keeps the extension alive and listens for install.
 * The popup handles all user-facing API calls.
 */

chrome.runtime.onInstalled.addListener(() => {
  console.log("Semptify-PI reference extension installed.");
});
