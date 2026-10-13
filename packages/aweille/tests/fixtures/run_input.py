from datetime import date
from typing import Any
from uuid import UUID

import pytest
from aweille.core import Distance, Pace, RunType, Section


@pytest.fixture
def run_input() -> dict[str, Any]:
    return {
        "id": UUID("54D97D4D-FADB-4D50-926E-AF1BB26C711A"),
        "planned_date": date(2026, 10, 14),
        "run_type": RunType.INTERVAL,
        "sections": [
            Section(Distance(1000), Pace(390)),
            Section(Distance(1000), Pace(345)),
            Section(Distance(1000), Pace(390)),
        ],
        "user_note": "  Keep the first section easy.  ",
        "trainer_note": "  Finish relaxed.  ",
    }
