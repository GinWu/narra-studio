# Narra Studio

中文说明见 [README.zh-CN.md](README.zh-CN.md).

Narra Studio is a Docker-first studio for AI content production experiments and model debugging.

It is not a chat application and it is not an automatic video-production platform. The goal is to provide a local, inspectable workspace where creators and developers can run media-generation models, compare results, keep generated assets, and preserve enough metadata to understand what happened later.

## What It Tries to Do

Narra Studio is designed around a few core ideas:

- call different AI providers through one backend API;
- experiment with text-to-speech, speech-to-text, voice profile, image generation, and video generation workflows;
- record every model call as an `Experiment`;
- save generated audio, image, video, and other files as `Asset` records;
- keep prompt templates and parameters reproducible;
- support manual evaluation and comparison;
- record estimated cost and invocation logs for review;
- organize useful results into content projects;
- run locally with Docker Compose as the default deployment path.

## Current Status

The current implementation includes:

- FastAPI backend;
- Docker Compose setup with `api`, `web`, `db`, and workspace volume;
- optional async profile with `redis` and Celery `worker`;
- PostgreSQL default database and SQLite-friendly development/test paths;
- Provider and Model Registry APIs;
- `CredentialResolver` for environment, Docker secret, file, or no-credential providers;
- Capability Adapter protocol and Adapter Registry;
- Mock adapter for TTS, STT, voice clone, image generation, and video generation;
- initial OpenAI, ElevenLabs, fal.ai, Replicate, and Alibaba Cloud Bailian / DashScope adapter support;
- Experiment, Asset, PromptTemplate, Evaluation, CostRecord, InvocationLog, Task, Project, ProjectItem, ScriptVersion, Shot, and VoiceProfile models;
- Voice Lab API for TTS and VoiceProfile-based TTS;
- Audio Lab API for STT and voice clone workflows;
- Image Lab API for text-to-image generation;
- Video Lab API backed by async task execution;
- Asset storage, download, upload, discard/delete rules, and storage repair checks;
- Evaluation and comparison APIs;
- cost estimation and invocation-log APIs;
- project organization and safe manifest export;
- sanitizer service for sensitive payloads and signed URLs;
- browser frontend for the main studio views.

## Not Yet Included

Some capabilities are intentionally not complete yet:

- live-verified real-provider video generation workflows;
- live-verified Alibaba Cloud Bailian / DashScope speech endpoints. The code path is implemented and covered by mocked HTTP tests, but real credentials, workspace permissions, endpoint paths, and billing should be verified by each deployment;
- provider webhook signature verification and public callback handling;
- image editing, image variation, and reference-image workflows;
- encrypted local API key storage through the UI;
- full voice-cloning and consent-management UI. Backend VoiceProfile governance exists, but the frontend workflow is still intentionally limited;
- multi-user accounts, RBAC, and team collaboration;
- packaged project export such as zip bundles or editing-suite project files;
- production-grade billing. Cost records are estimates only.

## Quick Start

Requirements:

- Docker and Docker Compose;
- optionally Python 3.11 for local backend tests;
- optionally Node.js 20+ for frontend smoke tests.

Start the default stack:

```bash
docker compose up --build
```

Open:

- frontend: http://localhost:8501
- backend health: http://localhost:8000/api/system/health

If host ports are already in use:

```bash
AIWM_API_PUBLISHED_PORT=18080 AIWM_WEB_PUBLISHED_PORT=18501 docker compose up --build
```

Start the async profile with Redis and Celery worker:

```bash
docker compose --profile async up --build
```

## Provider Credentials

The frontend must not store provider API keys. Configure provider records with references only, such as:

- `credential_source=docker_secret`
- `credential_ref=openai_api_key`
- `credential_file=/run/secrets/openai_api_key`

For local Docker secret mounts, create local files under `secrets/` and use the optional override:

```bash
docker compose -f docker-compose.yml -f docker-compose.secrets.example.yml --profile async up --build
```

Never commit real credential files.

### Alibaba Cloud Bailian / DashScope

The backend includes an optional `bailian` adapter for Alibaba Cloud Bailian / DashScope speech workflows. It is disabled by default and uses the credential reference `dashscope_api_key`.

Typical setup:

```bash
printf '%s' "$DASHSCOPE_API_KEY" > secrets/dashscope_api_key
docker compose -f docker-compose.yml -f docker-compose.secrets.example.yml --profile async up --build
```

Then seed or create the provider/model records through the backend API:

```bash
curl -X POST http://localhost:8000/api/providers/seed-defaults
curl -X POST 'http://localhost:8000/api/models/seed-bailian?provider_id=<bailian_provider_id>'
```

The seeded Bailian models are disabled by default. Confirm the region `api_base`, model IDs, and endpoint paths in your Bailian workspace before enabling them. Speech recognition and voice clone adapters upload audio files through an internal runtime-only file handoff; local filesystem paths are not stored in `Experiment` records or logs.

## Development

Install backend dependencies into your preferred virtual environment:

```bash
pip install -r backend/requirements.txt
```

Run backend tests:

```bash
PYTHONPATH=. python -m pytest tests -q
```

Run Alembic migrations against a local database URL:

```bash
AIWM_DATABASE_URL=sqlite:////tmp/aiwm-dev.db python -m alembic upgrade head
```

Run frontend smoke tests:

```bash
node --test tests/frontend/*.test.js
```

Validate Compose files:

```bash
docker compose config
docker compose --profile async config
```

## Storage Model

Generated files are stored under the Docker workspace volume mounted at `/app/workspace` inside containers. Asset records store relative paths, not host-machine absolute paths. Downloads should go through the backend Asset API.

## Security Notes

- Do not commit real API keys, tokens, passwords, private keys, provider signed URLs, or local database files.
- The frontend calls only this backend API; it should not call external AI providers directly.
- Provider credentials must be read through `CredentialResolver`.
- Adapter implementations should only return temporary files or source URLs.
- Final asset persistence belongs to `AssetService`.
- Sensitive response payloads should pass through `SanitizerService` before being stored or exported.
- The default database password is for local development only. Override it for any shared or deployed environment.

## Naming and Compatibility

The public project and repository name is `narra-studio`. Some internal environment variables still use the historical `AIWM_` prefix for backward compatibility with existing local deployments.

## Open-Source Boundary

Internal product and technical design documents are intentionally not part of the open-source distribution. Public documentation should live in files such as this README, `docs/ROADMAP.md`, and `docs/ARCHITECTURE_OVERVIEW.md`.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
