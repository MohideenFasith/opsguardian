from __future__ import annotations

import asyncio
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from opsguardian.config import settings
from opsguardian.storage import SQLiteStore
from opsguardian.strands_advisor import StrandsAdvisor
from opsguardian.workflow import IncidentEngine


async def main() -> None:
    settings.strands_mode = "offline"
    settings.demo_delay_ms = 0
    with tempfile.TemporaryDirectory() as tmp:
        store = SQLiteStore(str(Path(tmp) / "smoke.db"))
        engine = IncidentEngine(store, StrandsAdvisor())
        incident = engine.create_incident(auto_approve=True)
        await engine.run(incident.id)
        final = store.get(incident.id)
        assert final is not None
        assert final.status.value == "resolved"
        assert final.selected_fix and final.selected_fix["checks_passed"] == 17
        assert final.verification["pipeline_run"] == "success"
        print(f"SMOKE PASS incident={final.id} status={final.status.value} events={len(final.timeline)}")


if __name__ == "__main__":
    asyncio.run(main())
