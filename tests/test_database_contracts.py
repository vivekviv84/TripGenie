from types import SimpleNamespace
from uuid import uuid4

from app.services.lead_management import LeadManagementService


class FakeLeadRepository:
    def __init__(self) -> None:
        self.lead = SimpleNamespace(id=uuid4(), deleted_at=None)
        self.committed = False

    def get_active_by_id(self, lead_id):
        return self.lead

    def soft_delete(self, lead):
        lead.deleted_at = "deleted"
        return lead

    def commit(self):
        self.committed = True


def test_lead_management_soft_delete_uses_repository() -> None:
    repository = FakeLeadRepository()
    service = LeadManagementService(repository)

    service.delete_lead(repository.lead.id)

    assert repository.lead.deleted_at == "deleted"
    assert repository.committed is True
