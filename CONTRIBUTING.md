# Contributing

中文版本见 [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md).

Thanks for your interest in Narra Studio.

## Development Principles

- Keep the backend Docker-first.
- Keep provider credentials out of frontend code.
- Use `CredentialResolver` for secrets.
- Use `CapabilityRunService` for model calls.
- Let adapters return temporary files or source URLs only.
- Let `AssetService` create final assets.
- Keep generated files out of Git.

## Setup

```bash
pip install -r backend/requirements.txt
```

Run backend tests:

```bash
PYTHONPATH=. python -m pytest tests -q
```

Run frontend smoke tests:

```bash
node --test tests/frontend/*.test.js
```

Validate Docker Compose:

```bash
docker compose config
docker compose --profile async config
```

## Before Opening a Pull Request

- Do not include real secrets or local data.
- Do not include internal PRD/TDS documents.
- Run the relevant tests.
- Update README or public docs when behavior changes.
- Add tests for new service, adapter, task, or API behavior.

## Documentation Boundary

Internal product and technical design documents are not part of the open-source distribution. Public design explanations should be written as high-level docs under `docs/`.
