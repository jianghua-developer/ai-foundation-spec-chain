# demo —— 探针（**项目已停止**，2026-09-15）

> 本目录是 [DESIGN §1.8](../docs/DESIGN.md) 形态验证的**探针**，不是产品代码。
> 所属项目**已停止**，理由见 [`docs/EVALUATION.md`](../docs/EVALUATION.md)。
> 保留它是因为**结论可复现**——不是因为它还有用。

## 还剩什么

| 目录 | 是什么 | 还能跑吗 |
|---|---|---|
| `skeleton/` | 结构骨架图生成器（语义描述 + token + 数据 → 单文件 HTML） | ✅ **纯 Python，零依赖** |
| `tokens/` | DTCG 源 + 转换器（→ Tailwind 主题变量 / CSS 变量） | ✅ 纯 Python |
| `spec/` | 页面语义描述（6 屏 / 3 模块 / 侧边导航外壳）+ 演示数据 | 数据，非可执行 |
| `mapping/` | 映射层：语义件 → json-render 组件树 | ⚠️ 能产出组件树，但**渲染器已删**（见下） |
| `out/` | 产物：`skeleton.html`、`shiftboard.tree.json` | — |
| `REPORT.md` | 渲染链路的实测报告（14 个问题 / 7 条永久税） | 文档 |

## 跑

```bash
cd demo

# 结构骨架图（唯一还完整的链路）—— 产出 out/skeleton.html，双击即开
python3 -m skeleton spec/shiftboard.pages.json spec/shiftboard.fixture.json tokens/tokens.dtcg.json -o out/skeleton.html

# 映射层 —— 只到"组件树"为止，没有再往下的渲染器
python3 -m mapping spec/shiftboard.pages.json spec/shiftboard.fixture.json -o out/shiftboard.tree.json

# token 通路
python3 tokens/dtcg_to_css.py tokens/tokens.dtcg.json /tmp/theme.css --dark tokens/tokens.dark.dtcg.json
```

## 已删除的部分（2026-09-15 收尾时清理）

**React 前端栈**：`node_modules/`（171 个包 / 155 MB）、`src/`、`index.html`、`vite.config.mjs`、`package*.json`、`dist/`、`tools/*.mjs`、`out/shots/`。

它们是用来验证"spec → 真设计图"这条路的。**道路结论：能跑，但代价不收敛**（详见 [`REPORT.md`](REPORT.md) 与 `EVALUATION.md` §5.1）。删掉后：

- `mapping/` 仍能产出组件树（纯 Python + `catalog.snapshot.json`），**但没人能渲染它了**
- 端到端驱动与组件树校验脚本随栈一起删除——**它们的结论已记入 `EVALUATION.md` §5.1 / §5.3**

`catalog.snapshot.json` 保留：它是当时那份 shadcn 组件目录（36 个原语）的快照，`mapping/` 读它。
