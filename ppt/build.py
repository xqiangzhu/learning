# -*- coding: utf-8 -*-
"""
构建入口：一次生成两份演示文稿（10 页精简版 = 主交付物，23 页完整版 = 附录），
每份都同时产出 .pptx 与网页速览版，并做版面自检。

用法：
    python3 build.py                # 生成两份 pptx + 两份 html，并打印自检报告
    python3 build.py --quiet        # 只在自检不通过时输出
    python3 build.py --only compact # 只构建 10 页精简版（或 --only full）

自检内容：
    1) 每个文本框/表格单元格的「估算文本高度 vs 预留高度」（FIT_LOG）；
    2) 重新打开 pptx，检查所有形状是否越出画布（13.333 x 7.5 in），
       封面/章节页有意出血的装饰形状以 deco-* 命名并跳过。
退出码非 0 表示自检失败，可直接当 CI 门禁。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import render_pptx as RP                                    # noqa: E402
import render_html as RH                                    # noqa: E402
from deck_content import (SLIDES_COMPACT, SLIDES_FULL,       # noqa: E402
                          META_COMPACT, META_FULL)

# 产物目录：仓库约定把渲染产物放在 preview/ 类目录
# （dist/ build/ out/ 这几个名字会被工作区快照忽略、不会持久化）
DIST = os.path.join(HERE, "slides")

DECKS = [
    {"key": "compact", "label": "10 页精简版（主交付）",
     "slides": SLIDES_COMPACT, "meta": META_COMPACT,
     "pptx": "体检系统升级V2-术语与切流架构-10页.pptx",
     "html": "index.html", "other": "full.html",
     "other_label": "23 页完整版"},
    {"key": "full", "label": "23 页完整版（附录）",
     "slides": SLIDES_FULL, "meta": META_FULL,
     "pptx": "体检系统升级V2-术语与切流架构-23页完整版.pptx",
     "html": "full.html", "other": "index.html",
     "other_label": "10 页精简版"},
]


def check_bounds(path):
    """重新打开 pptx，检查形状是否越出画布。"""
    from pptx import Presentation
    from pptx.util import Emu
    prs = Presentation(path)
    sw, sh = prs.slide_width, prs.slide_height
    tol = Emu(9525 * 3)                          # 容忍 ~3px 误差
    issues = []
    for i, slide in enumerate(prs.slides, 1):
        for shp in slide.shapes:
            if shp.left is None or shp.top is None:
                continue
            if str(shp.name or "").startswith("deco"):
                continue                         # 有意出血的装饰圆环
            r = shp.left + (shp.width or 0)
            b = shp.top + (shp.height or 0)
            if shp.left < -tol or shp.top < -tol or r > sw + tol or b > sh + tol:
                issues.append("p%02d %-16s l=%.2f t=%.2f r=%.2f b=%.2f"
                              % (i, shp.shape_type, shp.left / 914400.0,
                                 shp.top / 914400.0, r / 914400.0, b / 914400.0))
    return len(prs.slides._sldIdLst), issues


def build_deck(deck, quiet=False):
    pptx_path = os.path.join(DIST, deck["pptx"])
    html_path = os.path.join(DIST, deck["html"])

    RP.FIT_LOG[:] = []
    RP.build(pptx_path, slides=deck["slides"], meta=deck["meta"])
    fit = list(RP.FIT_LOG)
    RH.build(html_path, pptx_name=deck["pptx"], slides=deck["slides"],
             meta=deck["meta"],
             extra_links='<a class="ghost" href="%s">%s</a>'
                         % (deck["other"], deck["other_label"]))

    n, bound_issues = check_bounds(pptx_path)
    overflow = [f for f in fit if f["over"] > 0.0]
    if not quiet:
        print("[%s] %d 页 | pptx %.0f KB"
              % (deck["label"], n, os.path.getsize(pptx_path) / 1024.0))
        print("  %s" % pptx_path)
        print("  %s" % html_path)
        print("  文本块自检：%d 个，溢出 %d 个 | 形状越界：%d 处"
              % (len(fit), len(overflow), len(bound_issues)))
        for f in overflow:
            print("    [溢出 %+.2fin] p%02d %-14s w=%.2f h=%.2f need=%.2f | %s"
                  % (f["over"], f["page"], f["where"], f["w"], f["h"], f["need"],
                     f["head"]))
        for i in bound_issues:
            print("    [越界] " + i)
    return overflow, bound_issues


def main():
    quiet = "--quiet" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    os.makedirs(DIST, exist_ok=True)

    if not quiet:
        print("=" * 74)
    bad = 0
    for deck in DECKS:
        if only and deck["key"] != only:
            continue
        ov, bi = build_deck(deck, quiet)
        bad += len(ov) + len(bi)
    if not quiet:
        print("=" * 74)
        print("自检结论：%s" % ("全部通过（0 溢出 / 0 越界）" if not bad
                                else "%d 处问题，见上" % bad))
        print("=" * 74)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
