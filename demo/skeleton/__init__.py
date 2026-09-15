"""语义规格 → **结构骨架图**（单文件 HTML，零依赖）。

与 `mapping/` 的分工：两者消费同一份输入（语义描述 + token + 示例数据），
- `mapping/` → json-render Spec → React 渲染：验证过形态，但**补偿不收敛**
- `skeleton/` → 结构骨架图：**收敛**，是主产物
"""

from .render import render_document

__all__ = ["render_document"]
