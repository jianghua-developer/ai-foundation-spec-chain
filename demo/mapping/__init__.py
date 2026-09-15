"""页面语义描述 → 组件树（L0 确定性映射层）。

对外只有两个函数：`render_screen` / `render_pages`。
"""

from .render import render_pages, render_screen
from .tree import TreeError

__all__ = ["render_pages", "render_screen", "TreeError"]
