"""布局模式 → 页面骨架。

用「模式」不用「位置」：`列表页` 不是「左列表右详情」。
这一层只决定：页面纵向怎么排、内容要不要收窄。

⚠️ **窄屏怎么堆叠不是渲染器自动给的**（实测：`Grid(columns=N)` 窄屏不重排）。
需要窄屏降级时，降级规则要**写在这一层**，不能指望渲染器。
"""

from __future__ import annotations

from .tree import Node, el, vstack


def _stack(children: list[Node]) -> Node:
    return vstack(*children, gap="lg")


def _narrow(children: list[Node]) -> Node:
    """表单/结果这类「单列、收窄、居中」的页面模式。"""
    return el("Card", _stack(children), title=None, description=None,
              maxWidth="md", centered=True)


LAYOUTS = {
    "列表页": _stack,
    "表单页": _narrow,
    "结果页": _narrow,
    "详情页": _narrow,   # 与结果页同为「单列收窄」——模式是意图，实现可以复用
}
