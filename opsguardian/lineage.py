from __future__ import annotations

import json
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LINEAGE_PATH = ROOT / "sample_data" / "lineage.json"


def trace_downstream(source: str, path: Path = DEFAULT_LINEAGE_PATH) -> list[str]:
    """Return unique downstream assets in breadth-first dependency order."""
    graph: dict[str, list[str]] = json.loads(path.read_text())
    seen = {source}
    out: list[str] = []
    queue = deque(graph.get(source, []))
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        out.append(node)
        queue.extend(graph.get(node, []))
    return out
