from collections.abc import Callable
from time import monotonic, sleep
from typing import TypeVar

import json
from google.oauth2.service_account import Credentials

import gspread
from google.auth.exceptions import GoogleAuthError
from gspread import Spreadsheet, Worksheet
from gspread.exceptions import GSpreadException, SpreadsheetNotFound, WorksheetNotFound

from app.core.config import Settings
from app.core.logging import get_logger
from app.models.lead import Lead
from app.services.sheet_mapping import (
    CONVERSATION_ID_COLUMN_INDEX,
    LEGACY_SHEET_COLUMNS,
    SHEET_COLUMNS,
    LeadSheetMapper,
)

logger = get_logger(__name__)
T = TypeVar("T")


class GoogleSheetsService:
    """Synchronize persisted leads into a configured Google worksheet."""

    SCOPES = (
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    )
    MAX_RETRIES = 3
    BASE_BACKOFF_SECONDS = 1.0

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._worksheet: Worksheet | None = None

    def verify_connection(self) -> None:
        """Authenticate and open the configured worksheet during startup."""

        if not self.settings.google_sheets_enabled:
            logger.info("Google Sheets disabled")
            return
        self._get_worksheet()

    def append_lead(self, lead: Lead) -> bool:
        """Append a lead row to Google Sheets, retrying transient failures."""

        return self._run_with_retry("append", lambda: self._append_lead_once(lead))

    def update_lead(self, lead: Lead) -> bool:
        """Update a lead row by conversation id, or append if it is not present."""

        return self._run_with_retry("update", lambda: self._update_lead_once(lead))

    def _append_lead_once(self, lead: Lead) -> None:
        """Append a lead row once without retry handling."""

        started_at = monotonic()
        worksheet = self._get_worksheet()
        logger.info("Google Sheets append started conversation_id=%s", lead.conversation_id or "missing")
        response = worksheet.append_row(
            LeadSheetMapper.to_row(lead),
            value_input_option="USER_ENTERED",
            table_range="A1",
        )
        row_number = self._row_number_from_append_response(response)
        if row_number is not None and hasattr(lead, "google_sheet_row"):
            lead.google_sheet_row = row_number
        duration_ms = round((monotonic() - started_at) * 1000, 2)
        logger.info(
            "Google Sheets append completed conversation_id=%s duration_ms=%s",
            lead.conversation_id or "missing",
            duration_ms,
        )

    def _update_lead_once(self, lead: Lead) -> None:
        """Update an existing lead row once without retry handling."""

        if not lead.conversation_id:
            self._append_lead_once(lead)
            return

        started_at = monotonic()
        worksheet = self._get_worksheet()
        logger.info("Google Sheets update started conversation_id=%s", lead.conversation_id)
        if getattr(lead, "google_sheet_row", None):
            row_number = lead.google_sheet_row
        else:
            try:
                cell = worksheet.find(lead.conversation_id, in_column=CONVERSATION_ID_COLUMN_INDEX)
                row_number = cell.row
                if hasattr(lead, "google_sheet_row"):
                    lead.google_sheet_row = row_number
            except Exception:
                logger.info("Google Sheets row not found; appending conversation_id=%s", lead.conversation_id)
                self._append_lead_once(lead)
                return

        row_range = f"A{row_number}:{self._column_letter(len(SHEET_COLUMNS))}{row_number}"
        worksheet.update(
            range_name=row_range,
            values=[LeadSheetMapper.to_row(lead)],
            value_input_option="USER_ENTERED",
        )
        duration_ms = round((monotonic() - started_at) * 1000, 2)
        logger.info(
            "Google Sheets update completed conversation_id=%s duration_ms=%s",
            lead.conversation_id,
            duration_ms,
        )

    def _get_worksheet(self) -> Worksheet:
        """Return a cached worksheet, authenticating on first use."""

        if self._worksheet is not None:
            return self._worksheet

        try:
            if not self.settings.google_sheets_enabled:
                raise ValueError("Google Sheets is disabled")
            if self.settings.google_service_account_json:
                credentials_info = json.loads(
                    self.settings.google_service_account_json
                )

                credentials = Credentials.from_service_account_info(
                    credentials_info,
                    scopes=list(self.SCOPES),
                )

                client = gspread.authorize(credentials)

            else:
                client = gspread.service_account(
                    filename=str(self.settings.google_service_account_file),
                    scopes=list(self.SCOPES),
                )

            logger.info("Google Sheets authentication succeeded")

            spreadsheet: Spreadsheet = client.open_by_key(
                str(self.settings.google_sheet_id)
            )

            worksheet = spreadsheet.worksheet(
                str(self.settings.google_worksheet)
            )

            logger.info(
                "Google worksheet opened: %s",
                self.settings.google_worksheet,
            )
            self._ensure_header_row(worksheet)
            self._worksheet = worksheet
            return worksheet

        except (
            GoogleAuthError,
            SpreadsheetNotFound,
            WorksheetNotFound,
            GSpreadException,
        ):
            logger.exception("Google Sheets connection failed")
            raise

    def _ensure_header_row(self, worksheet: Worksheet) -> None:
        """Ensure the first worksheet row contains the expected lead columns."""

        current_headers = worksheet.row_values(1)
        expected_headers = list(SHEET_COLUMNS)

        if current_headers == expected_headers:
            return

        if current_headers == list(LEGACY_SHEET_COLUMNS):
            worksheet.update(
                range_name=f"A1:{self._column_letter(len(SHEET_COLUMNS))}1",
                values=[expected_headers],
                value_input_option="RAW",
            )
            logger.info("Google worksheet header row upgraded for lead scoring columns")
            return

        if current_headers:
            logger.error("Google worksheet header row does not match expected lead columns")
            raise ValueError("Google worksheet header row does not match expected lead columns")

        worksheet.update(
            range_name=f"A1:{self._column_letter(len(SHEET_COLUMNS))}1",
            values=[expected_headers],
            value_input_option="RAW",
        )
        logger.info("Google worksheet header row initialized")

    @staticmethod
    def _column_letter(column_number: int) -> str:
        """Return a Google Sheets column letter for a one-based column number."""

        letters = ""
        current = column_number
        while current:
            current, remainder = divmod(current - 1, 26)
            letters = chr(65 + remainder) + letters
        return letters

    @staticmethod
    def _row_number_from_append_response(response: object) -> int | None:
        """Extract the appended row number from a Google Sheets API response."""

        if not isinstance(response, dict):
            return None
        updates = response.get("updates", {})
        updated_range = updates.get("updatedRange")
        if not isinstance(updated_range, str) or "!" not in updated_range:
            return None
        range_part = updated_range.split("!", maxsplit=1)[1]
        digits = "".join(character for character in range_part if character.isdigit())
        return int(digits) if digits else None

    def _run_with_retry(self, operation_name: str, operation: Callable[[], T]) -> bool:
        """Run a Sheets operation with exponential backoff and no caller exception."""

        started_at = monotonic()

        max_attempts = self.MAX_RETRIES + 1

        for attempt in range(1, max_attempts + 1):
            try:
                operation()
                duration_ms = round((monotonic() - started_at) * 1000, 2)
                logger.info("Google Sheets %s finished duration_ms=%s", operation_name, duration_ms)
                return True
            except Exception as exc:
                if attempt == max_attempts:
                    duration_ms = round((monotonic() - started_at) * 1000, 2)
                    logger.exception(
                        "Google Sheets %s failed after %s attempt(s) duration_ms=%s",
                        operation_name,
                        attempt,
                        duration_ms,
                    )
                    return False

                backoff_seconds = self.BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "Google Sheets %s retry attempt=%s next_retry_seconds=%s error_type=%s",
                    operation_name,
                    attempt,
                    backoff_seconds,
                    exc.__class__.__name__,
                )
                sleep(backoff_seconds)

        return False
