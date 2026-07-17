from app.schemas.analytics import AnalyticsSummary, MonthlyLeadCount
from app.schemas.monitoring import ComponentStatus, HealthResponse
from datetime import datetime, timezone


def test_analytics_summary_contract() -> None:
    response = AnalyticsSummary(
        total_leads=1,
        hot_leads=1,
        warm_leads=0,
        cold_leads=0,
        average_lead_score=90.0,
        average_budget=100000.0,
        average_call_duration=200.0,
        most_popular_destination="Bali",
        most_common_trip_type="honeymoon",
        monthly_lead_count=[MonthlyLeadCount(month="2026-07", count=1)],
    )

    assert response.total_leads == 1
    assert response.monthly_lead_count[0].month == "2026-07"


def test_health_response_contract() -> None:
    response = HealthResponse(
        status="ok",
        database=ComponentStatus(status="ok"),
        google_sheets=ComponentStatus(status="ok"),
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
    )

    assert response.database.status == "ok"
    assert response.google_sheets.status == "ok"
