from pydantic import BaseModel


class DistributionItem(BaseModel):
    """A label/count pair for dashboard charts."""

    label: str
    count: int


class MonthlyLeadCount(BaseModel):
    """Lead count grouped by month."""

    month: str
    count: int


class AnalyticsSummary(BaseModel):
    """Dashboard-ready lead analytics summary."""

    total_leads: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    average_lead_score: float | None
    average_budget: float | None
    average_call_duration: float | None
    most_popular_destination: str | None
    most_common_trip_type: str | None
    monthly_lead_count: list[MonthlyLeadCount]
