from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.schemas.analytics import AnalyticsSummary, DistributionItem, MonthlyLeadCount


class AnalyticsService:
    """Read-only dashboard analytics over active leads."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def summary(self) -> AnalyticsSummary:
        """Return high-level metrics for a dashboard overview."""

        total = self._count()
        priority_counts = {item.label: item.count for item in self.priority_distribution()}
        return AnalyticsSummary(
            total_leads=total,
            hot_leads=priority_counts.get("HOT", 0),
            warm_leads=priority_counts.get("WARM", 0),
            cold_leads=priority_counts.get("COLD", 0),
            average_lead_score=self._average(Lead.lead_score),
            average_budget=self._average(Lead.budget),
            average_call_duration=self._average(Lead.call_duration),
            most_popular_destination=self._top_value(Lead.destination),
            most_common_trip_type=self._top_value(Lead.trip_type),
            monthly_lead_count=self.monthly_counts(),
        )

    def destination_distribution(self) -> list[DistributionItem]:
        """Return active leads grouped by destination."""

        return self._distribution(Lead.destination)

    def priority_distribution(self) -> list[DistributionItem]:
        """Return active leads grouped by HOT/WARM/COLD priority."""

        return self._distribution(Lead.lead_priority)

    def monthly_counts(self) -> list[MonthlyLeadCount]:
        """Return active lead counts grouped by creation month."""

        month_expr = func.to_char(func.date_trunc("month", Lead.created_at), "YYYY-MM")
        rows = self.db.execute(
            select(month_expr.label("month"), func.count(Lead.id))
            .where(Lead.deleted_at.is_(None))
            .group_by("month")
            .order_by("month")
        ).all()
        return [MonthlyLeadCount(month=row[0], count=row[1]) for row in rows]

    def _count(self) -> int:
        """Return active lead count."""

        return self.db.execute(select(func.count(Lead.id)).where(Lead.deleted_at.is_(None))).scalar_one()

    def _average(self, column: object) -> float | None:
        """Return an average for a nullable numeric column."""

        value = self.db.execute(select(func.avg(column)).where(Lead.deleted_at.is_(None))).scalar_one()
        return round(float(value), 2) if value is not None else None

    def _top_value(self, column: object) -> str | None:
        """Return the most common non-empty value for a column."""

        row = self.db.execute(
            select(column, func.count(Lead.id).label("count"))
            .where(Lead.deleted_at.is_(None), column.is_not(None))
            .group_by(column)
            .order_by(func.count(Lead.id).desc())
            .limit(1)
        ).first()
        return str(row[0]) if row else None

    def _distribution(self, column: object) -> list[DistributionItem]:
        """Return label/count distribution for a nullable column."""

        rows = self.db.execute(
            select(column, func.count(Lead.id))
            .where(Lead.deleted_at.is_(None), column.is_not(None))
            .group_by(column)
            .order_by(func.count(Lead.id).desc())
        ).all()
        return [DistributionItem(label=str(row[0]), count=row[1]) for row in rows]
