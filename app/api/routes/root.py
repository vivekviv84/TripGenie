from fastapi import APIRouter

router = APIRouter(tags=["root"])


@router.get("/")
def read_root() -> dict[str, str]:
    """Return a small service identity response."""

    return {"service": "TripGenie AI Backend", "status": "running"}
