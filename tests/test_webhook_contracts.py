from types import SimpleNamespace

from app.schemas.webhook import IncomingWebhook
from app.services.lead_processing import LeadProcessingService


class FakeLeadRepository:
    def __init__(self) -> None:
        self.created_values = None
        self.committed = False

    def get_by_conversation_id(self, conversation_id):
        return None

    def create(self, values):
        self.created_values = values
        return SimpleNamespace(id="lead-1", conversation_id=values["conversation_id"])

    def commit(self):
        self.committed = True

    def rollback(self):
        self.committed = False


class FakeScoringService:
    def score(self, values):
        return SimpleNamespace(
            lead_score=90,
            lead_priority="HOT",
            lead_reason="Test reason",
            booking_intent="HIGH",
            travel_urgency="Within 3 Months",
            lead_summary="Test summary",
            next_action="Call within 2 hours",
            follow_up_action="Call within 2 hours",
        )


class FakeSyncService:
    def append_lead(self, lead):
        return True

    def update_lead(self, lead):
        return True


def test_webhook_processing_scores_and_persists_lead() -> None:
    repository = FakeLeadRepository()
    service = LeadProcessingService(repository, FakeScoringService(), FakeSyncService())
    payload = IncomingWebhook.model_validate(
        {
            "call": {"conversation_id": "conv_test"},
            "lead": {
                "customer_name": "Priya",
                "phone": "+919999999999",
                "destination": "Bali",
                "budget": "INR 100000",
            },
        }
    )

    result = service.process_call_end_webhook(payload)

    assert result.created is True
    assert repository.committed is True
    assert repository.created_values["lead_score"] == 90
