from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.lead import Lead


class LeadRepository:
    """Persistence operations for lead records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_conversation_id(self, conversation_id: str) -> Lead | None:
        """Return a lead by external conversation id when one exists."""

        statement = select(Lead).where(Lead.conversation_id == conversation_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_active_by_id(self, lead_id: UUID) -> Lead | None:
        """Return a non-deleted lead by id."""

        statement = select(Lead).where(Lead.id == lead_id, Lead.deleted_at.is_(None))
        return self.db.execute(statement).scalar_one_or_none()

    def list_active(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        priority: str | None = None,
        destination: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Lead], int]:
        """Return paginated active leads with optional filters and sorting."""

        statement = self._active_filtered_statement(
            status=status,
            priority=priority,
            destination=destination,
            search=search,
        )
        total = self.db.execute(select(func.count()).select_from(statement.subquery())).scalar_one()

        sort_column = self._sort_column(sort_by)
        direction = desc if sort_order.lower() == "desc" else asc
        rows = self.db.execute(
            statement.order_by(direction(sort_column)).offset((page - 1) * page_size).limit(page_size)
        ).scalars().all()
        return list(rows), total

    def _active_filtered_statement(
        self,
        *,
        status: str | None = None,
        priority: str | None = None,
        destination: str | None = None,
        search: str | None = None,
    ) -> Select[tuple[Lead]]:
        """Build the base active-lead query shared by list and count operations."""

        statement = select(Lead).where(Lead.deleted_at.is_(None))
        if status:
            statement = statement.where(Lead.status == status)
        if priority:
            statement = statement.where(Lead.lead_priority == priority)
        if destination:
            statement = statement.where(Lead.destination.ilike(f"%{destination}%"))
        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    Lead.customer_name.ilike(search_pattern),
                    Lead.phone.ilike(search_pattern),
                    Lead.destination.ilike(search_pattern),
                    Lead.conversation_id.ilike(search_pattern),
                )
            )
        return statement

    @staticmethod
    def _sort_column(sort_by: str) -> Any:
        """Return a safe sort column from a small allow-list."""

        allowed_columns = {
            "created_at": Lead.created_at,
            "updated_at": Lead.updated_at,
            "lead_score": Lead.lead_score,
            "budget": Lead.budget,
            "customer_name": Lead.customer_name,
        }
        return allowed_columns.get(sort_by, Lead.created_at)

    def create(self, values: Mapping[str, Any]) -> Lead:
        """Create and persist a new lead."""

        lead = Lead(**values)
        self.db.add(lead)
        self.db.flush()
        return lead

    def update(self, lead: Lead, values: Mapping[str, Any]) -> Lead:
        """Update an existing lead with normalized webhook values."""

        for field_name, field_value in values.items():
            setattr(lead, field_name, field_value)
        self.db.flush()
        return lead

    def soft_delete(self, lead: Lead) -> Lead:
        """Mark a lead as deleted without removing it from the database."""

        lead.deleted_at = datetime.now(timezone.utc)
        self.db.flush()
        return lead

    def update_google_sheet_row(self, lead_id: UUID, row_number: int) -> None:
        """Persist the Google Sheet row number for faster future updates."""

        lead = self.db.get(Lead, lead_id)
        if lead is not None:
            lead.google_sheet_row = row_number
            self.db.flush()

    def commit(self) -> None:
        """Commit the current transaction."""

        self.db.commit()

    def rollback(self) -> None:
        """Roll back the current transaction."""

        self.db.rollback()
