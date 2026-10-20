# -*- coding: utf-8 -*-
"""
构建入口：生成 .pptx 交付物 + 网页速览版，并做版面自检。

用法：
    python3 build.py            # 生成 pptx + html，并打印版面自检报告
    python3 build.py --quiet    # 只在有溢出/越界时报错

自检内容：
    1) 每个文本框的「估算文本高度 vs 预留高度」（FIT_LOG）；
    2) 重新打开 pptx，检查所有形状是否越出画布（13.333 x 7.5 in）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import render_pptx as RP                     # noqa: E402
from deck_content import SLIDES              # noqa: E402

# 产物目录：仓库约定把渲染产物放在 preview/ 类目录（dist/build/out 会被工作区忽略）
DIST = os.path.join(HERE, "slides")
PPTX_NAME = "体检系统升级V2-领域术语与切流架构.pptx"
HTML_NAME = "index.html"


def check_bounds(path):
    """重新打开 pptx，检查形状是否越出画布。"""
    from pptx import Presentation
    from pptx.util import Emu
    prs = Presentation(path)
    sw, sh = prs.slide_width, prs.slide_height
    issues = []
    for i, slide in enumerate(prs.slides, 1):
        for shp in slide.shapes:
            if shp.left is None or shp.top is None:
                continue
            if str(shp.name or "").startswith("deco"):
                continue                # 封面/章节页的出血装饰圆环
            l, t = shp.left, shp.top
            r, b = l + (shp.width or 0), t + (shp.height or 0)
            tol = Emu(9525 * 3)                       # 容忍 ~3px 误差
            if l < -tol or t < -tol or r > sw + tol or b > sh + tol:
                issues.append("p%02d %-14s l=%.2f t=%.2f r=%.2f b=%.2f"
                              % (i, shp.shape_type, l / 914400.0, t / 914400.0,
                                 r / 914400.0, b / 914400.0))
    return len(prs.slides._sldIdLst), issues


def main():
    quiet = "--quiet" in sys.argv
    os.makedirs(DIST, exist_ok=True)
    pptx_path = os.path.join(DIST, PPTX_NAME)

    RP.FIT_LOG[:] = []
    RP.build(pptx_path)

    import render_html
    html_path = os.path.join(DIST, HTML_NAME)
    render_html.build(html_path, pptx_name=PPTX_NAME)

    n_slides = len(SLIDES)
    overflow = [f for f in RP.FIT_LOG if f["over"] > 0.03]
    _, bound_issues = check_bounds(pptx_path)

    size_kb = os.path.getsize(pptx_path) / 1024.0
    if not quiet:
        print("=" * 74)
        print("生成完成：%d 页  |  pptx %.0f KB" % (n_slides, size_kb))
        print("  %s" % pptx_path)
        print("  %s" % html_path)
        print("-" * 74)
        print("文本框自检：%d 个，估算溢出 %d 个" % (len(RP.FIT_LOG), len(overflow)))
        for f in overflow:
            print("  [溢出 %+.2fin] p%02d %-14s w=%.2f h=%.2f need=%.2f | %s"
                  % (f["over"], f["page"], f["where"], f["w"], f["h"], f["need"],
                     f["head"]))
        print("形状越界自检：%d 处" % len(bound_issues))
        for i in bound_issues:
            print("  " + i)
        print("=" * 74)

    if overflow or bound_issues:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
