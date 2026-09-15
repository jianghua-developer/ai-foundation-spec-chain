"""字段类型 → 控件。

进来的是**语义类型**（引用选择 / 长文本 / 只读文本…），出去的是**控件**。
这里没有任何颜色、尺寸、位置的判断——视觉由渲染器 + token 决定。
"""

from __future__ import annotations

from typing import Any

from .tree import Node, el, hstack, vstack

# 字段语义类型 → 控件。每条规则只表达「这个语义用什么控件承载」。
_TEXTUAL = {"文本": "text", "数字": "number", "日期": "text"}  # catalog 无 date 类型，降级为文本


def _checks(field: dict) -> list[dict] | None:
    label = field["label"]
    rules = []
    if field.get("required"):
        rules.append({"type": "required", "message": f"{label}不能为空"})
    if field.get("max_length"):
        rules.append(
            {
                "type": "maxLength",
                "message": f"{label}最多 {field['max_length']} 字",
                "args": {"max": field["max_length"]},
            }
        )
    return rules or None


def control(field: dict, *, state_path: str, options: list[str] | None = None,
            value: Any = None) -> Node:
    """一个字段 → 一个（或一组）控件。"""
    kind = field["type"]
    label = field["label"]
    name = field["id"]
    placeholder = field.get("placeholder")
    checks = _checks(field)

    if kind == "只读文本":
        return vstack(
            el("Text", text=label, variant="caption"),
            el("Text", text="" if value is None else str(value), variant="body"),
            gap="sm",
        )

    if kind == "长文本":
        return el("Textarea", label=label, name=name, placeholder=placeholder,
                  rows=4, checks=checks, value={"$bindState": state_path})

    if kind == "引用选择" or kind == "单选":
        return el("Select", label=label, name=name, options=options or [],
                  placeholder=placeholder, checks=checks,
                  value={"$bindState": state_path})

    if kind == "开关":
        return el("Switch", label=label, name=name, checks=checks,
                  checked={"$bindState": state_path})

    if kind == "日期区间":
        # 一个语义件 → 两个控件。区间是语义，两个输入框是承载方式。
        return vstack(
            el("Text", text=label, variant="caption"),
            hstack(
                el("Input", label="开始", name=f"{name}.from", type="text",
                   placeholder="YYYY-MM-DD", checks=None, value=None),
                el("Input", label="结束", name=f"{name}.to", type="text",
                   placeholder="YYYY-MM-DD", checks=None, value=None),
            ),
            gap="sm",
        )

    if kind in _TEXTUAL:
        return el("Input", label=label, name=name, type=_TEXTUAL[kind],
                  placeholder=placeholder, checks=checks,
                  value={"$bindState": state_path})

    raise ValueError(f"未定义的字段类型：{kind!r}")
