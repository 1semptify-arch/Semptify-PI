# Semptify-PI

Semptify Plugin Interface prototype — client-side plugins (browser extension, desktop app, local script) that connect to Semptify Core.

**Part of Semptify 5.1.** The version is tracked inside this repo, not in the repo name.

## What this is

This repo holds the reference implementation and API contract for the Semptify Plugin Interface. It is intentionally decoupled from `1semptify-arch/Semptify`:

- No imports from the Semptify Core codebase.
- No shared credentials, `SECRET_KEY`, or `DATABASE_URL` with Core.
- No shared database with Core.
- Plugin code uses only the public `Semptify-PI` API surface.

## Local agent database

A local PostgreSQL 16 instance is available on `localhost:5432` for agent/test use. The agent database `semptify_pi` is independent of Semptify Core's database and is only for scratch work and testing.

Copy `.env.example` to `.env` and set `DATABASE_URL`. Run `python tools/verify_postgres.py` to confirm the connection.

## Repo structure

```
Semptify-PI/
├── apps.yaml                    # Source of truth for local services
├── pyproject.toml               # Monorepo packages + console scripts
├── .env.example                 # Local env template (copy to .env)
├── mock_core/                   # Local FastAPI test double for Semptify Core
├── browser_extension/           # Candidate D reference plugin
├── desktop_app/                 # Candidate E reference plugin
├── local_script/                # Candidate F reference plugin
├── plugin_api_spec/             # OpenAPI + JSON Schema contract
├── tools/                       # Helper scripts
│   └── verify_postgres.py       # Check agent Postgres connection
└── docs/
    └── design-spec.md           # The full plugin architecture design spec
```

## Status

This is the initial scaffold. No app code is committed yet. The first implementation tasks will be:

1. Land the `mock_core` test double.
2. Land one reference plugin (likely `local_script`) to validate the API.
3. Develop the remaining packaging candidates in parallel.

## License

AGPL-3.0 unless Brad decides otherwise.
