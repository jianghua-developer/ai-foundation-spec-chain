"""组件树的构造与校验。纯结构，不含任何业务语义。

这一层是「我们的映射层」与「第三方渲染器」之间的接缝：
输出 = json-render 的 Spec（扁平元素表 + root + 可选 state）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .catalog import CATALOG, TreeError, props_of


@dataclass
class Node:
    type: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list["Node"] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


def el(type_: str, *children: Node, visible=None, on=None, **props) -> Node:
    """构造组件树节点。props 一律用关键字传；缺失的由 build 阶段补 null。"""
    extra: dict[str, Any] = {}
    if visible is not None:
        extra["visible"] = visible
    if on is not None:
        extra["on"] = on
    return Node(type_, dict(props), list(children), extra)


def vstack(*children: Node, gap: str = "md", **props) -> Node:
    """纵向堆叠：**子元素一律撑满宽度**。

    为什么必须显式写：现成组件库的 `Stack` 把 `align` 默认成 `start`，
    于是子元素不撑满、`Grid(columns=N)` 拿不到容器宽度而按自身内容算等分列
    —— 表格会挤在左边、列宽由最宽内容决定。**这个默认值不符合"区块撑满页面"的语义意图**，
    所以映射层必须自带这一层语义默认值。
    """
    return el("Stack", *children, direction="vertical", gap=gap,
              align="stretch", justify=None, **props)


def hstack(*children: Node, gap: str = "md", align: str = "center",
           justify: str | None = None, **props) -> Node:
    """横向并排。横向时 `align` 管的是纵向对齐，居中通常才是想要的。"""
    return el("Stack", *children, direction="horizontal", gap=gap,
              align=align, justify=justify, **props)


@dataclass
class Ref:
    """引用一个**已经存在**的元素 key（不再产出新元素）。

    用于「外壳 + 屏」这种多段拼装：屏各自成树、各自分配 key；
    外壳里只要放一个引用，把它挂进内容区。
    """

    key: str


def _check(node) -> None:
    if isinstance(node, Ref):
        return
    """确定性校验：组件存在、props 名合法、事件名合法。"""
    if node.type not in CATALOG:
        raise TreeError(f"catalog 里没有组件 {node.type!r}")
    unknown = set(node.props) - set(props_of(node.type))
    if unknown:
        raise TreeError(f"{node.type} 不认识的 props: {sorted(unknown)}")
    for event in node.extra.get("on", {}):
        declared = CATALOG[node.type]["events"]
        if event not in declared:
            raise TreeError(f"{node.type} 没有事件 {event!r}（可用：{declared}）")
    for child in node.children:
        _check(child)


def _emit(node, key: str, out: dict[str, Any]) -> str:
    if isinstance(node, Ref):
        return node.key
    # catalog 的 props 是 nullable 而非 optional —— 缺的必须补 null，不能省略
    props = dict(node.props)
    for name in props_of(node.type):
        props.setdefault(name, None)
    element: dict[str, Any] = {"type": node.type, "props": props}
    element.update(node.extra)
    out[key] = element
    # 注意：schema 要求 children **必填**（TS 类型标的是可选，但校验器不认）
    element["children"] = [_emit(child, f"{key}.{i}", out) for i, child in enumerate(node.children)]
    return key


def to_elements(root: Node, root_key: str) -> dict[str, Any]:
    """子树 → 扁平元素表（挂到指定 key 前缀下）。供「外壳 + 屏」这种多段拼装用。"""
    _check(root)
    elements: dict[str, Any] = {}
    _emit(root, root_key, elements)
    return elements


def to_spec(root: Node, root_key: str, state: dict | None = None) -> dict:
    """组件树 → Spec。键按 DFS 前序确定性分配，同输入必同输出。"""
    elements = to_elements(root, root_key)
    spec: dict[str, Any] = {"root": root_key, "elements": elements}
    if state is not None:
        spec["state"] = state
    return spec
