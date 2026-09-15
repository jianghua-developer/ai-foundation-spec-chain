"""catalog 是资产：组件目录由渲染器侧 dump 成快照，映射层只读、不手抄一份 schema。

快照由 `tools/dump-catalog.mjs` 生成（`npm run dump-catalog`）。
"""

from __future__ import annotations

import json
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parent.parent / "catalog.snapshot.json"
CATALOG: dict[str, dict] = json.loads(SNAPSHOT.read_text(encoding="utf-8"))


class TreeError(Exception):
    """组件树违反 catalog 契约。"""


def props_of(component: str) -> list[str]:
    if component not in CATALOG:
        raise TreeError(f"catalog 里没有组件 {component!r}")
    return CATALOG[component]["props"]


def events_of(component: str) -> list[str]:
    if component not in CATALOG:
        raise TreeError(f"catalog 里没有组件 {component!r}")
    return CATALOG[component]["events"]
