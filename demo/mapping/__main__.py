"""CLI：python -m mapping <pages.json> <fixture.json> [-o out.json]"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .render import render_pages


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    pages = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    fixture = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    bundle = render_pages(pages, fixture)
    text = json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"
    if "-o" in argv:
        out = Path(argv[argv.index("-o") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        total = len(bundle["spec"]["elements"])
        print(f"{out}  ({len(bundle['titles'])} 屏 / 单棵树 {total} 个元素)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
