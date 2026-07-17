from datetime import datetime
from decimal import Decimal
from typing import Any

from app.models.lead import Lead

LEGACY_SHEET_COLUMNS: tuple[str, ...] = (
    "Timestamp",
    "Customer",
    "Phone",
    "Destination",
    "Travel Month",
    "Travellers",
    "Trip Type",
    "Budget",
    "Hotel Preference",
    "Additional Requirements",
    "Lead Score",
    "Lead Priority",
    "Status",
    "Next Action",
    "Call Duration",
    "Outcome",
    "Conversation ID",
    "Recording URL",
)

SHEET_COLUMNS: tuple[str, ...] = (
    "Timestamp",
    "Customer",
    "Phone",
    "Destination",
    "Travel Month",
    "Travellers",
    "Trip Type",
    "Budget",
    "Hotel Preference",
    "Additional Requirements",
    "Lead Score",
    "Priority",
    "Reason",
    "Booking Intent",
    "Travel Urgency",
    "Status",
    "Next Action",
    "Follow-up Action",
    "Lead Summary",
    "Call Duration",
    "Outcome",
    "Conversation ID",
    "Recording URL",
)

CONVERSATION_ID_COLUMN_INDEX = SHEET_COLUMNS.index("Conversation ID") + 1


class LeadSheetMapper:
    """Map Lead ORM records into Google Sheets rows."""

    @staticmethod
    def to_row(lead: Lead) -> list[str]:
        """Return a row matching the configured Google Sheets column order."""

        return [
            LeadSheetMapper._format_value(lead.created_at),
            LeadSheetMapper._format_value(lead.customer_name),
            LeadSheetMapper._format_value(lead.phone),
            LeadSheetMapper._format_value(lead.destination),
            LeadSheetMapper._format_value(lead.travel_month),
            LeadSheetMapper._format_value(lead.travellers),
            LeadSheetMapper._format_value(lead.trip_type),
            LeadSheetMapper._format_value(lead.budget),
            LeadSheetMapper._format_value(lead.hotel_preference),
            LeadSheetMapper._format_value(lead.additional_requirements),
            LeadSheetMapper._format_value(lead.lead_score),
            LeadSheetMapper._format_value(lead.lead_priority),
            LeadSheetMapper._format_value(lead.lead_reason),
            LeadSheetMapper._format_value(lead.booking_intent),
            LeadSheetMapper._format_value(lead.travel_urgency),
            LeadSheetMapper._format_value(lead.status),
            LeadSheetMapper._format_value(lead.next_action),
            LeadSheetMapper._format_value(lead.follow_up_action),
            LeadSheetMapper._format_value(lead.lead_summary),
            LeadSheetMapper._format_value(lead.call_duration),
            LeadSheetMapper._format_value(lead.outcome),
            LeadSheetMapper._format_value(lead.conversation_id),
            LeadSheetMapper._format_value(lead.recording_url),
        ]

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format Python values into Sheets-friendly strings."""

        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Decimal):
            return f"{value:.2f}"
        return str(value)
