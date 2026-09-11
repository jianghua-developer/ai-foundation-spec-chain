# 页面渲染方案 · 调研存档

- 日期：**2026-09-11**
- 用途：[DESIGN](../DESIGN.md) §1.8（页面设计的形态）的依据。**只记事实与出处，不记结论。**
- ⚠️ **方法学限制**：本轮多域名 WebFetch 被环境阻断（`a2ui.org`、`designtokens.org`、`github.com` 等），结论来自**搜索摘要**（搜索引擎又做了一层摘要）。**关键结论多源交叉，细节请自行复核**。个别项目名/版本号来自第三方聚合站，可信度低于许可证类多源一致的结论。

---

## 1. Figma MCP

**已从只读变读写**（2026-03-24 起）。工具分 Read / Write 两组。

| 组 | 工具（节选） |
|---|---|
| Read | `get_design_context`（默认输出 React+Tailwind）、`get_metadata`（sparse XML）、`get_screenshot`、`get_variable_defs`、`download_assets`、`get_code_connect_map`、`whoami` |
| **Write** | **`use_figma`**（通用创建/编辑）、`generate_figma_design`（从 HTML 生成图层）、`create_new_file`、`upload_assets`、`generate_diagram` |

- **`use_figma` / `generate_figma_design` 只在远程 server 提供**；本地 desktop server 无。
- **三条硬门槛**：
  1. **Full seat** 才能写（Dev seat 只读）
  2. **客户端必须在 Figma MCP Catalog 白名单内**，否则需 join waitlist
  3. **beta 品质**："may need manual review and cleanup"；**20kb 输出上限/次**；**不支持图片与自定义字体**
- **官方定位与设计系统绑定**：「Design system detection isn't automatic… Left to its own defaults, the agent **hardcodes values**: colors, spacing, typography.」——它会硬编视觉值。
- **REST API 几乎不能写**：file endpoints 全是 GET；变量写入仅 **Enterprise** 且只覆盖 tokens。
- **Plugin API** 是唯一真正的画布写通道，但必须在 Figma 客户端进程内执行 → 所有第三方写 MCP 都要"插件 + 桥"。
- `.fig` 格式闭源未公开，已被逆向（`figmatojson`），理论上可离线生成再导入——**仅适合实验**。

出处：[Tools and prompts](https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/) · [Write to canvas](https://developers.figma.com/docs/figma-mcp-server/write-to-canvas/) · [Rate limits & access](https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/) · [MCP vs agent](https://developers.figma.com/docs/figma-mcp-server/mcp-vs-agent/) · [REST file endpoints](https://developers.figma.com/docs/rest-api/file-endpoints/) · [Bitovi 实测](https://www.bitovi.com/blog/figma-just-opened-the-canvas-to-agents.-heres-what-actually-happens)

---

## 2. DTCG（Design Tokens）

**不是 W3C 标准。** 规范自述原文：

> "This specification was published by the Design Tokens Community Group. **It is not a W3C Standard nor is it on the W3C Standards Track.**"

- 法律地位：**W3C 社区组（Community Group）的 CG-FINAL 报告**，受 FSA 治理，含 RF 承诺 → 实现与商用无障碍。
- 首个稳定版 **2025.10**（2025-10-28），也称 version 1；三模块：Format / Color / Resolver。
- **采用梯度（"宣布支持" ≠ "生产可用"）**：

| 工具 | 程度 |
|---|---|
| **Terrazzo** | 生产可用（2.0.0 stable 专门对齐 DTCG） · **MIT** |
| Penpot | 原生集成 · MPL-2.0（文件级 copyleft，不传染） |
| Style Dictionary | 生产可用，但 2025.10 全量支持**仍在推进**（v5） · Apache-2.0 |
| Tokens Studio | 生产可用，自有格式早于 DTCG · 插件 MIT |
| **Figma** | **渐进推出、未完成**——截至 2026-08 **不覆盖 composite tokens**，颜色叠加会**烘焙成字面量** |

- **无竞争格式**（Theo / SD v3 自有格式均已迁移）。分裂点在 **composite tokens**（typography / shadow / gradient）。
- **DTCG 只定义 token 的语义，完全不定义布局 / 页面结构 / 组件结构。**

出处：[DTCG 2025.10 Format](https://www.designtokens.org/TR/2025.10/format/) · [DTCG FAQ](https://www.designtokens.org/faq/) · [Terrazzo](https://github.com/terrazzoapp/terrazzo) · [Style Dictionary](https://github.com/style-dictionary/style-dictionary)

---

## 3. 「DTCG → 真设计图」的现成方案：**没有**

生态输出端只有两类：**平台代码**（CSS / Swift / XML）与 **token 展示**（色卡 / 编辑器 / 样式指南）。**没有"页面"。** 原因是规范层面的——DTCG 里根本没有布局/页面这块。

最接近的两个（均**不建议依赖**）：

- **Umbono**（极新 v0.3.0，单一来源，低置信）——架构思路与"agent 出语义 / 引擎独占视觉 / 确定性渲染"高度重合，原文：
  > "The scene.json format admits **no visual decisions at all** — no coordinates, colors, or routing hints… the engine renders **deterministically (same input, same bytes)**."
  但输入是自有 schema、面向流程图/架构图，**不是 UI**。
- **Handoff**（MIT，真实存在）——渲染"活的组件 + token 预览"，但产出是**文档站**不是设计图，且 beta。

出处：[Umbono](https://www.npmjs.com/package/umbono) · [Handoff](https://github.com/Convertiv/handoff-app)

---

## 4. A2UI（Google）

**协议，不是组件库，也不是托管服务。**

- 官方原则原文：
  > "**Agents send data, clients execute code.**"
  > "Agents can only use **pre-approved components from a client-defined catalog**, preventing UI injection attacks. **All JSON is schema-validated.**"
  > "**Flat, streaming JSON structure** designed for easy incremental generation."
- **能 / 不能**：

| 「完整应用」指 | 能？ |
|---|---|
| 界面蓝图（组件树 + 数据绑定） | ✅ |
| 视觉样式 | ❌ renderer 决定 |
| 业务逻辑 | ❌ 在 agent / 后端 |
| 数据来源与存储 | ❌（只能填 dataModel） |
| 可运行应用 | ❌ **无渲染引擎，只是 spec** |

- **样式策略（关键）**：renderer-controlled styling——
  > "agents describe **what** to show (via semantic hints like **`usageHint: 'h1'`**), while catalogs interpret theming and **renderers decide how it looks**… themed via **CSS variables**."
- **catalog 工作流**：客户端定义 catalog（JSON Schema）→ 注册实现 → 用 `supportedCatalogIds` 告知 agent → agent 在 `createSurface` 里带 `catalogId` → 用词表内的组件名发消息。
- **wire 操作**：`createSurface` / `updateComponents` / `updateDataModel`（JSON Pointer 绑定）。
- **LLM-agnostic**：`genui_x` 有 anthropic / openai / gemini / ollama 四个 factory；`ai-kit-a2ui-core` 有 Anthropic + OpenAI adapter；A2UI Vue 用 `LLM_PROVIDER` 切 provider。
- **传输**：A2A ✅ / AG-UI ✅ / REST ✅ / WebSocket ✅ / **MCP ✅**；SSE 提案中（GitHub 快照与 a2ui.org roadmap **状态标注不一致**）。
- **Agent 框架集成**：A2A ✅ / AG-UI ✅ / AG2 ✅ / CopilotKit ✅；ADK 🚧；**Claude Agent SDK 等为 💡 Proposed（社区兴趣）**。
- **没有官方托管端点**——官方 quickstart 是**本地跑**（A2A agent :10002 + 前端 :5173），且用 `GEMINI_API_KEY`。在线可试的只有 **A2UI Composer**（`a2ui-composer.ag-ui.com`）与社区 playground。
- 版本线：v0.8 stable / v0.9 draft，多源说法不一，**活跃演进中**。

出处：[a2ui.org](https://a2ui.org/) · [Defining Your Own Catalog](https://a2ui.org/guides/defining-your-own-catalog/) · [Glossary](https://a2ui.org/concepts/glossary/) · [Theming & Styling](https://raw.githubusercontent.com/a2ui-project/a2ui/main/docs/public/guides/theming.md) · [Roadmap](https://a2ui.org/roadmap/) · [Transports](https://github.com/a2ui-project/a2ui/blob/6a82313a/docs/concepts/transports.md) · [Quickstart](https://github.com/a2ui-project/a2ui/blob/81783227/docs/quickstart.md) · [生态对比](https://a2ui.org/introduction/agent-ui-ecosystem/)

---

## 5. CopilotKit 与 AG-UI

- **CopilotKit** = 西雅图创业公司（2023），$27M A 轮（2026-05）；产品是"agent 与用户之间的横向层"，三层栈（Frontend SDK → Runtime → Agent），支持 React/Angular/Vue/RN + Slack/Teams。有 **Enterprise Intelligence** 商业档位。
- **AG-UI = CopilotKit 造的传输协议**，已被 Google / LangChain / AWS / Microsoft / Mastra / PydanticAI / Agno 采用。
- **AG-UI ≠ A2UI**（关键区分）：
  > **AG-UI = "the pipe"**（传输/运行时层）／ **A2UI = "the content"**（声明式生成式 UI 格式）
- **协议栈**：MCP（agent↔工具）· A2A（agent↔agent）· AG-UI（agent↔**用户**）· A2UI（内容格式）。
- CopilotKit 的能力面含 **Human-in-the-Loop**（agent 暂停、请求用户输入/确认后继续）、Shared State、Generative UI。
- ⚠️ **许可证在不同来源间冲突**（MIT vs Apache-2.0），需自行核对 LICENSE。

出处：[CopilotKit](https://github.com/CopilotKit/CopilotKit) · [AG-UI and A2UI Explained](https://www.copilotkit.ai/blog/ag-ui-and-a2ui-explained-how-the-emerging-agentic-stack-fits-together) · [State of Agentic UI](https://www.copilotkit.ai/blog/the-state-of-agentic-ui-comparing-ag-ui-mcp-ui-and-a2ui-protocols) · [TechCrunch](https://techcrunch.com/2026/05/05/copilotkit-raises-27m-to-help-devs-deploy-app-native-ai-agents/)

---

## 6. 「结构化描述 → UI 渲染」的开源候选

**最强的否定结论：没有任何开源渲染器能直接接受高层语义（数据表格 / 表单 / 统计块粒度）输入。**

| 候选 | 许可 | 输入 | 覆盖 | 备注 |
|---|---|---|---|---|
| **amis**（百度） | Apache-2.0 | 自有 DSL（组件实例级） | **最全**：CRUD 表格（排序/分页/筛选）+ 表单 + 卡片 + 列表 + 图表 | `amis.embed()` 可无头；**DSL 不禁止视觉属性**；换肤不彻底；详情/统计块未获一手确认 |
| **json-render**（Vercel Labs，2026-01） | Apache-2.0 | **你定义的 catalog** + 元素树 | 自带 36 个 shadcn 组件（低层件） | 四件套 Schema/Catalog/Registry/Spec；含 `actions` 声明位；渐进渲染（JSONL + JSON Patch） |
| **A2UI** | Apache-2.0 | 同上（catalog 机制） | basic catalog 仅原语 | 见 §4 |
| RJSF | Apache-2.0 | JSON Schema + uiSchema | **仅表单** | `@rjsf/shadcn` 吃 CSS 变量 |
| JSON Forms | MIT | JSON Schema + UI Schema | **仅表单** | 架构上**视觉与结构分离最干净**；无纯 vanilla 绑定 |
| LowCodeEngine | MIT | 编辑器 schema | — | **DSL 天然把视觉属性烘进去** |
| GrapesJS | BSD-3 | HTML/CSS 画布 | 建站 | headless 有确定性缺陷 |
| Puck | MIT（核心） | 你自己的组件 props 树 | **无内置语义** | 可作宿主骨架 |
| Form.io | ⚠️ 核心 OSL-3.0 | — | — | **Pro/Premium 组件仅企业订阅** |

**组件库候选**（作渲染器实现层）：

| 库 | 主题能力 |
|---|---|
| **antd 5** | Design Token 三层（seed/map/alias）+ ConfigProvider，最深 |
| **shadcn/ui** | 组件直接吃 **CSS 变量** → DTCG 转 CSS 变量后**零映射直灌**；MIT 但是拷贝源码 |
| naive-ui | theme overrides + CSS 变量（Vue） |

**许可证雷区**：Form.io（OSL-3.0 + 商业档位）· Thesys C1（完全闭源）· Puck Cloud / CopilotKit Enterprise（商业档位）。本清单内主流是 MIT / Apache-2.0，**未遇到 AGPL**。

出处：[amis](https://github.com/baidu/amis) · [amis CRUD](https://baidu.github.io/amis/zh-CN/components/crud) · [json-render](https://github.com/vercel-labs/json-render) · [RJSF](https://github.com/rjsf-team/react-jsonschema-form) · [JSON Forms](https://jsonforms.io/docs/architecture/) · [Puck](https://puckeditor.com/)

---

## 7. 未查到的项（明确记录）

- 官方对 Figma file JSON schema 的**稳定版本承诺**——无（README 明写 beta）。
- MCP Catalog waitlist 的处理周期/通过率——无公开资料。
- 任何官方的「Figma → 结构化规格（非代码）」导出——不存在。
- amis 是否有官方 `detail`（详情）/`statistic`（统计）组件——**未读到一手文档页**。
- Umbono 的独立验证——单一来源，低置信。
- A2UI 传输状态在 GitHub 快照与官网 roadmap 间**标注不一致**。
