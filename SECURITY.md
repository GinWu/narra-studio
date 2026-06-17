# Security Policy

中文版本见 [SECURITY.zh-CN.md](SECURITY.zh-CN.md).

## Supported Versions

This project is early-stage software. Security fixes are applied to the main branch unless a release branch policy is introduced later.

## Reporting a Vulnerability

Please do not open a public issue for secrets exposure, credential handling bugs, path traversal, unsafe downloads, or provider callback vulnerabilities.

Report privately to the project maintainer through the repository owner's preferred private contact channel. If no private channel is listed, open a minimal public issue asking for a private disclosure contact without including exploit details.

## Credential Handling Rules

- Do not commit real API keys, provider tokens, passwords, private keys, or signed URLs.
- Frontend code must not store provider secrets.
- Provider credentials must be resolved by the backend `CredentialResolver`.
- Adapter code must not read environment variables or Docker secrets directly.
- Logs, task payloads, experiments, invocation logs, and exports must not contain raw credentials.

## Local Development Secrets

Local Docker secret files may be placed under `secrets/`; that directory is ignored except for documentation placeholders. Treat any file under `secrets/` as private local state.

## Scope Notes

Cost records are estimates and are not intended for billing. This project does not yet provide multi-user access control or RBAC.
