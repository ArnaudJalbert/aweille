from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from aweille.core import SectionInput


@pytest.fixture
def run_input() -> dict[str, Any]:
    return {
        "id": UUID("54D97D4D-FADB-4D50-926E-AF1BB26C711A"),
        "planned_date": date(2026, 10, 14),
        "run_type": "interval",
        "sections": [
            SectionInput(Decimal("1.000"), 390),
            SectionInput(Decimal("1"), 345),
            SectionInput(Decimal("1"), 390),
        ],
        "user_note": "  Keep the first section easy.  ",
        "trainer_note": "  Finish relaxed.  ",
    }
