from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.services.sheet_mapping import SHEET_COLUMNS, LeadSheetMapper


def test_sheet_mapper_outputs_one_value_per_column() -> None:
    lead = SimpleNamespace(
        created_at=datetime(2026, 7, 17, tzinfo=timezone.utc),
        customer_name="Priya Sharma",
        phone="+919876543210",
        destination="Bali",
        travel_month="December",
        travellers=2,
        trip_type="honeymoon",
        budget=Decimal("150000"),
        hotel_preference="5 star resort",
        additional_requirements="Private pool",
        lead_score=100,
        lead_priority="HOT",
        lead_reason="Strong lead",
        booking_intent="HIGH",
        travel_urgency="3-12 Months",
        status="new",
        next_action="Send honeymoon package",
        follow_up_action="Send honeymoon package",
        lead_summary="Short summary",
        call_duration=245,
        outcome="qualified",
        conversation_id="conv_123",
        recording_url="https://example.com/recording.mp3",
    )

    row = LeadSheetMapper.to_row(lead)

    assert len(row) == len(SHEET_COLUMNS)
    assert row[SHEET_COLUMNS.index("Priority")] == "HOT"
    assert row[SHEET_COLUMNS.index("Booking Intent")] == "HIGH"
    assert row[SHEET_COLUMNS.index("Budget")] == "150000.00"
