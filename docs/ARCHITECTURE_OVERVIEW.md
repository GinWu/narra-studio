# Architecture Overview

中文版本见 [ARCHITECTURE_OVERVIEW.zh-CN.md](ARCHITECTURE_OVERVIEW.zh-CN.md).

Narra Studio uses a Docker-first architecture.

## Runtime Services

Default profile:

- `web`: browser UI;
- `api`: FastAPI backend;
- `db`: PostgreSQL;
- `workspace`: Docker volume for generated assets and exports.

Async profile:

- `redis`: Celery broker/backend;
- `worker`: Celery worker for asynchronous tasks.

## Backend Layers

The backend keeps provider-specific behavior behind adapter boundaries:

- Provider records describe suppliers and credential references.
- Model records describe concrete capabilities and default parameters.
- CredentialResolver reads credentials from approved backend-only sources.
- Capability adapters normalize provider API differences.
- CapabilityRunService creates experiments, calls adapters, handles errors, and coordinates asset/cost/log hooks.
- AssetService downloads or moves generated files into final workspace storage.
- Audio Lab passes existing audio assets to provider adapters through runtime-only file references. These local paths are not persisted in experiments or logs.

## Core Facts

- `Experiment`: a model call fact.
- `Asset`: a generated or uploaded material fact.
- `PromptTemplate`: reusable prompt content and version metadata.
- `Evaluation`: manual assessment facts.
- `CostRecord`: cost estimate facts.
- `InvocationLog`: invocation summary logs.
- `Task`: asynchronous execution state fact.
- `Project` and `ProjectItem`: organization layer for useful materials and experiments.
- `VoiceProfile`: governed provider voice identity for VoiceProfile-based TTS.

## Security Boundaries

- The frontend calls only this backend API.
- The frontend does not hold provider API keys.
- Adapters do not create final assets.
- Adapters do not read environment variables or Docker secrets directly.
- Stored paths are relative where they represent workspace assets.
- Runtime-only local file references must not be persisted.
- SanitizerService is responsible for redacting sensitive payloads before persistence or export.
