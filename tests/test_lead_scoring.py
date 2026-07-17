from decimal import Decimal
from types import SimpleNamespace

from app.services.lead_scoring import LeadScoringService


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        lead_hot_threshold=75,
        lead_warm_threshold=45,
        lead_high_intent_threshold=70,
        lead_medium_intent_threshold=40,
        lead_realistic_budget_min=50000,
        lead_score_weight_destination=15,
        lead_score_weight_travel_month=15,
        lead_score_weight_travellers=10,
        lead_score_weight_budget_available=15,
        lead_score_weight_budget_realistic=10,
        lead_score_weight_customer_intent=15,
        lead_score_weight_trip_type=10,
        lead_score_weight_additional_requirements=10,
    )


def test_hot_lead_scores_to_100() -> None:
    service = LeadScoringService(_settings())

    result = service.score(
        {
            "destination": "Bali",
            "travel_month": "December",
            "travellers": 2,
            "budget": Decimal("150000"),
            "outcome": "qualified",
            "trip_type": "honeymoon",
            "additional_requirements": "Ready to book private pool",
        }
    )

    assert result.lead_score == 100
    assert result.lead_priority == "HOT"
    assert result.booking_intent == "HIGH"
    assert result.follow_up_action == "Send honeymoon package"


def test_cold_lead_recommends_budget_collection() -> None:
    service = LeadScoringService(_settings())

    result = service.score(
        {
            "destination": None,
            "travel_month": None,
            "travellers": None,
            "budget": None,
            "outcome": None,
            "trip_type": None,
            "additional_requirements": None,
        }
    )

    assert result.lead_score == 0
    assert result.lead_priority == "COLD"
    assert result.booking_intent == "LOW"
    assert result.follow_up_action == "Collect missing budget information"
