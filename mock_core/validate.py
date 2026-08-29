"""Validation script for Semptify-PI mock_core."""

import sys

import httpx

BASE = "http://127.0.0.1:9000"


def check(resp, msg):
    print(f"{msg}: {resp.status_code}")
    if resp.status_code >= 400:
        print(resp.text)
        sys.exit(1)


def main():
    with httpx.Client() as c:
        r = c.get(f"{BASE}/api/v1/plugins")
        check(r, "list plugins")
        print(r.json())

        r = c.get(f"{BASE}/api/v1/plugins/example-document-organizer")
        check(r, "get manifest")
        body = r.json()
        assert body["status"] == "approved"
        assert "github.com/1semptify-arch/Semptify-PI/releases/download/" in body["downloads"]["local_script"]["download_url"]

        r = c.post(
            f"{BASE}/api/v1/plugins/example-document-organizer/connect",
            headers={"Authorization": "Bearer sess_synthetic"},
            json={"packaging": "local_script"},
        )
        check(r, "connect")
        token_data = r.json()
        token = token_data["token"]
        token_id = token_data["token_id"]
        print("issued token:", token[:10] + "...")

        r = c.get(f"{BASE}/api/v1/plugin/me", headers={"Authorization": f"Bearer {token}"})
        check(r, "plugin me")
        print(r.json())

        r = c.get(f"{BASE}/api/v1/plugins/tokens", headers={"Authorization": "Bearer sess_synthetic"})
        check(r, "list tokens")
        print(r.json())

        r = c.post(
            f"{BASE}/api/v1/plugin/files/doc_123/download-url",
            headers={"Authorization": f"Bearer {token}"},
        )
        check(r, "download url")
        print(r.json())

        r = c.post(
            f"{BASE}/api/v1/plugin/files/upload-url",
            headers={"Authorization": f"Bearer {token}"},
            json={"filename": "notice.pdf", "parent_folder": "/Semptify5.0/Inbox"},
        )
        check(r, "upload url")
        upload = r.json()
        print(upload)

        r = c.post(
            f"{BASE}/api/v1/plugin/files/complete",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "completion_token": upload["completion_token"],
                "provider_file_id": "provider_abc",
                "filename": "notice.pdf",
                "size": 1024,
            },
        )
        check(r, "complete upload")
        print(r.json())

        r = c.delete(f"{BASE}/api/v1/plugins/tokens/{token_id}", headers={"Authorization": "Bearer sess_synthetic"})
        check(r, "revoke token")

    print("\nAll mock_core validations passed.")


if __name__ == "__main__":
    main()
