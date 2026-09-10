from fastapi import APIRouter, Depends
from app.schemas.result import AnalysisResultResponse, KpiResponse
from app.services.analysis_service import AnalysisService
from app.dependencies.auth import get_current_user, get_db

router = APIRouter()

@router.get("/{dataset_id}", response_model=AnalysisResultResponse)
def get_results(
    dataset_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    return AnalysisService.get_results(
        dataset_id,
        current_user.id,
        db,
    )

@router.get("/{dataset_id}/kpis", response_model=KpiResponse)
def get_kpis(dataset_id: str, current_user = Depends(get_current_user)):
    return AnalysisService.get_kpis(dataset_id)
