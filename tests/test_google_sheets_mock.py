from types import SimpleNamespace

import pytest

from app.services.google_sheets import GoogleSheetsService


@pytest.mark.google_sheets
def test_column_letter_supports_columns_after_z() -> None:
    service = GoogleSheetsService(SimpleNamespace())

    assert service._column_letter(1) == "A"
    assert service._column_letter(26) == "Z"
    assert service._column_letter(27) == "AA"
