"""DTCG → Tailwind v4 主题变量。

DESIGN §1.8 定「转换用 Terrazzo（MIT）或等价工具」。本 demo 用这个等价小工具，
**只为验证 token 通路**；正式实现应换 Terrazzo（见 REPORT 的偏离说明）。

输出分两块，依据是「能不能被主题变体覆盖」：

| 去向 | 内容 | 为什么 |
|---|---|---|
| `@theme { }` | 静态设计尺度（间距 / 字体 / 字重 / 字号 / 圆角） | 不随明暗切换，是"这套设计长什么样" |
| `:root { }` | 语义色 | 要能被 `prefers-color-scheme` 覆盖 |

命名规则 = token 路径 → Tailwind 的主题变量名（**这就是 token 源与组件库之间唯一的耦合点**）：

    color.primary-foreground  → --primary-foreground   （语义色，shadcn 契约）
    space.base                → --spacing              （间距基准，Tailwind 契约）
    font.sans                 → --font-sans
    weight.medium             → --font-weight-medium
    text.sm                   → --text-sm  +  --text-sm--line-height
    radius.base               → --radius
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 哪些顶层组进 :root（可被主题变体覆盖），其余进 @theme
ROOT_GROUPS = {"color"}


# ------------------------------------------------------------------ 取值

def _index(dtcg: dict) -> dict[tuple, dict]:
    """建立 path → 节点 的索引，供 DTCG 别名 `{a.b}` 解析。"""
    out: dict[tuple, dict] = {}

    def walk(node: dict, path: tuple):
        if "$value" in node:
            out[path] = node
            return
        for key, child in node.items():
            if key.startswith("$") or not isinstance(child, dict):
                continue
            walk(child, (*path, key))

    walk(dtcg, ())
    return out


def _resolve(value, index: dict):
    """解析 DTCG 别名：`"{font.sans}"` → 被引用 token 的值。"""
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        target = tuple(value[1:-1].split("."))
        if target not in index:
            raise ValueError(f"别名指不到：{value}")
        return index[target]["$value"]
    return value


def _color(value, index) -> str:
    value = _resolve(value, index)
    if isinstance(value, str):
        return value
    if "hex" in value:
        return value["hex"]
    parts = " ".join(str(c) for c in value["components"])
    return f"color({value.get('colorSpace', 'srgb')} {parts} / {value.get('alpha', 1)})"


def _dimension(value, index) -> str:
    value = _resolve(value, index)
    if isinstance(value, str):
        return value
    return f"{value['value']}{value['unit']}"


def _font_family(value, index) -> str:
    value = _resolve(value, index)
    if isinstance(value, str):
        return value
    return ", ".join(f'"{f}"' if " " in f else f for f in value)


# ------------------------------------------------- 组 → 变量名与取值规则

def _names(path: tuple) -> list[tuple[str, str | None]]:
    """token 路径 → [(变量名, 复合类型取哪一部分)]。非复合类型第二部分为 None。"""
    group, rest = path[0], "-".join(path[1:])
    if group == "color":
        return [(f"--{rest}", None)]
    if group in ("radius", "space"):
        prefix = {"radius": "--radius", "space": "--spacing"}[group]
        return [(prefix, None)] if rest == "base" else [(f"{prefix}-{rest}", None)]
    if group == "font":
        return [(f"--font-{rest}", None)]
    if group == "weight":
        return [(f"--font-weight-{rest}", None)]
    if group == "text":                       # typography 复合 → 拆成字号 + 行高
        return [(f"--text-{rest}", "font-size"), (f"--text-{rest}--line-height", "line-height")]
    raise ValueError(f"没定义过怎么映射这一组：{group!r}")


def _serialize(type_: str, value, part: str | None, index: dict) -> str:
    if type_ == "color":
        return _color(value, index)
    if type_ == "dimension":
        return _dimension(value, index)
    if type_ == "fontFamily":
        return _font_family(value, index)
    if type_ == "fontWeight":
        return str(value)
    if type_ == "typography":
        _resolve(value, index)                # 只为触发别名校验
        return _dimension(value["fontSize"], index) if part == "font-size" else str(value["lineHeight"])
    raise ValueError(f"不认识的 DTCG 类型：{type_!r}")


def to_vars(dtcg: dict) -> tuple[dict[str, str], dict[str, str]]:
    """→ (theme 变量, root 变量)。"""
    index = _index(dtcg)
    theme: dict[str, str] = {}
    root: dict[str, str] = {}

    def walk(node: dict, path: tuple, inherited_type: str | None):
        type_ = node.get("$type", inherited_type)
        if "$value" in node:
            bucket = root if path[0] in ROOT_GROUPS else theme
            for name, part in _names(path):
                bucket[name] = _serialize(type_, node["$value"], part, index)
            return
        for key, child in node.items():
            if key.startswith("$") or not isinstance(child, dict):
                continue
            walk(child, (*path, key), type_)

    walk(dtcg, (), None)
    return theme, root


# ------------------------------------------------------------------ 输出

def _block(selector: str, variables: dict[str, str]) -> str:
    body = "\n".join(f"  {k}: {v};" for k, v in variables.items())
    return f"{selector} {{\n{body}\n}}\n"


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    light = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    theme, root = to_vars(light)
    parts = [
        "/* 由 tokens/dtcg_to_css.py 从 DTCG 生成 —— 不要手改。 */\n",
        "/* 静态设计尺度：间距基准 / 字体 / 字重 / 字号阶梯 / 圆角 */\n",
        _block("@theme", theme),
        "/* 语义色：可被主题变体覆盖 */\n",
        _block(":root", root),
    ]
    if "--dark" in argv:
        dark = json.loads(Path(argv[argv.index("--dark") + 1]).read_text(encoding="utf-8"))
        _, dark_root = to_vars(dark)
        parts.append(_block("@media (prefers-color-scheme: dark)\n:root", dark_root))
    out_path = Path(argv[2])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"{out_path}  (@theme {len(theme)} + :root {len(root)} 个变量)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
