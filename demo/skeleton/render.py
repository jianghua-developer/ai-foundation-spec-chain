"""页面语义描述（+ 通用设计资产 + 示例数据）→ **结构骨架图**（单文件 HTML，零依赖）。

设计要点 —— 为什么它收敛而「真设计图」不收敛：

1. **版式是我们自己定死的**，不试图还原真实产品的版式 → 不需要布局引擎、不需要响应式
2. **一个语义件一个模板**，不拆成第三方原语 → 不需要补偿
3. **通用设计直接由 token 驱动**：既变成真实生效的 CSS 变量，也渲染成规格样张
4. 加一个新语义件 = 加一个模板函数；加一个新页面 = 加数据。**两者都不牵动别处**

它不是渲染器：它不承诺"这就是最终样子"，只承诺"这页有什么、怎么排、点了去哪、用什么设计"。
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

from . import style

ROOT = Path(__file__).resolve().parent.parent


def esc(v) -> str:
    return html.escape("" if v is None else str(v))


# ------------------------------------------------------------------ CSS

CSS = """
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--background); color: var(--foreground);
  font-family: var(--font-sans);
  font-size: var(--text-sm); line-height: var(--text-sm--line-height);
}
code { font-size: var(--text-xs); color: var(--muted-foreground); }
h1 { font-size: var(--text-2xl); font-weight: var(--font-weight-bold); margin: 0 0 calc(var(--spacing)*2); }
h2 { font-size: var(--text-lg); font-weight: var(--font-weight-semibold); margin: 0 0 calc(var(--spacing)*3); }
h3 { font-size: var(--text-base); font-weight: var(--font-weight-semibold); margin: 0 0 calc(var(--spacing)*2); }
p { margin: 0; }
.sk-doc { max-width: 1180px; margin: 0 auto; padding: calc(var(--spacing)*8) calc(var(--spacing)*6) calc(var(--spacing)*16); }
.sk-muted { color: var(--muted-foreground); }
.sk-doc > header { border-bottom: 2px solid var(--border); padding-bottom: calc(var(--spacing)*4); margin-bottom: calc(var(--spacing)*6); }
.sk-section { margin-bottom: calc(var(--spacing)*10); }
.sk-card { background: var(--card); color: var(--card-foreground); border: 1px solid var(--border); border-radius: var(--radius); padding: calc(var(--spacing)*5); }

/* 通用设计一览 */
.sk-row { display: flex; gap: calc(var(--spacing)*4); padding: calc(var(--spacing)*2) 0; border-top: 1px solid var(--border); }
.sk-rowlabel { flex: 0 0 64px; color: var(--muted-foreground); font-size: var(--text-xs); padding-top: 2px; }
.sk-typesample { margin-bottom: calc(var(--spacing)); }
.sk-swatches { display: flex; flex-wrap: wrap; gap: calc(var(--spacing)*2); }
.sk-swatch { display: flex; align-items: center; gap: calc(var(--spacing)); font-size: var(--text-xs); }
.sk-swatch i { width: 22px; height: 22px; border-radius: 4px; border: 1px solid var(--border); display: inline-block; }
.sk-swatch em { font-style: normal; }
.sk-bars { display: flex; flex-direction: column; gap: 4px; }
.sk-bar { display: flex; align-items: center; gap: calc(var(--spacing)*2); font-size: var(--text-xs); }
.sk-bar i { height: 10px; background: var(--primary); border-radius: 2px; display: inline-block; }
.sk-bar em { font-style: normal; color: var(--muted-foreground); }
.sk-radius { width: 48px; height: 32px; background: var(--secondary); border: 1px solid var(--border); display: inline-block; vertical-align: middle; }

/* 外壳 */
.sk-shell { display: flex; gap: calc(var(--spacing)*5); align-items: flex-start; }
.sk-side { flex: 0 0 200px; background: var(--secondary); border-radius: var(--radius); padding: calc(var(--spacing)*3); }
.sk-menu-group { margin-bottom: calc(var(--spacing)*3); }
.sk-menu-label { font-size: var(--text-xs); color: var(--muted-foreground); }
.sk-menu-item { padding: calc(var(--spacing)) calc(var(--spacing)*2); border-radius: calc(var(--radius) - 2px); font-size: var(--text-sm); }
.sk-menu-item.on { background: var(--primary); color: var(--primary-foreground); }
.sk-content { flex: 1; }

/* 屏与区块 */
.sk-screen { border: 1px dashed var(--border); border-radius: var(--radius); padding: calc(var(--spacing)*4); margin-bottom: calc(var(--spacing)*6); }
.sk-screenhead { display: flex; align-items: baseline; gap: calc(var(--spacing)*2); margin-bottom: calc(var(--spacing)*3); }
.sk-chip { display: inline-block; font-size: var(--text-xs); padding: 1px 6px; border-radius: 4px; background: var(--muted); color: var(--muted-foreground); }
.sk-block { border: 1px solid var(--border); border-left: 3px solid var(--primary); border-radius: calc(var(--radius) - 2px); padding: calc(var(--spacing)*3) calc(var(--spacing)*4); margin-bottom: calc(var(--spacing)*3); }
.sk-blockhead { display: flex; align-items: baseline; gap: calc(var(--spacing)*2); margin-bottom: calc(var(--spacing)*2); }
.sk-note { font-size: var(--text-xs); color: var(--muted-foreground); }

/* 数据表格 */
table.sk-table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
.sk-table th { text-align: left; font-weight: var(--font-weight-semibold); color: var(--muted-foreground); font-size: var(--text-xs); border-bottom: 1px solid var(--border); padding: calc(var(--spacing)) calc(var(--spacing)*2); }
.sk-table td { border-bottom: 1px solid var(--border); padding: calc(var(--spacing)*2); }

/* 语气（语义 → 视觉的唯一落点） */
.tone-中性, .tone-次操作 { background: var(--secondary); color: var(--secondary-foreground); }
.tone-提示, .tone-主操作 { background: var(--primary); color: var(--primary-foreground); }
.tone-警告 { background: var(--accent); color: var(--accent-foreground); }
.tone-危险, .tone-失败 { background: var(--destructive); color: var(--destructive-foreground); }
.tone-成功 { background: var(--secondary); color: var(--secondary-foreground); }
.sk-badge { display: inline-block; font-size: var(--text-xs); padding: 1px 8px; border-radius: 999px; }

/* 表单 / 控件占位 */
.sk-field { margin-bottom: calc(var(--spacing)*3); }
.sk-fieldlabel { font-size: var(--text-xs); color: var(--muted-foreground); margin-bottom: 2px; }
.sk-input { border: 1px solid var(--input); border-radius: calc(var(--radius) - 2px); padding: calc(var(--spacing)*2); color: var(--muted-foreground); background: var(--background); }
.sk-btn { display: inline-block; padding: calc(var(--spacing)*2) calc(var(--spacing)*4); border-radius: calc(var(--radius) - 2px); font-size: var(--text-sm); }
.sk-row-inline { display: flex; gap: calc(var(--spacing)*2); align-items: center; flex-wrap: wrap; }
.sk-callout { border-left: 3px solid var(--primary); padding: calc(var(--spacing)*2) calc(var(--spacing)*3); background: var(--muted); border-radius: calc(var(--radius) - 2px); }
.sk-kv { display: grid; grid-template-columns: 120px 1fr; gap: calc(var(--spacing)) calc(var(--spacing)*3); font-size: var(--text-sm); }
.sk-kv dt { color: var(--muted-foreground); font-size: var(--text-xs); }
.sk-kv dd { margin: 0; }
"""


# ------------------------------------------------------- 语义件 → HTML

def _runtime_value(ref: str, fixture: dict) -> str:
    """值的三种来源：样例数据直接显示；运行时值标注来源（静态图里没有真值）。"""
    if ref.startswith("submission."):
        return f'<span class="sk-chip">提交值 {esc(ref.split(".", 1)[1])}</span>'
    if ref.startswith("runtime."):
        return f'<span class="sk-chip">运行时 {esc(ref[len("runtime."):])}</span>'
    cur = fixture
    for part in ref.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return '<span class="sk-muted">—</span>'
    return esc(cur)


def _field(f: dict, fixture: dict) -> str:
    kind, label = f["type"], f["label"]
    req = ' <span style="color:var(--destructive)">*</span>' if f.get("required") else ""
    if kind == "只读文本":
        return (f'<div class="sk-field"><div class="sk-fieldlabel">{esc(label)}（只读）</div>'
                f'<div>{_runtime_value(f.get("value_from", ""), fixture)}</div></div>')
    if kind in ("长文本",):
        return (f'<div class="sk-field"><div class="sk-fieldlabel">{esc(label)}{req}</div>'
                f'<div class="sk-input" style="height:64px">{esc(f.get("placeholder", ""))}</div></div>')
    if kind == "日期区间":
        return (f'<div class="sk-field"><div class="sk-fieldlabel">{esc(label)}</div>'
                f'<div class="sk-row-inline"><span class="sk-input">开始 YYYY-MM-DD</span>'
                f'<span class="sk-input">结束 YYYY-MM-DD</span></div></div>')
    control = f'<span class="sk-input">选择…</span>' if kind in ("单选", "引用选择") else \
              f'<span class="sk-input">{esc(f.get("placeholder", "输入…"))}</span>'
    return (f'<div class="sk-field"><div class="sk-fieldlabel">{esc(label)}{req}</div>{control}</div>')


def _action(a: dict) -> str:
    return f'<span class="sk-btn tone-{esc(a["tone"])}">{esc(a["label"])}</span>'


def _action_note(a: dict) -> str:
    bits = []
    if a.get("op"):
        bits.append(f'[OP {esc(a["op"])}]')
    if a.get("goto"):
        bits.append(f'→ {esc(a["goto"])}')
    return " ".join(bits)


BLOCKS: dict[str, callable] = {}


def block(kind: str):
    def deco(fn):
        BLOCKS[kind] = fn
        return fn
    return deco


@block("页头")
def _b_header(b: dict, ctx) -> str:
    sub = f'<p class="sk-muted">{esc(b["description"])}</p>' if b.get("description") else ""
    return f'<h3>{esc(b["title"])}</h3>{sub}'


@block("筛选栏")
def _b_filter(b: dict, ctx) -> str:
    return '<div class="sk-row-inline">' + "".join(_field(f, ctx.fixture) for f in b["fields"]) + "</div>"


@block("数据表格")
def _b_table(b: dict, ctx) -> str:
    cols, rows = b["columns"], ctx.fixture.get(b["source"]["entity"], [])
    actions = b.get("row_actions", [])
    head = "".join(f"<th>{esc(c['label'])}</th>" for c in cols)
    head += "<th></th>" if actions else ""
    body = ""
    for row in rows:
        tds = ""
        for c in cols:
            raw = row.get(c["field"], "")
            if c["type"] == "状态":
                tone = (c.get("value_semantics") or {}).get(str(raw), "中性")
                tds += f'<td><span class="sk-badge tone-{esc(tone)}">{esc(raw)}</span></td>'
            else:
                tds += f"<td>{esc(raw)}</td>"
        if actions:
            cells = ""
            for a in actions:
                if not row.get(a.get("visible_when_rule", ""), True):
                    cells += f'<span class="sk-note">（{esc(a.get("visible_when_rule"))} 拦住）</span>'
                else:
                    label = a["label"]
                    note = f' <code>{esc(_action_note(a))}</code>' if a.get("goto") else ""
                    cells += f'<span class="sk-btn tone-次操作">{esc(label)}</span>{note}'
            tds += f'<td class="sk-row-inline">{cells}</td>'
        body += f"<tr>{tds}</tr>"
    note = f'<div class="sk-note">数据来源 OP {esc(b["source"]["op"])} · {esc(b["source"]["entity"])}</div>'
    return f'<table class="sk-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>{note}'


@block("表单")
def _b_form(b: dict, ctx) -> str:
    out = "".join(_field(f, ctx.fixture) for f in b["fields"])
    for a in b["actions"]:
        for rule in a.get("on_failure", []):
            out += (f'<div class="sk-callout tone-失败">失败：{esc(rule["feedback"])}'
                    f' <code>when {esc(rule["when"])} · 锚在 {esc(rule["target"])}</code></div>')
    row = " ".join(f'{_action(a)} <code>{esc(_action_note(a))}</code>' for a in b["actions"])
    return f'{out}<div class="sk-row-inline" style="margin-top:calc(var(--spacing)*2)">{row}</div>'


@block("结果提示")
def _b_result(b: dict, ctx) -> str:
    msg = f'<div class="sk-muted">{esc(b["description"])}</div>' if b.get("description") else ""
    return f'<div class="sk-callout tone-{esc(b["tone"])}"><strong>{esc(b["title"])}</strong>{msg}</div>'


@block("详情摘要")
def _b_summary(b: dict, ctx) -> str:
    items = "".join(
        f'<dt>{esc(i["label"])}</dt><dd>{_runtime_value(i["value_from"], ctx.fixture)}</dd>'
        for i in b["items"]
    )
    title = f'<h3>{esc(b["title"])}</h3>' if b.get("title") else ""
    return f'{title}<dl class="sk-kv">{items}</dl>'


@block("操作组")
def _b_actions(b: dict, ctx) -> str:
    return '<div class="sk-row-inline">' + " ".join(
        f'{_action(a)} <code>{esc(_action_note(a))}</code>' for a in b["actions"]
    ) + "</div>"


# ------------------------------------------------------------------ 组装

class Ctx:
    def __init__(self, fixture):
        self.fixture = fixture


def render_screen(screen: dict, ctx: Ctx) -> str:
    blocks = ""
    for b in screen["blocks"]:
        fn = BLOCKS.get(b["kind"])
        if fn is None:
            raise ValueError(f"没定义过这个语义件怎么画：{b['kind']!r}")
        blocks += (f'<div class="sk-block"><div class="sk-blockhead">'
                   f'<span class="sk-chip">{esc(b["kind"])}</span></div>{fn(b, ctx)}</div>')
    return (f'<section class="sk-screen" id="{esc(screen["id"])}">'
            f'<div class="sk-screenhead"><span class="sk-chip">{esc(screen["id"])}</span>'
            f'<strong>{esc(screen["title"])}</strong>'
            f'<span class="sk-chip">布局 · {esc(screen.get("layout", "—"))}</span></div>'
            f'{blocks}</section>')


def render_shell(shell: dict) -> str:
    groups = ""
    for g in shell["menus"]:
        items = "".join(
            f'<div class="sk-menu-item">{esc(i["label"])} <code>→{esc(i["goto"])}</code></div>'
            for i in g["items"]
        )
        groups += (f'<div class="sk-menu-group"><div class="sk-menu-label">{esc(g["label"])}</div>'
                   f'{items}</div>')
    side = f'<div class="sk-side"><div class="sk-menu-label">{esc(shell["title"])}</div>{groups}</div>'
    return (f'<section class="sk-section"><h2>外壳（跨屏常驻）</h2>'
            f'<div class="sk-shell">{side}'
            f'<div class="sk-card sk-content"><strong>内容区</strong>'
            f'<p class="sk-muted">各屏在这里切换 —— 外壳的 {esc(shell.get("mode"))} 是「模式」，不是「位置」。</p>'
            f'</div></div></section>')


def render_flows(pages: dict) -> str:
    rows = ""
    for s in pages["screens"]:
        for b in s["blocks"]:
            for a in b.get("actions", []):
                fail = "；".join(
                    f'{r["when"]} → {r["feedback"]}' for r in a.get("on_failure", [])
                ) or "—"
                rows += (f'<tr><td>{esc(s["id"])}</td><td>{esc(a["label"])}</td>'
                         f'<td>{esc(a.get("op", "—"))}</td>'
                         f'<td>{esc((a.get("on_success") or {}).get("goto", "—"))}</td>'
                         f'<td>{esc(fail)}</td></tr>')
            for a in b.get("row_actions", []):
                rows += (f'<tr><td>{esc(s["id"])}</td><td>{esc(a["label"])}（行内）</td>'
                         f'<td>{esc(a.get("op", "—"))}</td><td>{esc(a.get("goto", "—"))}</td>'
                         f'<td>{esc(a.get("visible_when_rule", "—"))}</td></tr>')
    return ('<section class="sk-section"><h2>交互与结果</h2>'
            '<p class="sk-muted">这张表就是 <code>CR5</code> 的 <code>OP → SCR</code> 边，与你怎么渲染无关。</p>'
            '<table class="sk-table"><thead><tr><th>屏</th><th>动作</th><th>OP</th>'
            f'<th>成功 →</th><th>失败</th></tr></thead><tbody>{rows}</tbody></table></section>')


def render_document(pages: dict, fixture: dict, tokens: dict) -> str:
    ctx = Ctx(fixture)
    shell = pages.get("shell")
    body = [
        style.design_sheet(tokens),
        render_shell(shell) if shell else "",
        '<section class="sk-section"><h2>页面</h2>'
        + "".join(render_screen(s, ctx) for s in pages["screens"]) + "</section>",
        render_flows(pages),
    ]
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(pages.get("scenario", "页面设计"))} · 结构骨架图</title>
<style>{style.css_variables(tokens)}{CSS}</style>
</head><body><div class="sk-doc">
<header><h1>{esc(pages.get("scenario", ""))} · 结构骨架图</h1>
<p class="sk-muted">语义规格 + 通用设计。<strong>不是最终样式还原</strong> —— 看结构、看设计规范、看跳转，不看像素。</p></header>
{"".join(body)}
</div></body></html>
"""


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    pages = style.load(Path(argv[1]))
    fixture = style.load(Path(argv[2]))
    tokens = style.load(Path(argv[3]))
    out = Path(argv[argv.index("-o") + 1]) if "-o" in argv else ROOT / "out" / "skeleton.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_document(pages, fixture, tokens), encoding="utf-8")
    print(f"{out}  ({len(pages['screens'])} 屏 / {len(pages['screens'][0]['blocks'])} 类区块/屏)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
