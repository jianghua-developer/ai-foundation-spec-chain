"""映射层入口：页面语义描述（+ 数据）→ 组件树。

纯函数：同输入必同输出，无随机、无时间、无 IO、无 LLM。
"""

from __future__ import annotations

from typing import Any

from .actions import NAV_PATH
from .layout import LAYOUTS
from .semantics import BLOCKS, Ctx
from .shell import MODES
from .tree import Node, Ref, to_elements, to_spec, vstack


def _nest(pairs: dict[str, Any]) -> dict:
    """{'/a/b': v} → {'a': {'b': v}}。state 是嵌套对象，路径是 JSON Pointer。"""
    out: dict = {}
    for path, value in pairs.items():
        parts = [p for p in path.split("/") if p]
        cur = out
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
        cur[parts[-1]] = value
    return out


def _initial_state(screen: dict, ctx: Ctx) -> dict:
    """表单/筛选的初值。只读字段从数据取，可编辑字段留空。"""
    pairs: dict[str, Any] = {}
    for block in screen["blocks"]:
        if block["kind"] == "筛选栏":
            for field in block["fields"]:
                pairs[ctx.state("filter", field["id"])] = ""
        elif block["kind"] == "表单":
            for field in block["fields"]:
                if field.get("value_from"):
                    pairs[ctx.state("form", field["id"])] = ctx.resolve(field["value_from"]) or ""
                else:
                    pairs[ctx.state("form", field["id"])] = ""
    return _nest(pairs)


def render_screen(screen: dict, fixture: dict, pages: dict | None = None) -> dict:
    ctx = Ctx(screen["id"], fixture, pages)
    children: list[Node] = [
        node
        for block in screen["blocks"]
        for node in BLOCKS[block["kind"]](block, ctx)
    ]
    layout = LAYOUTS[screen.get("layout", "列表页")]
    return to_spec(layout(children), screen["id"].lower(), state=_initial_state(screen, ctx))


def render_pages(pages: dict, fixture: dict) -> dict:
    """整份页面语义描述 → **一棵组件树**（含可点原型与外壳）。

    各屏不是分开的 spec，而是同一棵树里由 `visible` 控制的子树：
        visible: {$state: "/nav/current", eq: "SCR#"}
    切屏 = 把 `/nav/current` 写进 state（`setState`，渲染器内置动作）。

    外壳（`shell`）**跨屏常驻**：它是屏的容器，不在 `visible` 的管辖范围内。
    于是**导航零宿主代码**：宿主只负责「把拿到的树渲染出来」，不需要知道
    「有几屏」「当前在哪一屏」「菜单有几级」「按钮点了跳哪」——全是映射层的产出。
    """
    screens = {s["id"]: render_screen(s, fixture, pages) for s in pages["screens"]}
    entry = pages["screens"][0]["id"]

    elements: dict = {}
    screen_refs: list[Ref] = []
    for screen_id, spec in screens.items():
        elements.update(spec["elements"])
        elements[spec["root"]]["visible"] = {"$state": f"{NAV_PATH}/current", "eq": screen_id}
        screen_refs.append(Ref(spec["root"]))

    shell = pages.get("shell")
    if shell:
        root = MODES[shell.get("mode", "侧边导航")](screen_refs, shell)
    else:
        root = vstack(*screen_refs, gap="lg")
    elements.update(to_elements(root, "app"))

    state: dict = {}
    for spec in screens.values():
        state.update(spec.get("state") or {})
    state["nav"] = {"current": entry, "context": {}}

    return {
        "schema_version": "tree/0.2",
        "entry": entry,
        "titles": {s["id"]: s["title"] for s in pages["screens"]},
        "spec": {"root": "app", "elements": elements, "state": state},
    }
