# AGENTS.md — Standing Rules for AI Agents Working on Semptify-PI

This repo is worked on by AI coding agents (Devin, Windsurf, Claude Code, etc.). These rules apply to all of them.

## Non-negotiable rules

1. **Preflight read is mandatory.** Before touching any file, the agent must read it (and its immediate neighbors) first. No blind edits.
2. **One task per commit.** No bundled half-migrations across sessions. Each commit should be revertable on its own.
3. **No self-approval.** An agent does not mark its own task or PR as done. A human (Brad) confirms completion.
4. **Python 3.11.9 only.** Match Semptify Core's Python mandate.
5. **This repo is decoupled from Semptify.** No imports, no shared credentials, no shared database, no cross-references to the Semptify Core codebase or its data.
6. **No real tenant data in this repo.** Use synthetic fixtures and test users only. Real `semptify_uid`, OAuth tokens, or case data are off-limits.
7. **No production secrets in git.** `.env`, `config.json` with tokens, local SQLite files, and key material are `.gitignore`d and must stay out of commits.
8. **No document bytes on `mock_core`.** The mock Core returns fake direct URLs. It does not store or transmit document bytes.
9. **No paid tiers, accounts, or dark patterns.** The plugin directory is public-service positioning only.
10. **Never commit case data or PII.** No tenant names, addresses, case numbers, or scraped personal records.

## Local environment

- **Local PostgreSQL 16** is available for agent/test use on `localhost:5432`. The agent database is `semptify_pi` and is independent of Semptify Core's database.
- Set `DATABASE_URL` in `.env` (copied from `.env.example`). Use `tools/verify_postgres.py` to confirm the connection before relying on it.
- This Postgres instance is for agent scratch work and testing only; it is not the deployed application database.

## Additional notes

- `apps.yaml` is the source of truth for which services run and how.
- Every app under this repo is standalone unless `apps.yaml` says otherwise.
- The public API surface for plugins is in `plugin_api_spec/` and `docs/design-spec.md`.

## Cross-repo conventions

`C:\master-repo\CONVENTIONS.md` is the master source of truth for keeping this
repo's build docs, hand-offs, and logs separate from Semptify Core's. Read it
before adding cross-repo references; cite, do not copy.
