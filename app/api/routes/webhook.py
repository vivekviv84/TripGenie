from time import perf_counter

from fastapi import APIRouter, Depends

from app.api.dependencies import authenticate_webhook_request, get_lead_processing_service
from app.core.logging import get_logger
from app.schemas.webhook import IncomingWebhook, WebhookProcessingResponse
from app.services.lead_processing import LeadProcessingService

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = get_logger(__name__)


@router.post(
    "/call-end",
    response_model=WebhookProcessingResponse,
    dependencies=[Depends(authenticate_webhook_request)],
)
def receive_call_end_webhook(
    payload: IncomingWebhook,
    service: LeadProcessingService = Depends(get_lead_processing_service),
) -> WebhookProcessingResponse:
    """Receive a completed-call webhook and persist the extracted lead."""

    started_at = perf_counter()
    conversation_id = payload.call.conversation_id
    logger.info("Incoming webhook received")
    logger.info("Conversation ID: %s", conversation_id or "missing")

    result = service.process_call_end_webhook(payload)

    processing_time_ms = round((perf_counter() - started_at) * 1000, 2)
    logger.info(
        "Webhook processing completed conversation_id=%s processing_time_ms=%s",
        result.conversation_id or "missing",
        processing_time_ms,
    )

    return WebhookProcessingResponse(
        status="success",
        lead_id=result.lead_id,
        conversation_id=result.conversation_id,
        created=result.created,
        message="Lead processed successfully",
    )
