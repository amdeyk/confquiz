# Change Document: Optional .env2 for This Update

Date: 2026-01-13

## Summary

Configuration still reads from `.env` by default.
For this update, you can use a separate `.env2` by setting the `ENV_FILE` environment variable.

## Code Changes

- `config.py` now loads `ENV_FILE` (default: `.env`).

## Repo Hygiene

- `.gitignore` ignores `.env2` and `.env2.*` so the alternate file stays out of git.

## Documentation Updates

- Updated environment instructions across:
  - `DEPLOYMENT.md`
  - `ENVIRONMENT_CONFIG.md`
  - `QUICKSTART.md`
  - `README.md`
  - `CHANGES_ENVIRONMENT_FIX.md`
  - `DEPLOYMENT_CHECKLIST_FINAL.md`
- `.env.example` notes it should be copied to `.env` (or `.env2` when using `ENV_FILE`).

## How to Use

Default behavior:
```
# No ENV_FILE needed; app loads .env automatically
```

Override example:
```
ENV_FILE=.env2
```
