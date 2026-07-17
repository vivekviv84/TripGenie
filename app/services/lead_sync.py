from typing import Any, Protocol


class LeadSyncService(Protocol):
    """Interface for secondary lead sync destinations."""

    def append_lead(self, lead: Any) -> bool:
        """Append a newly created lead to the destination."""

    def update_lead(self, lead: Any) -> bool:
        """Update an existing lead in the destination."""
