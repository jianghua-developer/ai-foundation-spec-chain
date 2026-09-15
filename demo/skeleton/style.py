"""通用设计资产（DTCG）→ CSS 变量 + **通用设计一览**。

骨架图不是线框：它要**体现通用设计**（导航布局 / 字体字号 / 颜色风格 / 间距 / 圆角）。
做法是——token 既变成真实生效的 CSS 变量，也在页面顶部渲染成一份**规格样张**。

复用 `tokens/dtcg_to_css.py` 的 `to_vars()`：token → 变量名只有一处定义。
"""

from __future__ import annotations

import html
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("dtcg", ROOT / "tokens" / "dtcg_to_css.py")
dtcg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dtcg)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def css_variables(tokens: dict) -> str:
    """token → `:root { --x: … }`（含 @theme 那批静态尺度）。"""
    theme, root = dtcg.to_vars(tokens)
    lines = ["  " + f"{k}: {v};" for k, v in {**theme, **root}.items()]
    return ":root {\n" + "\n".join(lines) + "\n}\n"


# ------------------------------------------------------- 通用设计一览

def _leaves(tokens: dict, group: str) -> list[tuple[str, object]]:
    node = tokens.get(group, {})
    return [(k, v.get("$value")) for k, v in node.items() if isinstance(v, dict) and "$value" in v]


def _px(value) -> str:
    if isinstance(value, dict):
        return f"{value['value']}{value['unit']}"
    return str(value)


def design_sheet(tokens: dict) -> str:
    """通用设计一览：字体 / 字号阶梯 / 配色 / 间距基准 / 圆角。"""
    fam = ", ".join(_leaves(tokens, "font")[0][1]) if _leaves(tokens, "font") else "sans-serif"
    parts = [f'<section class="sk-design"><h2>通用设计一览</h2>',
             f'<p class="sk-muted">来自 token 源（DTCG），换一份 token 这里与全图一起变。</p>']

    # 字体族
    parts.append(
        '<div class="sk-row"><div class="sk-rowlabel">字体</div>'
        f'<div style="font-family:{html.escape(fam)}">中文样式样张 Aa Bb 123 —— {html.escape(fam)}</div></div>'
    )

    # 字号阶梯
    sizes = _leaves(tokens, "text")
    scale = "".join(
        f'<div class="sk-typesample" style="font-size:var(--text-{k})">'
        f'<span class="sk-muted">{html.escape(k)} · {_px(v.get("fontSize"))}</span> '
        f'换班申请入口 Shift Board</div>'
        for k, v in sizes
    )
    parts.append(f'<div class="sk-row"><div class="sk-rowlabel">字号</div><div>{scale}</div></div>')

    # 配色
    swatches = "".join(
        f'<span class="sk-swatch"><i style="background:var(--{k})"></i>'
        f'<em>{html.escape(k)}</em><code>{html.escape(str(v))}</code></span>'
        for k, v in _leaves(tokens, "color")
    )
    parts.append(f'<div class="sk-row"><div class="sk-rowlabel">配色</div><div class="sk-swatches">{swatches}</div></div>')

    # 间距基准（组件间距 = 基准 × 倍数）
    base = _leaves(tokens, "space")
    if base:
        _, bv = base[0]
        bars = "".join(
            f'<span class="sk-bar"><i style="width:calc(var(--spacing) * {n})"></i>'
            f'<em>{n}× = {n}·{_px(bv)}</em></span>'
            for n in (1, 2, 3, 4, 6, 8)
        )
        parts.append(f'<div class="sk-row"><div class="sk-rowlabel">间距</div><div class="sk-bars">{bars}</div></div>')

    # 圆角
    r = _leaves(tokens, "radius")
    if r:
        parts.append(
            f'<div class="sk-row"><div class="sk-rowlabel">圆角</div>'
            f'<div><span class="sk-radius" style="border-radius:var(--radius)"></span>'
            f'<span class="sk-muted"> {_px(r[0][1])}</span></div></div>'
        )

    parts.append("</section>")
    return "\n".join(parts)
