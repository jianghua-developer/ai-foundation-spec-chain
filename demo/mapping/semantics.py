"""区块语义件 → 元素。

**视觉决策只集中在下面三张表里**，语义件本身不含颜色/尺寸/位置。
其余全是结构翻译：一个语义件展开成哪几个组件、子件挂在哪。
"""

from __future__ import annotations

from typing import Any

from . import actions
from .fields import control
from .tree import Node, el, hstack, vstack

# 语义语气 → 组件变体。这是「语义 → 视觉」的唯一落点。
BUTTON_TONE = {"主操作": "primary", "次操作": "secondary", "危险": "danger"}
BADGE_TONE = {"中性": "secondary", "提示": "outline", "警告": "default", "危险": "destructive"}
ALERT_TONE = {"成功": "success", "提示": "info", "警告": "warning", "失败": "error"}

CARD_BARE = {"title": None, "description": None, "maxWidth": None, "centered": None}


class Ctx:
    """映射上下文：本屏 id + 演示数据 + 状态命名空间 + 整份页面描述。"""

    def __init__(self, screen_id: str, fixture: dict, pages: dict | None = None):
        self.screen_id = screen_id
        self.fixture = fixture
        self.pages = pages or {"screens": []}
        self.ns = screen_id.lower()

    def submission_state_path(self, field_id: str) -> str | None:
        """`submission.F-TO` → 承载该字段的那一屏的表单状态路径。

        「用户在哪个屏填了这个字段」是页面之间的结构关系，映射层知道；
        语义件只声明「要显示提交上来的那个值」。
        """
        for screen in self.pages["screens"]:
            for block in screen["blocks"]:
                if block["kind"] != "表单":
                    continue
                if any(f["id"] == field_id for f in block["fields"]):
                    return f"/{screen['id'].lower()}/form/{field_id}"
        return None

    def state(self, *parts: str) -> str:
        return "/" + "/".join((self.ns, *parts))

    def resolve(self, ref: str) -> Any:
        cur: Any = self.fixture
        for part in ref.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur

    def options(self, ref: str) -> list[str]:
        """选项来源支持两种形态：`{"选项": [...]}` 或 `{"实体": [{"字段": ...}]}`。"""
        head, _, field = ref.partition(".")
        values = self.fixture.get(head)
        if not isinstance(values, list):
            return []
        if field:
            return [str(v.get(field, "")) for v in values if isinstance(v, dict)]
        return [str(v) for v in values]


# ---------------------------------------------------------------- 区块


def _page_header(block: dict, ctx: Ctx) -> list[Node]:
    out = [el("Heading", text=block["title"], level="h1")]
    if block.get("description"):
        out.append(el("Text", text=block["description"], variant="muted"))
    return out


def _filter_bar(block: dict, ctx: Ctx) -> list[Node]:
    controls = [
        control(f, state_path=ctx.state("filter", f["id"]), options=f.get("options"))
        for f in block["fields"]
    ]
    return [hstack(*controls)]


def _cell(column: dict, row: dict, ctx: Ctx) -> Node:
    raw = row.get(column["field"], "")
    if column["type"] == "状态":
        tone = (column.get("value_semantics") or {}).get(str(raw), "中性")
        return el("Badge", text=str(raw), variant=BADGE_TONE[tone])
    return el("Text", text=str(raw), variant="body")


def _data_table(block: dict, ctx: Ctx) -> list[Node]:
    columns = block["columns"]
    rows = ctx.resolve(block["source"]["entity"]) or []
    row_actions = block.get("row_actions", [])
    width = len(columns) + (1 if row_actions else 0)

    header = el("Grid",
                *[el("Text", text=c["label"], variant="caption") for c in columns],
                *([el("Text", text="", variant="caption")] if row_actions else []),
                columns=width, gap="md")

    def centered(cell: Node) -> Node:
        """单元格纵向居中。

        `Grid` 的单元格默认 stretch —— 行高由最高的格子（带按钮那格）决定，
        而 `Text` 是块级贴顶、`Badge` 是行内贴基线，两者都不居中，于是同一行里对不齐。
        catalog 没有「单元格对齐」这个 prop，只能在映射层包一层。
        """
        return hstack(cell, gap="none", align="center")

    body: list[Node] = []
    for row in rows:
        cells = [centered(_cell(c, row, ctx)) for c in columns]
        for act in row_actions:
            # 规则 R# 的判定结果由数据给出；映射层只负责「按结果给不给这个按钮」
            allowed = bool(row.get(act.get("visible_when_rule", ""), True))
            # 行内操作靠右：`Grid` 是**等分列**，按钮会拉满整格；
            # 用 hstack(justify=end) 把它推回右侧并按内容收窄 —— 映射层对 catalog 默认值的补偿
            cells.append(hstack(
                el("Button", label=act["label"], variant="secondary", disabled=None,
                   visible=allowed,
                   on={"press": actions.row_action(act, row)}),
                gap="none", justify="end",
            ))
        body.append(el("Grid", *cells, columns=width, gap="md"))

    return [el("Card", vstack(header, el("Separator", orientation="horizontal"), *body, gap="sm"),
               **CARD_BARE)]


def _failures_for(block: dict, field_id: str) -> list[dict]:
    """挂在某个字段上的失败分支：动作里声明、按 target 锚到字段。"""
    return [
        rule
        for action in block.get("actions", [])
        for rule in action.get("on_failure", [])
        if rule.get("target") == field_id
    ]


def _action_row(items: list[dict], ctx: Ctx) -> Node:
    buttons = []
    for a in items:
        buttons.append(el("Button", label=a["label"], variant=BUTTON_TONE[a["tone"]],
                          disabled=None,
                          on={"press": actions.spec_action_binding(a, ctx.screen_id)}))
    return hstack(*buttons)


def _form(block: dict, ctx: Ctx) -> list[Node]:
    children: list[Node] = []
    for f in block["fields"]:
        options = ctx.options(f["options_from"]) if f.get("options_from") else f.get("options")
        value = ctx.resolve(f["value_from"]) if f.get("value_from") else None
        children.append(control(f, state_path=ctx.state("form", f["id"]),
                                options=options, value=value))
        # 失败反馈**声明在树里**、锚在目标字段旁；宿主只写规则号
        for rule in _failures_for(block, f["id"]):
            children.append(el("Alert", title=rule["feedback"], message=None, type="error",
                               visible=actions.failure_visible(ctx.screen_id, rule["when"])))
    children.append(_action_row(block["actions"], ctx))
    return [vstack(*children, gap="lg")]


def _result(block: dict, ctx: Ctx) -> list[Node]:
    return [el("Alert", title=block["title"], message=block.get("description"),
               type=ALERT_TONE.get(block["tone"], "info"))]


def _summary_value(ref: str, ctx: Ctx):
    """摘要值的三种来源：

    - `runtime./a/b`      → 运行时读 state（如"上一屏选中的那个人"）
    - `submission.F-X`    → 运行时读**承载该字段那一屏**的表单状态
    - 其它                → 映射期从样例数据取字面量
    """
    if ref.startswith("runtime."):
        # 点号写法 → JSON Pointer：runtime.nav.context.person → /nav/context/person
        return {"$state": "/" + ref[len("runtime."):].strip("/").replace(".", "/")}
    if ref.startswith("submission."):
        path = ctx.submission_state_path(ref.split(".", 1)[1])
        return {"$state": path} if path else ""
    value = ctx.resolve(ref)
    return "" if value is None else str(value)


def _summary(block: dict, ctx: Ctx) -> list[Node]:
    rows = []
    for item in block["items"]:
        rows.append(el("Grid",
                       el("Text", text=item["label"], variant="caption"),
                       el("Text", text=_summary_value(item["value_from"], ctx), variant="body"),
                       columns=2, gap="md"))
    parts: list[Node] = []
    if block.get("title"):
        parts.append(el("Heading", text=block["title"], level="h3"))
    parts.extend(rows)
    return [vstack(*parts, gap="sm")]


def _action_group(block: dict, ctx: Ctx) -> list[Node]:
    return [_action_row(block["actions"], ctx)]


BLOCKS = {
    "页头": _page_header,
    "筛选栏": _filter_bar,
    "数据表格": _data_table,
    "表单": _form,
    "结果提示": _result,
    "详情摘要": _summary,
    "操作组": _action_group,
}
