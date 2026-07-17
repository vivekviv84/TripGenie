from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import authenticate_operations_request
from app.db.dependencies import get_db
from app.schemas.analytics import AnalyticsSummary, DistributionItem, MonthlyLeadCount
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(authenticate_operations_request)])


@router.get("", response_model=AnalyticsSummary)
def get_analytics(db: Session = Depends(get_db)) -> AnalyticsSummary:
    """Return dashboard overview metrics."""

    return AnalyticsService(db).summary()


@router.get("/destinations", response_model=list[DistributionItem])
def get_destination_distribution(db: Session = Depends(get_db)) -> list[DistributionItem]:
    """Return lead counts grouped by destination."""

    return AnalyticsService(db).destination_distribution()


@router.get("/priorities", response_model=list[DistributionItem])
def get_priority_distribution(db: Session = Depends(get_db)) -> list[DistributionItem]:
    """Return lead counts grouped by priority."""

    return AnalyticsService(db).priority_distribution()


@router.get("/monthly", response_model=list[MonthlyLeadCount])
def get_monthly_leads(db: Session = Depends(get_db)) -> list[MonthlyLeadCount]:
    """Return lead counts grouped by month."""

    return AnalyticsService(db).monthly_counts()
