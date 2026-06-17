# Roadmap

中文版本见 [ROADMAP.zh-CN.md](ROADMAP.zh-CN.md).

This roadmap describes public product direction at a high level. It is not a promise of delivery dates.

## Current Focus

- Local Docker-first media model studio.
- Mock-first end-to-end workflows for audio, image, and video experiments.
- Experiment, asset, prompt, evaluation, cost, log, task, and project records.
- Safe provider credential references and backend-only provider calls.
- Initial Audio Lab backend support for STT, voice clone, and VoiceProfile-based TTS.

## Near-Term Improvements

- Live-verify and calibrate selected real provider adapters, including Alibaba Cloud Bailian / DashScope speech endpoints.
- Harden real provider adapters for selected TTS, STT, voice clone, and image generation APIs.
- Improve async video provider support and polling.
- Add richer frontend workflows for prompt templates, evaluations, cost summaries, and project workspaces.
- Add end-to-end Docker smoke tests for async video generation.
- Improve public documentation and setup experience.

## Later Ideas

- Image editing, image variation, and reference-image workflows.
- Rich VoiceProfile and voice-cloning consent UI workflows.
- Provider webhook support with signature verification and replay protection.
- Project bundle exports.
- Team collaboration, accounts, RBAC, and audit logs.
- Optional encrypted local credential storage.

## Non-Goals for Now

- Commercial billing.
- Fully automated content production pipelines.
- Frontend-side direct calls to external AI providers.
