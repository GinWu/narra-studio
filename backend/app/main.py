from __future__ import annotations

from fastapi import FastAPI

from backend.app.api.assets import router as assets_router
from backend.app.api.audio import router as audio_router
from backend.app.api.capabilities import router as capabilities_router
from backend.app.api.costs import router as costs_router
from backend.app.api.experiments import router as experiments_router
from backend.app.api.exports import router as exports_router
from backend.app.api.evaluations import router as evaluations_router
from backend.app.api.image import router as image_router
from backend.app.api.models import router as models_router
from backend.app.api.prompts import router as prompts_router
from backend.app.api.projects import router as projects_router
from backend.app.api.providers import router as providers_router
from backend.app.api.system import router as system_router
from backend.app.api.tasks import router as tasks_router
from backend.app.api.voice import router as voice_router
from backend.app.api.voice_profiles import router as voice_profiles_router
from backend.app.api.video import router as video_router
from backend.app.config import get_settings
from backend.app.logging_config import configure_logging


from fastapi.middleware.cors import CORSMiddleware

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="Narra Studio API",
    version="0.1.0",
    description="Docker-first backend API for Narra Studio.",
)

# Enable CORS for local and remote browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router, prefix="/api/system", tags=["system"])
app.include_router(capabilities_router, prefix="/api/capabilities", tags=["capabilities"])
app.include_router(experiments_router, prefix="/api/experiments", tags=["experiments"])
app.include_router(evaluations_router, prefix="/api/evaluations", tags=["evaluations"])
app.include_router(exports_router, prefix="/api/exports", tags=["exports"])
app.include_router(assets_router, prefix="/api/assets", tags=["assets"])
app.include_router(costs_router, prefix="/api/costs", tags=["costs"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
app.include_router(providers_router, prefix="/api/providers", tags=["providers"])
app.include_router(models_router, prefix="/api/models", tags=["models"])
app.include_router(prompts_router, prefix="/api/prompts", tags=["prompts"])
app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
app.include_router(voice_router, prefix="/api/labs/voice", tags=["voice-lab"])
app.include_router(voice_profiles_router, prefix="/api/voice-profiles", tags=["voice-profiles"])
app.include_router(audio_router, prefix="/api/labs/audio", tags=["audio-lab"])
app.include_router(image_router, prefix="/api/labs/image", tags=["image-lab"])
app.include_router(video_router, prefix="/api/labs/video", tags=["video-lab"])


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "narra-studio-api",
        "status": "ok",
        "health": "/api/system/health",
    }
