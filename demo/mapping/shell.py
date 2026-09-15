"""应用外壳（shell）→ 组件树。

外壳是**跨屏常驻**的容器，屏在它的内容区里切换 —— 它不是"屏的一个属性"，是独立一层。

用「模式」不用「位置」：`侧边导航` / `顶部导航`，而不是"导航放左边"。

⚠️ **实测发现**：侧边导航需要「定宽 + 自适应」两栏，而现成原语的布局能力**不足以表达**——
`Stack` 没有 flex-grow、`Grid` 只有等分列。当前只能靠 `Card.maxWidth` 近似，见 REPORT。
"""

from __future__ import annotations

from .actions import NAV_PATH, goto
from .tree import Node, el, hstack, vstack

NAV_CURRENT = f"{NAV_PATH}/current"

CARD_BARE = {"title": None, "description": None, "maxWidth": None, "centered": None}


def _menu_item(item: dict) -> Node:
    """一个菜单项。**选中态 = 「当前屏是不是它」**，用 $cond 从 state 派生，不另存一份状态。"""
    return el(
        "Button",
        label=item["label"],
        variant={
            "$cond": {"$state": NAV_CURRENT, "eq": item["goto"]},
            "$then": "primary",
            "$else": "secondary",
        },
        disabled=None,
        on={"press": goto(item["goto"])},
    )


def _menu_tree(shell: dict) -> list[Node]:
    """模块 → 功能子菜单。菜单是**功能地图的可见投影**（上游应由节点 1 的地图推导，此处手写）。"""
    groups = []
    for group in shell["menus"]:
        groups.append(
            vstack(
                el("Text", text=group["label"], variant="caption"),
                *[_menu_item(item) for item in group["items"]],
                gap="sm",
            )
        )
    return groups


def _sidebar(shell: dict) -> Node:
    return el(
        "Card",
        vstack(el("Heading", text=shell["title"], level="h3"), *_menu_tree(shell), gap="lg"),
        title=None,
        description=None,
        maxWidth="sm",
        centered=None,
    )


def _topbar(shell: dict) -> Node:
    items = [item for group in shell["menus"] for item in group["items"]]
    return el(
        "Card",
        hstack(el("Heading", text=shell["title"], level="h3"),
               *[_menu_item(i) for i in items], gap="sm", justify="between"),
        **CARD_BARE,
    )


def _side(children: list[Node], shell: dict) -> Node:
    return hstack(_sidebar(shell), vstack(*children, gap="lg"), gap="lg", align="start")


def _top(children: list[Node], shell: dict) -> Node:
    return vstack(_topbar(shell), vstack(*children, gap="lg"), gap="lg")


MODES = {
    "侧边导航": _side,
    "顶部导航": _top,
}
