from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.capabilities.bootstrap import build_default_adapter_registry
from backend.app.schemas.capability import CapabilityRunCreate, CapabilityRunRead
from backend.app.services.asset_service import AssetService
from backend.app.services.capability_run_service import CapabilityRunCommand, CapabilityRunService
from backend.app.services.cost_service import CostService


router = APIRouter()
default_adapter_registry = build_default_adapter_registry()


@router.post("/run", response_model=CapabilityRunRead)
def run_capability(payload: CapabilityRunCreate, db: Session = Depends(get_db)):
    outcome = CapabilityRunService(
        db,
        default_adapter_registry,
        asset_processor=AssetService(db),
        cost_recorder=CostService(db),
    ).run(
        CapabilityRunCommand(**payload.model_dump())
    )
    return CapabilityRunRead(
        experiment_id=outcome.experiment.id,
        status=outcome.experiment.status,
        result_mode=outcome.experiment.result_mode,
        output_asset_refs_json=outcome.experiment.output_asset_refs_json,
        error_json=outcome.experiment.error_json,
    )
