from backend.app.main import app


def test_async_worker_compose_uses_real_celery_worker():
    compose = open("docker-compose.yml", encoding="utf-8").read()

    assert "backend.app.tasks.celery_app:celery_app" in compose
    assert "worker\", \"--loglevel=INFO\", \"-Q\", \"default,video" in compose
    assert "\"backend.app.worker\"" not in compose


def test_core_api_routes_are_registered():
    paths = {route.path for route in app.routes}
    expected = {
        "/api/system/health",
        "/api/providers",
        "/api/models",
        "/api/capabilities/run",
        "/api/experiments",
        "/api/assets",
        "/api/prompts",
        "/api/labs/voice/tts",
        "/api/labs/image/generate",
        "/api/labs/video/generate",
        "/api/evaluations/upsert",
        "/api/costs/summary",
        "/api/tasks",
        "/api/projects",
        "/api/projects/{project_id}/shots/{shot_id}",
        "/api/exports/projects/{project_id}/manifest",
    }
    assert expected.issubset(paths)

