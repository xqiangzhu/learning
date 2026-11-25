#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
体检系统 HMSC · 业务与集成流程图 PPT 生成器
来源：domain-flows.md / frontend-flows.md / integration-flows.md（+ ADR 0001~0016 交叉口径）
风格基线：参考本仓库 b04c21a《体检平台架构决策与核心流程.pptx》生成脚本，
用 python-pptx 原生形状绘制流程图与时序图（16:9，可编辑）。
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE as MSO_LINE
from pptx.oxml.ns import qn

# ---------------- palette（与 b04c21a 保持一致） ----------------
INK      = RGBColor(0x24, 0x32, 0x4E)
GRAY     = RGBColor(0x6B, 0x77, 0x8C)
LINE     = RGBColor(0x9A, 0xAA, 0xC4)
ARROW    = RGBColor(0x51, 0x65, 0x85)
TEAL     = RGBColor(0x0E, 0x7C, 0x86)
TEAL_L   = RGBColor(0xE1, 0xF1, 0xF2)
BLUE     = RGBColor(0x2F, 0x6D, 0xB3)
BLUE_L   = RGBColor(0xE8, 0xF0, 0xFA)
PURPLE   = RGBColor(0x6D, 0x59, 0x9C)
PURPLE_L = RGBColor(0xEE, 0xEA, 0xF7)
ORANGE   = RGBColor(0xD9, 0x72, 0x2C)
ORANGE_L = RGBColor(0xFB, 0xEE, 0xE2)
GREEN    = RGBColor(0x2E, 0x8B, 0x57)
GREEN_L  = RGBColor(0xE6, 0xF4, 0xEB)
RED      = RGBColor(0xC0, 0x45, 0x3E)
RED_L    = RGBColor(0xFB, 0xE9, 0xE8)
GOLD     = RGBColor(0xB8, 0x86, 0x0B)
GOLD_L   = RGBColor(0xFA, 0xF3, 0xDF)
PAPER    = RGBColor(0xF4, 0xF7, 0xFB)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
DARK     = RGBColor(0x1B, 0x2A, 0x4A)
DARK_2   = RGBColor(0x24, 0x3A, 0x60)

FONT = "Microsoft YaHei"
EMU_IN = 914400

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

# ---------------- low-level helpers ----------------
def _style_run(r, size, bold, color, italic=False):
    f = r.font
    f.size = Pt(size); f.bold = bold; f.italic = italic
    f.color.rgb = color; f.name = FONT
    rPr = r._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
    ea.set('typeface', FONT)

def _fill_text(tf, lines, size, bold, color, align, spacing=0.98):
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    if isinstance(lines, str):
        lines = lines.split("\n")
    first = True
    for ln in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.line_spacing = spacing
        if isinstance(ln, str):
            r = p.add_run(); r.text = ln
            _style_run(r, size, bold, color)
        else:  # (text, size, bold, color)
            r = p.add_run(); r.text = ln[0]
            _style_run(r, ln[1], ln[2], ln[3])

def box(slide, x, y, w, h, text, *, fill=WHITE, line=LINE, lw=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
        size=10, bold=False, color=INK, align=PP_ALIGN.CENTER, dash=False, radius=0.16, spacing=0.98):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(lw)
        if dash:
            sp.line.dash_style = MSO_LINE.DASH
    sp.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try: sp.adjustments[0] = radius
        except Exception: pass
    _fill_text(sp.text_frame, text, size, bold, color, align, spacing)
    return sp

def tbox(slide, x, y, w, h, text, *, size=10, bold=False, color=INK, align=PP_ALIGN.LEFT, spacing=0.98):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    _fill_text(tb.text_frame, text, size, bold, color, align, spacing)
    return tb

def arrow(slide, x1, y1, x2, y2, *, color=ARROW, w=1.6, dash=False, label=None, lx=0.0, ly=-0.26):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(w)
    c.shadow.inherit = False
    ln = c.line._get_or_add_ln()
    if dash:
        d = ln.makeelement(qn('a:prstDash'), {'val': 'dash'}); ln.append(d)
    tail = ln.makeelement(qn('a:tailEnd'), {'type': 'triangle', 'w': 'med', 'len': 'med'}); ln.append(tail)
    if label:
        mx, my = (x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly
        tbox(slide, mx - 0.45, my - 0.12, 0.9, 0.26, label, size=8.5, bold=True, color=color, align=PP_ALIGN.CENTER)
    return c

def seg(slide, x1, y1, x2, y2, *, color=ARROW, w=1.6, dash=False):
    """line segment without arrowhead (for elbows)"""
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(w)
    c.shadow.inherit = False
    if dash:
        lnn = c.line._get_or_add_ln()
        d = lnn.makeelement(qn('a:prstDash'), {'val': 'dash'}); lnn.append(d)
    return c

def chip_w(text, size=9):
    per_cjk = size / 72 * 1.02
    per_asc = size / 72 * 0.52
    wd = sum(per_cjk if ord(ch) > 0x2E80 else per_asc for ch in text)
    return wd + 0.28

def chip(slide, x, y, text, *, fill=PAPER, line=LINE, color=INK, size=9, bold=False, h=0.36):
    w = chip_w(text, size)
    box(slide, x, y, w, h, text, fill=fill, line=line, size=size, bold=bold, color=color, radius=0.5)
    return x + w + 0.14

def chip_row(slide, chips, x0, y, maxx=12.78, *, fill=PAPER, line=LINE, color=INK, size=9, h=0.36, rowdy=0.46):
    x, y = x0, y
    for t in chips:
        w = chip_w(t, size)
        if x + w > maxx:
            x = x0; y += rowdy
        x = chip(slide, x, y, t, fill=fill, line=line, color=color, size=size, h=h)
    return y

def tag(slide, x, y, text, color, size=11):
    return tbox(slide, x, y, 6.5, 0.3, text, size=size, bold=True, color=color)

_PAGE = [1]
def page_no(slide, n=None):
    _PAGE[0] += 1
    tbox(slide, 12.35, 7.08, 0.85, 0.3, f"{_PAGE[0]:02d}", size=9, color=GRAY, align=PP_ALIGN.RIGHT)

def header(slide, num, title, en, accent, tags, badge_size=19):
    box(slide, 0.55, 0.36, 0.68, 0.68, num, fill=accent, line=None, size=badge_size, bold=True,
        color=WHITE, radius=0.22)
    tbox(slide, 1.42, 0.28, 8.6, 0.55, title, size=23, bold=True, color=INK)
    tbox(slide, 1.44, 0.86, 8.6, 0.3, en, size=10.5, color=GRAY)
    widths = [chip_w(t, 9) for t in tags]
    total = sum(widths) + 0.14 * (len(tags) - 1)
    x = 12.78 - total
    for t, w in zip(tags, widths):
        box(slide, x, 0.52, w, 0.38, t, fill=WHITE, line=accent, size=9, bold=True, color=accent, radius=0.5)
        x += w + 0.14
    seg(slide, 0.55, 1.32, 12.78, 1.32, color=RGBColor(0xD8, 0xE0, 0xEC), w=1.0)

def decision_bar(slide, text, accent):
    box(slide, 0.55, 1.48, 12.23, 0.6, text, fill=PAPER, line=None, shape=MSO_SHAPE.RECTANGLE,
        size=12, bold=True, color=INK, align=PP_ALIGN.LEFT)
    box(slide, 0.55, 1.48, 0.09, 0.6, "", fill=accent, line=None, shape=MSO_SHAPE.RECTANGLE)

def band(slide, label, chips, y=6.52):
    tbox(slide, 0.55, y + 0.04, 1.3, 0.3, label, size=9.5, bold=True, color=GRAY)
    chip_row(slide, chips, 1.72, y, maxx=12.78, fill=PAPER, line=RGBColor(0xD5, 0xDD, 0xEA),
             color=RGBColor(0x4A, 0x55, 0x6C), size=9)

def new_slide():
    return prs.slides.add_slide(BLANK)

# =========================================================
# S0 封面
# =========================================================
s = new_slide()
box(s, 0, 0, 13.334, 7.5, "", fill=DARK, line=None, shape=MSO_SHAPE.RECTANGLE)
box(s, 9.6, -1.6, 5.2, 5.2, "", fill=DARK_2, line=None, shape=MSO_SHAPE.OVAL)
box(s, -1.3, 5.2, 3.8, 3.8, "", fill=DARK_2, line=None, shape=MSO_SHAPE.OVAL)
tbox(s, 0.75, 0.6, 8.0, 0.35, "HMSC · 企业健康体检福利平台", size=13, bold=True, color=RGBColor(0x8F, 0xB4, 0xE3))
tbox(s, 0.75, 1.75, 12.2, 1.05, "体检系统业务与集成流程图全景", size=38, bold=True, color=WHITE)
tbox(s, 0.78, 2.85, 12.2, 0.45, "统一语言名词解释 × 领域实体 × 核心流程 × 前端基线 × 系统集成时序 · 36 页全图解（可编辑原生形状）",
     size=15, color=RGBColor(0x9F, 0xC3, 0xE8))
seg(s, 0.8, 3.55, 6.2, 3.55, color=TEAL, w=2.5)
cover_steps = ["配置权益", "准入门禁", "选检加车", "结算支付", "预约履约", "到检核销", "报告解读", "报销变现"]
cx, cw, gap = 0.75, 1.28, 0.24
for i, t in enumerate(cover_steps):
    box(s, cx, 5.15, cw, 0.62, t, fill=None, line=RGBColor(0x5F, 0x7F, 0xA6), size=10.5,
        bold=True, color=RGBColor(0xCF, 0xE0, 0xF5), radius=0.24)
    if i < len(cover_steps) - 1:
        arrow(s, cx + cw + 0.02, 5.46, cx + cw + gap - 0.02, 5.46,
              color=RGBColor(0x5F, 0x7F, 0xA6), w=1.4)
    cx += cw + gap
tbox(s, 0.78, 6.35, 11.0, 0.3, "来源：domain-flows.md / frontend-flows.md / integration-flows.md（ADR-0001~0016 交叉校验）",
     size=10.5, color=RGBColor(0x7C, 0x93, 0xB8))
tbox(s, 0.78, 6.75, 9.0, 0.3, "流程图汇报版 · 2026-11", size=10.5, color=RGBColor(0x7C, 0x93, 0xB8))

# =========================================================
# S1 流程图全景导航
# =========================================================
s = new_slide()
header(s, "览", "流程图全景导航 · 三层文档体系", "Flow Map · Domain × Frontend × Integration", BLUE,
       ["全景", "3 层", "22 图"], badge_size=15)
decision_bar(s, "三层互补：领域流程图不暴露接口细节，集成时序图收敛全部跨系统契约，前端流转图锁定页面衔接与状态码口径 —— 三层术语严格一致。",
             BLUE)
cards = [
    ("统一语言 · 名词解释", "Ubiquitous Language", "59 词条 / 9 组", "标准定义 + 避免叫法\n权益交易 / 门店履约 / 报告解读\n积分结算 / 套餐模型 / 商城卡券", BLUE, "P03 – P12"),
    ("领域实体全景", "Domain Entities", "29 实体 / 21 详定义", "聚合根 / 内部实体 / 值对象\n生命周期与业务不变量\n建模规范与免密赋权规约", TEAL, "P13 – P15"),
    ("核心领域流程", "domain-flows.md", "7 张流程图", "端到端主流程 + 6 张子图\n（配置权益/选检结算/预约履约\n/到检报告/状态机/报销）", ORANGE, "P16 – P22"),
    ("前端页面流转", "frontend-flows.md", "5 主线 + 名词对照", "员工/家属/优惠购/报销双通道\n页面流转与隐式上下文\n状态码基线与口径对齐", PURPLE, "P23 – P27"),
    ("系统集成时序", "integration-flows.md", "1 拓扑 + 7 时序图", "HMC/积分支付/直连供应商\n/TBDS/211 保险/HMES 解读\n/报销财务 8 大下游", GOLD, "P28 – P36"),
]
for i, (cn, en, cnt, sample, acc, rng) in enumerate(cards):
    x, y = 0.55 + i * 2.47, 2.42
    box(s, x, y, 2.34, 2.62, "", fill=WHITE, line=RGBColor(0xD8, 0xE0, 0xEC), lw=1.0, radius=0.08)
    box(s, x, y, 2.34, 0.07, "", fill=acc, line=None, shape=MSO_SHAPE.RECTANGLE)
    tbox(s, x + 0.14, y + 0.14, 2.1, 0.32, cn, size=11, bold=True, color=INK)
    tbox(s, x + 0.15, y + 0.5, 2.1, 0.24, en, size=8, color=GRAY)
    tbox(s, x + 0.15, y + 0.82, 2.1, 0.28, cnt, size=10, bold=True, color=acc)
    tbox(s, x + 0.15, y + 1.18, 2.08, 1.05, sample, size=8, color=RGBColor(0x4A, 0x55, 0x6C))
    box(s, x + 0.15, y + 2.18, 1.5, 0.32, rng, fill=PAPER, line=None, size=8.5, bold=True, color=acc, radius=0.5)
tbox(s, 0.55, 5.35, 12.2, 0.3, "阅读路径：名词解释与领域实体（P03–P15）→ 领域主链（P16 端到端）→ 逐子图下钻 → 前端基线（P23–P27）→ 集成时序与契约收口（P28–P36）",
     size=10, color=GRAY)
steps = ["配置权益", "准入门禁", "智能选检", "加车结算", "预约履约", "到检核销", "报告解读", "报销变现"]
cx, cw2, step2 = 0.6, 1.58, 1.51
for i, t in enumerate(steps):
    box(s, cx, 5.85, cw2, 0.5, t, fill=[BLUE, PURPLE, TEAL, BLUE, TEAL, TEAL, ORANGE, PURPLE][i],
        line=None, shape=MSO_SHAPE.CHEVRON, size=9.5, bold=True, color=WHITE)
    cx += step2
band(s, "口径铁律", ["单链归属 Benefit→Order→Appointment", "订单/预约两套独立状态码", "业务图不暴露 URL/MQ/SFTP",
                    "积分 1:1 等值", "资金回调驱动退积分"], y=6.62)
page_no(s)

# =========================================================
# 统一语言 · 名词解释（59 词条 / 9 组，风格沿用 b04c21a 术语表）
# =========================================================
def term_card(slide, x, y, w, h, cn, en, definition, avoid, accent, compact=False):
    box(slide, x, y, w, h, "", fill=WHITE, line=RGBColor(0xD8, 0xE0, 0xEC), lw=0.9, radius=0.055)
    box(slide, x, y, 0.075, h, "", fill=accent, line=None, shape=MSO_SHAPE.RECTANGLE)
    tsize = 10 if compact else 11.5
    esize = 8 if compact else 9
    dsize = 8 if compact else 9
    asize = 7.5 if compact else 8.5
    tb = slide.shapes.add_textbox(Inches(x + 0.17), Inches(y), Inches(w - 0.3), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    lines = [
        [(cn + "  ", tsize, True, INK), (en, esize, False, GRAY)],
        (definition, dsize, False, RGBColor(0x33, 0x3E, 0x52)),
        [("避免叫法：", asize, True, RED), (avoid, asize, False, RED)],
    ]
    first = True
    for ln in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = 0.98
        if isinstance(ln, tuple):
            ln = [ln]
        for t, sz, bd, col in ln:
            r = p.add_run(); r.text = t
            _style_run(r, sz, bd, col)
    return tb

def grid_cards(slide, terms, accent, compact, y0, yh, cols=3, x0=0.55, xw=12.23, gap=0.14):
    cw = (xw - gap * (cols - 1)) / cols
    for i, (cn, en, df, av) in enumerate(terms):
        r_, c_ = divmod(i, cols)
        term_card(slide, x0 + c_ * (cw + gap), y0 + r_ * (yh + gap), cw, yh,
                  cn, en, df, av, accent, compact)

def glossary_slide(label, title, en, accent, desc, terms):
    s = new_slide()
    header(s, label, title, en, accent, ["统一语言", f"{len(terms)} 词条"], badge_size=13)
    decision_bar(s, desc, accent)
    rows = (len(terms) + 2) // 3
    compact = rows >= 3
    y0 = 2.32 if rows >= 3 else (2.42 if rows == 2 else 2.72)
    yh = 1.22 if rows >= 3 else (1.72 if rows == 2 else 2.05)
    grid_cards(s, terms, accent, compact, y0, yh)
    tbox(s, 0.55, 7.05, 11.0, 0.28,
         "词条格式：标准定义 ＋ 避免叫法 —— 评审、需求、代码命名与外部供应商沟通统一使用标准名词",
         size=8.5, color=GRAY)
    page_no(s)
    return s

# ---- G0 总览 ----
s = new_slide()
header(s, "词", "建立统一语言 · 体检业务核心名词解释", "Ubiquitous Language · 59 Terms in 9 Groups",
       BLUE, ["统一语言", "59 词条", "9 组"], badge_size=15)
decision_bar(s, "体检业务核心域：负责体检权益与预约履约全生命周期管理 —— 权益发放与购买 → 分院预约排期 → 到检核销 → 报告交付 → 健康解读增值服务。",
             BLUE)
gcat = [
    ("权益与交易", "Entitlements", "6 词条", "Order · SubOrder · Holder · Refund", BLUE),
    ("机构、门店与履约", "Supplier, Store & Fulfillment", "15 词条 · 2 页", "Appointment · Same-Store Reschedule · Bundled", TEAL),
    ("报告与解读", "Reporting & VAS", "13 词条 · 2 页", "Report · LLM-OCR · AI / 医生解读", ORANGE),
    ("购物车与合并结算", "Cart & Checkout", "3 词条", "Combination Order · Capacity Hold", GREEN),
    ("积分与福利结算", "Points & Welfare", "8 词条", "Point Parity · Shadow Ledger · Callback Refund", GOLD),
    ("套餐与项目模型", "Packages & Items", "9 词条", "Single-Core Invariant · Demographic Guard", PURPLE),
    ("健康商城与卡券", "Shop & Vouchers", "5 词条", "Card Voucher Redemption · Non-Refundable", TEAL),
]
xs4 = [0.55, 3.64, 6.73, 9.82]
ys2 = [2.42, 4.12]
for i, (cn, en, cnt, sample, acc) in enumerate(gcat):
    x, y = xs4[i % 4], ys2[i // 4]
    box(s, x, y, 2.91, 1.5, "", fill=WHITE, line=RGBColor(0xD8, 0xE0, 0xEC), lw=1.0, radius=0.08)
    box(s, x, y, 2.91, 0.07, "", fill=acc, line=None, shape=MSO_SHAPE.RECTANGLE)
    tbox(s, x + 0.16, y + 0.13, 2.65, 0.32, cn, size=11.5, bold=True, color=INK)
    tbox(s, x + 0.17, y + 0.47, 2.65, 0.24, en, size=8, color=GRAY)
    tbox(s, x + 0.17, y + 0.72, 2.65, 0.26, cnt, size=10, bold=True, color=acc)
    tbox(s, x + 0.17, y + 1.0, 2.62, 0.44, sample, size=8, color=GRAY)
x, y = xs4[3], ys2[1]
box(s, x, y, 2.91, 1.5, "", fill=PAPER, line=RGBColor(0xD8, 0xE0, 0xEC), lw=1.0, radius=0.08)
tbox(s, x + 0.16, y + 0.13, 2.65, 0.3, "✗ Avoid = 沟通禁用叫法", size=10.5, bold=True, color=RED)
tbox(s, x + 0.17, y + 0.48, 2.62, 0.95,
     "每词条 = 标准定义 + 避免叫法。防止「预约单≠订单」「退款≠取消预约」等混用歧义，评审与编码统一引用本词表。",
     size=8.5, color=RGBColor(0x4A, 0x55, 0x6C))
tbox(s, 0.55, 5.95, 12.2, 0.3, "配套阅读：P13 – P15 领域实体全景 ｜ P16 – P22 领域流程图 ｜ P23 – P27 前端基线 ｜ P28 – P36 集成时序",
     size=9.5, color=GRAY)
steps = ["权益", "选购", "建单", "支付", "预约", "到检", "报告", "解读"]
cx, cw2, step2 = 0.6, 1.58, 1.51
for i, t in enumerate(steps):
    box(s, cx, 6.45, cw2, 0.5, t, fill=[BLUE, PURPLE, TEAL, BLUE, TEAL, TEAL, ORANGE, PURPLE][i],
        line=None, shape=MSO_SHAPE.CHEVRON, size=9.5, bold=True, color=WHITE)
    cx += step2
page_no(s)

# ---- G1 权益与交易 ----
glossary_slide("词1", "权益与交易", "Entitlements", BLUE,
    "界定体检资格与资金交易的凭据体系：一笔主订单严格对应一位持有人，子订单承载费用归属与套餐性质。",
    [
    ("主订单", "Order",
     "体检资格与支付结算的交易凭据：支付成功即持有待预约权益；取消预约后权益恢复可再约；到检/出报告后闭环。",
     "预约单、挂号单、采购单"),
    ("子订单", "SubOrder",
     "主订单项下具体项目包实例，区分费用归属（统付/自费）与套餐性质（主套餐、加项、升级），随主单统一履约。",
     "主订单、项目明细、订单项"),
    ("加项包", "Add-on Package",
     "主套餐外额外叠加的单项/组合项目，通常员工自选自费或积分兑换，履约时随主套餐打包提交分院。",
     "升级包、附加服务、附加险"),
    ("升级包", "Upgrade Package",
     "将原有主套餐整体置换升舱为更高规格套餐的差价凭据。",
     "加项包、换购"),
    ("持有人", "Holder",
     "实际享有并执行体检资格的自然人；业务严格约束一笔主订单仅对应一位持有人。",
     "购买人、下单人、客户、用户"),
    ("退款", "Refund",
     "已支付主订单款项原路返还：可取消预约后独立发起，也可直接申请并由系统级联取消关联预约单。",
     "取消预约、换单、废单"),
    ])

# ---- G2 机构、门店与预约 ----
glossary_slide("词2", "机构、门店与预约", "Supplier, Store & Appointment", TEAL,
    "区分供应商两类接入形态（API 直连 / 公立人工确认）与门店实体；预约单是依附主订单存在的履约凭据。",
    [
    ("线上直连供应商", "Online Supplier",
     "美年、爱康、瑞慈、中科、嘉会等具备 API 直连的民营连锁；预约时实时排期锁单，直接预约成功。",
     "线下供应商、合作商、第三方"),
    ("线下医院供应商", "Offline Supplier",
     "公立医院体检中心，每家为独立 Supplier；无实时排期接口，走「申请成功→确认预约」人工确认链路。",
     "线上供应商、虚拟机构"),
    ("体检分院 / 门店", "Store",
     "供应商在具体地理位置设立的实体网点，具备地址、营业时间、停业状态与适用套餐包清单。",
     "供应商、机构、医院"),
    ("套餐门店交集匹配", "Intersection Matching",
     "可履约门店必须严格满足主套餐 + 全部自选加项包的设备与服务能力交集；支持先选套餐或先选门店双向流程。",
     "自由搭配、任意门店"),
    ("停业展示策略", "Suspension Visibility",
     "企业项目维度配置停业分院的展示规则：完全过滤隐藏，或保留展示但置灰提示暂停服务不可约。",
     "门店下架、物理删除"),
    ("预约单", "Appointment",
     "持有人锁定供应商、分院与就检日期的履约凭据，依附主订单，包含主套餐与所有加项包。",
     "订单、排期、挂号单"),
    ])

# ---- G3 履约规则与边界 ----
glossary_slide("词3", "履约规则与边界", "Fulfillment Rules & Boundaries", GREEN,
    "约定改期、取消、屏蔽日、特批与超期释放等履约边界：同店改期、当日禁退可改、主+加项合并原子交付。",
    [
    ("原分院同店改期", "Same-Store Reschedule",
     "仅在原预约分院范围内变更日期/时段；原单编号不变、不建新单、不影响主订单，禁止跨店。",
     "重新预约、换店改期"),
    ("取消预约", "Cancel Appointment",
     "释放机构已锁定档期，主订单恢复可再次预约；体检日当天默认禁止用户主动取消。",
     "退单、退款、废单"),
    ("项目屏蔽日", "Blackout Dates",
     "MIS 在企业项目维度配置的排期阻断日（长假、封网日），员工端命中日期统一屏蔽不可选。",
     "机构停业、排期约满"),
    ("排期时间段", "Schedule Period",
     "同一就检日内的预约时间窗（如 08:00-09:00）；项目开关控制，未启用降级为全天。",
     "预约轮次、挂号时段"),
    ("特批协调排期", "Coordination Mode",
     "日期标记「需协调」时触发客服特批：生成「申请成功」预约单，线下人工对接医院加号加配额。",
     "线上直连锁单、自动驳回"),
    ("当日不对称改退", "Asymmetric Day-of Policy",
     "体检当天禁止主动取消（保机构医疗备料），但允许原分院内改期至后续可用日期。",
     "全面锁单、任意退约"),
    ("超期未到检自动释放", "Overdue Cancellation",
     "No-show 超体检日由定时任务自动取消预约单、释放占容，主订单恢复「待预约」。",
     "权益作废、永久占用"),
    ("合并原子履约", "Bundled Fulfillment",
     "主套餐 + 全部加项包不可分割整体交付（线上单一外部单挂子项 / 线下单条 Excel），单店单次完成。",
     "拆分预约、跨院分拆"),
    ("权益到期拦截门禁", "Equity Expiry Guard",
     "权益过期后现存预约单虽可取消，但无法再次选店发起新预约，锁死企业福利预算敞口。",
     "宽限期补约、过期换店"),
    ])

# ---- G4 报告同步与档案 ----
glossary_slide("词4", "报告同步与档案", "Reporting & Health Record", ORANGE,
    "到检与报告的回传归档机制：双轨状态同步、大模型 OCR 统一结构化、外院报告隔离与家庭共查。",
    [
    ("体检报告", "Report",
     "体检中心到检后出具的总检成果数据与原件文件，标志体检履约链路的终态闭环。",
     "解读结果、结论单"),
    ("异常指标", "Abnormal Findings",
     "报告中超出参考值区间或专科医生提示阳性体征的具体指标项。",
     "疾病、确诊、异常报告"),
    ("双轨到检报告同步", "Dual-Track Ingestion",
     "线上民营定时轮询拉取到检+PDF（原生 JSON 已弃用）；线下公立由 MIS 导入名单或核销上传。",
     "全自动回调、纯手工维护"),
    ("大模型OCR结构化解析", "LLM-OCR Ingestion",
     "全域原版 PDF 统一经大模型 OCR 抽取检测值与异常指标，映射标准字典后归档健康档案 HMES。",
     "人工录入、机构私有 JSON"),
    ("自主外院报告隔离", "Past Report Isolation",
     "用户自传外院历史报告仅个人端可查，不推送健康档案、不参与正式历年趋势比对。",
     "混合档案、污染主档"),
    ("家庭报告共用查看", "Family Report Aggregation",
     "员工账号可直接查阅本人及出资家属的体检报告，界面切换持有人，不设跨账号强制授权。",
     "强制账号隔离、家属独立鉴权"),
    ])

# ---- G5 解读增值服务 ----
glossary_slide("词5", "解读增值服务", "Interpretation Value-Added Services", PURPLE,
    "分层解读服务：免费普惠 AI 即时解读与异步三方医生解读并行；C24/C59 随权益导入而非商城零售。",
    [
    ("报告解读增值服务", "Report Interpretation",
     "系统配置启用的三方机构增值解读：报告推送专业机构深度分析，异步回传结论供用户查阅。",
     "AI问答、医生问诊"),
    ("AI智能解读", "AI Interpretation",
     "基于结构化指标由算法/大模型即时输出成因与生活建议，与人工咨询独立平行、互不干扰。",
     "医生咨询、人工解读"),
    ("医生咨询", "Doctor Consultation",
     "用户就健康问题或指标向专业医生发起一对一图文/电话问诊，独立于 AI 解读存在。",
     "报告解读、AI客服"),
    ("异步三方医生解读流水线", "Async Physician Pipeline",
     "工单制：报告+病史异步推送三方专科医生，限时核阅后结构化结论回调回写，挂载权益与报告项下。",
     "实时通讯、电话直拨"),
    ("权益子产品导入赋权", "Benefit-Imported Sub-Product",
     "C24/C59 不在商城销售：随企业权益包作为子产品导入，出报告后核验权益开放解读入口。",
     "商城零售单买、事后加购"),
    ("项目级普惠AI解读", "Universal AI Interpretation",
     "项目开关开启后，所有出报告员工均可即时、免费查阅指标成因与调理建议。",
     "付费AI、专享AI"),
    ("B端异常指标监控看板", "B2B Dashboard",
     "面向企业 HR 的团队异常指标分布与健康监控看板，脱敏合规，服务雇主健康干预决策。",
     "个人短信报警、粗暴推弹窗"),
    ])

# ---- G6 购物车与合并结算 ----
glossary_slide("词6", "购物车与合并结算", "Cart & Aggregate Checkout", GREEN,
    "购物车到收银台的瞬态结算链路：合单不占容、支付即解体、超时自动释放占容回退购物车。",
    [
    ("购物车项", "Cart Item",
     "单个持有人意向体检的草稿容器：承载 1 位持有人 + 主套餐 + 加项包 + 意向门店日期；不占名额，超时回退，支付回调后物理清理。",
     "购物车商品、预订单、挂单"),
    ("组合订单", "Combination Order",
     "多购物车项合并结算的瞬态聚合凭据：仅用于收银台合并扣减积分与调起支付网关；支付成功即解体为各自独立主订单，不承载售后。",
     "合并订单、大订单、批量订单"),
    ("排期临时占容", "Capacity Hold",
     "下单时对意向分院时段的临时占座：15 分钟未支付由定时任务自动取消并释放；支付成功回调后正式扣减确立。",
     "锁库存、排期占座、预约挂号"),
    ])

# ---- G7 积分与福利结算 ----
glossary_slide("词7", "积分与福利结算", "Points & Welfare Settlement", GOLD,
    "1:1 等值抵扣与两阶段结算：先升舱后加项、子订单分摊落标、双账本镜像防超扣与回调驱动退积分。",
    [
    ("积分等值比例", "Point Parity",
     "积分与法定货币严格 1:1 等值（1 积分=1 元），忽略动态汇率配置，支持 100% 全额抵扣。",
     "动态积分比例、浮动汇率"),
    ("积分抵扣优先级", "Point Deduction Priority",
     "混合结算的法定扣减顺序：先主套餐升级/加价，后自选加项包。",
     "加项优先、随机抵扣、均摊抵扣"),
    ("积分子订单分摊", "SubOrder Allocation",
     "整单积分与现金按优先级精确写入对应子订单记账，支付结构透明可溯。",
     "主单汇总记账、模糊分摊"),
    ("权益附随积分", "Benefit-bound Points",
     "额度与生命周期完全依附体检权益起止日期；总账由下游积分平台托管，HMSC 不设独立钱包。",
     "平台代币、独立钱包、永久积分"),
    ("回调驱动退积分", "Callback-driven Refund",
     "资金退款异步成功回调驱动退还积分；下游失败回滚重试，超限流转人工介入。",
     "同步退积分、资金前置返还"),
    ("两阶段冻结转实扣", "Two-phase Settlement",
     "正向「下单预冻结→支付回调实扣」；逆向「取消待付原路解冻→退款回调解冻」。",
     "直接扣减、立即核销、单步扣款"),
    ("双边镜像账本", "Shadow Ledger",
     "外部平台冻结的同时在核心本地并发记录镜像预冻结流水：防超扣、双边留痕、端到端对账。",
     "本地独立钱包、单边记账、虚账"),
    ("明细级SKU穿透", "SKU-level Mapping",
     "向外部平台提交扣减时将子订单精细映射为商品行项目（sku/数量/单价），拒绝订单级总额粗扣。",
     "订单级总额抵扣、粗粒度扣减"),
    ])

# ---- G8 套餐与项目模型 ----
glossary_slide("词8", "套餐与项目模型", "Packages, Items & Customization", PURPLE,
    "套餐层级与医学规约：主干单选互斥、差额升舱、适检门禁、标准医学字典与家属积分共济。",
    [
    ("主干套餐单选互斥", "Single-Core Invariant",
     "标准主套餐(00)/升级套餐(02)/加价套餐(03)必须且只能选其一作为履约基础。",
     "多选主套餐、仅选加项包"),
    ("升级换购补差价", "Upgrade Price Difference",
     "升级套餐按「升级售价 − 统付基准价」差额算价；差价支持自费或积分 1:1 全额抵扣。",
     "升级全额自费、独立双套餐"),
    ("加价套餐", "Price-markup Package",
     "原套餐项目不变、因分院溢价产生的附加价套餐(03)：编码与主套餐一致，补付 extraPrice。",
     "升级套餐、加项包"),
    ("加项包互斥与限额", "Exclusivity & Budget Cap",
     "自选加项包(01)叠加约束：同类冲突项目医学互斥禁兼选，受企业金额/额度上限严格管控。",
     "无限加选、冲突混选"),
    ("适检人口属性门禁", "Demographic Guard",
     "基于持有人性别与婚姻状态做前端展示过滤与下单硬拦截，杜绝禁忌项目开单。",
     "通用体检包、人群免检"),
    ("受益人范围划分", "Beneficiary Scope",
     "员工专属产品包(P) 与家属产品包(G) 分区，对应不同统付额度、自费补贴与可约分院清单。",
     "统一大包、混龄包"),
    ("平台标准医学字典", "Standard Medical Taxonomy",
     "平台统一维护科目与临床项目字典：各供应商异构项目入库统一映射对齐，保证跨机构可比。",
     "供应商私有字典、随意录入"),
    ("家属积分共济", "Family Points Sharing",
     "家属包企业不统付：员工全额自费或纯积分购买，可直扣员工本人福利积分账户。",
     "企业统付家属、独立家属积分"),
    ("问卷推荐自动勾选", "Auto-Recommendation",
     "基于生活习惯与家族病史问卷计算健康风险，推荐套餐与加项包并默认自动勾选。",
     "纯文本建议、盲目自选"),
    ])

# ---- G9 健康商城与卡券 ----
glossary_slide("词9", "健康商城与卡券", "Health Shop & Vouchers", TEAL,
    "多租户商城与卡券风控：项目级自定义分类、卡密兑换生成核心权益、兑换后锁死不可退款。",
    [
    ("项目自定义分类", "Project Custom Categorization",
     "按企业项目维度配置商品分类，双轨标签区分「优惠套餐购买/健康商城分类」，前端动态过滤，千企千面橱窗隔离。",
     "平台硬编码分类、大一统类目"),
    ("卡券卡密兑换", "Card Voucher Redemption",
     "商城卡券在企业体检端经 checkGardPassword 核验，在下游核心域生成正式权益（Benefit）后进入标准履约流程。",
     "跨域直生待预约单、绕过核心权益"),
    ("优惠套餐即时转单", "Discount Package Order",
     "自费优惠套餐支付成功直接生成待预约主订单（支持积分 1:1 抵扣），免卡券兑换环节，可立即选分院排期。",
     "优惠卡密、延迟入账"),
    ("卡密核销锁死边界", "Non-Refundable Boundary",
     "未兑换期关闭前台自助退款，须客服 MIS 审核原路退；一旦兑换生成核心权益即永久锁死不可退。",
     "自助秒退卡密、兑换后退卡"),
    ("实物商品退款级序", "Physical Goods Refund",
     "未发货可自主即时退款；发货后须退货退款闭环（寄回验收）；混合退款由资金回调驱动释放积分。",
     "发货后直接退款、同步退积分"),
    ])

# =========================================================
# 领域实体全景（domain-entities.md）
# =========================================================
# ---- E1 实体清单总览 ----
s = new_slide()
header(s, "实", "领域实体全景总览 · 29 实体", "Domain Entities · Aggregates, Inner Entities & Value Objects", TEAL,
       ["domain-entities", "实体清单"], badge_size=15)
decision_bar(s, "按限界上下文划分 7 大实体群；实体 = 有唯一标识与生命周期，值对象 = 由属性定义、不可变、可互换；外部访问必须经聚合根保护不变量。",
             TEAL)
ent_groups = [
    ("企业配置与名单", "6 实体", BLUE, [
        "Project 企业项目（projectCode · 顶层规则根）",
        "TeamOrder 团单（teamOrderCode · 年度/批次周期）",
        "Group 组别（内部实体 · 数据层前台不露出）",
        "ImportBatch 导入批次（batchSerialNo · HR 批量导入）",
        "StaffMember 白名单员工（customerCode · 鉴权建档）",
        "User 用户账号（userId · 出资与家庭报告共查）"]),
    ("权益与产品", "6 实体", TEAL, [
        "Benefit / Equity 体检权益（importSerialNumber）",
        "ProductPackage 产品包（packageCode · P 员工/G 家属）",
        "MedicalPackage 体检套餐（00/02/03/01 四形态）",
        "SubProduct 增值子产品（C24/C59 导入赋权）",
        "MedicalItem 临床项目（标准医学字典）",
        "RecommendationRecord 智能推荐（01→02/03）"]),
    ("交易与结算", "7 实体", GOLD, [
        "Order 主订单（mainOrderCode · 含 0 元统付）",
        "SubOrder 子订单（费用归属与套餐性质分摊）",
        "Holder 持有人（1:1 强约束）",
        "CartItem 购物车项（草稿不占容）",
        "CombinationOrder 组合订单（瞬态支付即解体）",
        "CardVoucher 卡券卡密（兑换锁死不可退）",
        "ElectronicInvoice 电子发票（开票/作废/红冲）"]),
    ("履约与资源", "3 实体", PURPLE, [
        "Appointment 预约单（appointmentCode · 状态中枢）",
        "Store 分院门店（storeCode · 能力与营业状态）",
        "Supplier 供应商（直连 API / 线下人工）"]),
    ("报告与增值", "3 实体", ORANGE, [
        "Report 体检报告（reportId · OCR 归档 HMES）",
        "ReportInterpretation 解读工单（HMC 托管）",
        "ConsultRecord AI 导医咨询（科室推荐）"]),
    ("合规与理赔", "2 实体", RED, [
        "ConsentRecord 合规签署（哈希存证 + PDF 留档）",
        "ClaimApplication 商保理赔（OCR+签名+SFTP 211）"]),
    ("积分与报销", "3 实体", GREEN, [
        "ShadowLedgerRecord 镜像流水（防超扣对账）",
        "MedicalReimbursement 体检代报销（01/02）",
        "PointsReimbursement 积分报销（KBX · 两阶段）"]),
]
xs7 = [0.55, 3.64, 6.73, 9.82]
ys2 = [2.35, 4.72]
for i, (cn, cnt, acc, items) in enumerate(ent_groups):
    x, y = xs7[i % 4], ys2[i // 4]
    hh = 2.22
    box(s, x, y, 2.91, hh, "", fill=WHITE, line=RGBColor(0xD8, 0xE0, 0xEC), lw=1.0, radius=0.06)
    box(s, x, y, 2.91, 0.06, "", fill=acc, line=None, shape=MSO_SHAPE.RECTANGLE)
    tbox(s, x + 0.14, y + 0.1, 2.0, 0.28, cn, size=10.5, bold=True, color=INK)
    tbox(s, x + 2.1, y + 0.12, 0.75, 0.24, cnt, size=8, bold=True, color=acc, align=PP_ALIGN.RIGHT)
    yy = y + 0.42
    step_i = min(0.29, (hh - 0.5) / max(len(items), 1))
    for it in items:
        tbox(s, x + 0.14, yy, 2.66, step_i, "· " + it, size=6.5, color=RGBColor(0x3A, 0x46, 0x5C))
        yy += step_i
box(s, xs7[3], ys2[1], 2.91, 2.22, "", fill=PAPER, line=RGBColor(0xD8, 0xE0, 0xEC), lw=1.0, radius=0.06)
tbox(s, xs7[3] + 0.14, ys2[1] + 0.1, 2.66, 0.28, "实体 vs 值对象判别", size=10.5, bold=True, color=INK)
tbox(s, xs7[3] + 0.14, ys2[1] + 0.42, 2.66, 1.7,
     ["实体：有唯一标识与生命周期（Order / Appointment / Store…），标识创建后不可变",
      "值对象：由属性定义、不可变、可互换（SchedulePeriod 时段 / StoreAddress 地址 / Money 金额 / AbnormalFinding 异常指标）",
      "充血模型：状态扭转内置实体方法 appointment.cancel()，禁 setter 篡改"],
     size=7, color=RGBColor(0x4A, 0x55, 0x6C))
page_no(s)

# ---- E2 核心聚合根与业务不变量 ----
s = new_slide()
header(s, "实2", "核心聚合根与业务不变量", "Core Aggregates & Business Invariants", TEAL,
       ["domain-entities", "Invariants"], badge_size=13)
decision_bar(s, "六大核心聚合根各自守护不变量：单链归属、单持有人、同店改期单号不变、合并原子交付、主干单选互斥、报告档案隔离。",
             TEAL)
agg = [
    ("Benefit 体检权益", "importSerialNumber / equityId", BLUE,
     "EFFECTIVE → LOCKED → CONSUMED ｜ EXPIRED / REVOKED",
     "预约门禁前置校验；两阶段锁定释放 lockForAppointment/releaseLock；权益到期熔断禁止再约"),
    ("Order 主订单", "orderId / mainOrderCode", TEAL,
     "WAIT_PAY → PAID_WAIT_APPOINT → APPOINTED → FINISHED / REFUNDED",
     "单一持有人不变量（1:1 Holder）；Benefit→Order→Appointment 单链；退款前置取消预约；0 元统付自动视为已支付"),
    ("Appointment 预约单", "appointmentId / appointmentCode", PURPLE,
     "PENDING / CONFIRMED(02) → CHECKED_IN(04) → REPORTED(05)｜CANCELLED / OVERDUE / FAILED(07)",
     "同店改期禁跨店且单号不变；当日不对称改退；主+加项合并原子履约；团检日 groupCheck(Y/N) 动态落标"),
    ("ProductPackage 产品包", "packageCode / packageId", GOLD,
     "DRAFT → ACTIVE → SUSPENDED / EXPIRED",
     "P 员工 / G 家属受益人隔离（家属不统付）；门店白名单圈定履约边界；C24/C59 挂载子产品导入赋权"),
    ("MedicalPackage 体检套餐", "packetCode / packetId", ORANGE,
     "形态：00 标准 / 02 升级 / 03 加价 / 01 自选加项",
     "主干单选互斥；适检人口门禁（性别/婚否）；医学互斥与预算帽；免费加项津贴 morePayType；标准字典对齐"),
    ("Report 体检报告", "reportId", GREEN,
     "到检出具 → OCR 解析 → 归档 HMES（终态交付）",
     "统一大模型 OCR 管道（废弃私有 JSON）；自主外院报告物理隔离不入档；值对象 AbnormalFinding 内容决定等价性"),
]
for i, (cn, idt, acc, lc, inv) in enumerate(agg):
    x = 0.55 + (i % 3) * 4.18
    y = 2.35 + (i // 3) * 2.12
    box(s, x, y, 3.98, 1.98, "", fill=WHITE, line=acc, lw=1.1, radius=0.05)
    box(s, x, y, 3.98, 0.42, cn, fill=acc, line=None, size=10.5, bold=True, color=WHITE, radius=0.12)
    box(s, x, y + 0.22, 3.98, 0.2, "", fill=acc, line=None, shape=MSO_SHAPE.RECTANGLE)
    tbox(s, x + 0.14, y + 0.48, 3.7, 0.22, "Identity: " + idt, size=7, color=GRAY)
    box(s, x + 0.12, y + 0.72, 3.74, 0.5, lc, fill=PAPER, line=None, size=7, bold=True, color=INK)
    tbox(s, x + 0.14, y + 1.28, 3.7, 0.66, inv, size=7, color=RGBColor(0x3A, 0x46, 0x5C))
box(s, 0.55, 6.62, 12.23, 0.56, [("其余关键实体不变量", 8.5, True, INK),
    ("SubOrder 主干单选互斥 + 积分优先级落标 ｜ Holder 严格 1:1 ｜ Store 交集匹配/屏蔽日/停业策略 ｜ CardVoucher 兑换即锁死 ｜ ConsentRecord 年度团单周期绑定存证", 7.5, False, INK)],
    fill=PAPER, line=None, size=7.5)
page_no(s)

# ---- E3 建模规范与 ToB 免密赋权 ----
s = new_slide()
header(s, "实3", "领域建模规范与 ToB 免密动态赋权", "Modeling Principles & JIT Provisioning", TEAL,
       ["domain-entities", "建模规范", "ToB 免密"], badge_size=13)
decision_bar(s, "充血模型 + 标识不可变 + 聚合边界保护；ToB 免密走「中转页 + 策略模式 + Apollo 动态映射」按需赋权（JIT Provisioning）。",
             TEAL)
tag(s, 0.55, 2.28, "领域建模规范与演进原则", BLUE, size=10.5)
princ = [
    ("① 充血模型 Rich Domain Model", "状态扭转与校验内置实体方法（appointment.cancel() / order.restoreEquity()），禁止 Service setter 篡改"),
    ("② 唯一标识不可变", "实体 ID 创建后全局固定；改期、重试、属性调整均不得生成新实体替代原实体"),
    ("③ 聚合边界保护", "外部访问 SubOrder / ReportInterpretation 等子实体必须经聚合根 Order / Report 操作"),
    ("④ 值对象不可变", "SchedulePeriod / StoreAddress / Money / AbnormalFinding 由属性定义等价性，可互相替换"),
]
y = 2.62
for t, d in princ:
    box(s, 0.55, y, 6.05, 0.62, [(t, 8.5, True, BLUE), (d, 7.2, False, INK)], fill=WHITE, line=BLUE, size=7)
    y += 0.72
tag(s, 0.55, 5.62, "实体 vs 值对象对照（摘录）", TEAL, size=10.5)
tbox(s, 0.55, 5.94, 6.05, 1.0,
     ["实体：Appointment 预约单 / Store 分院 / Order 主订单 —— 有全局唯一标识与完整生命周期",
      "值对象：SchedulePeriod 排期时段 / StoreAddress 分院地址 / Money 金额 / AbnormalFinding 异常指标",
      "—— 内容决定等价性，无独立标识与状态演变，不可变可互换"],
     size=7.5, color=RGBColor(0x3A, 0x46, 0x5C))
tag(s, 6.73, 2.28, "ToB 免密对接 · 中转页 + Apollo 动态权益导入", PURPLE, size=10.5)
jit = [
    ("① 中转页无感过渡", "前端路由 /jump/:projectCode（token / target / channel / openid）：token 暂存 sessionStorage+Cookie，初始化项目上下文后 location.replace 进首页"),
    ("② 策略模式鉴权", "ewp.bizType 配置项目→免密业务策略实现类映射；tokenSurvivalTimeBizType 按渠道设定 Token 生存周期"),
    ("③ Apollo 岗位映射", "ewp.xinfutong.userPost.{projectCode}.{userPost} 字典：岗位 → groupCode / teamOrderCode / 附赠积分 / subGroupCust / 代报销继承标识"),
    ("④ JIT 动态赋权时序", "查 queryEquityByWorkCodeAndTeam：已有权益直接返回 customerCode；未命中则 syncOceanicUserInfo 动态创建 StaffMember 并生成 Benefit（无需前置名单）"),
]
y = 2.62
for t, d in jit:
    box(s, 6.73, y, 6.05, 0.78, [(t, 8.5, True, PURPLE), (d, 7.2, False, INK)], fill=PURPLE_L, line=PURPLE, size=7)
    y += 0.88
box(s, 6.73, 6.2, 6.05, 0.62, [("动态热加载", 8, True, RED),
    ("ApolloPropertiesRefresher 监听机制支持配置动态刷新（无需重启）；benefitRuleConfig 控制权益生成规则", 7.2, False, INK)],
    fill=RED_L, line=RED, size=7)
page_no(s)

# =========================================================
# S2 端到端全景主流程（domain-flows 一）
# =========================================================
s = new_slide()
header(s, "域", "体检业务端到端全景主流程", "End-to-End Master Flow · 7 Stages", TEAL,
       ["domain-flows", "主流程图"], badge_size=15)
decision_bar(s, "单链归属：Benefit（体检权益）➔ Order（主订单，含 0 元统付）➔ Appointment（预约单）；双入口汇流：一体化选购锁单 与 已支付待预约重约。",
             TEAL)

def stage_panel(slide, x, y, w, h, sno, stitle, accent, nodes, arrows_v=True, note=None):
    box(slide, x, y, w, h, "", fill=WHITE, line=RGBColor(0xD8, 0xE0, 0xEC), lw=1.0, radius=0.06)
    box(slide, x, y, w, 0.4, "", fill=accent, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
    box(slide, x, y + 0.2, w, 0.22, "", fill=accent, line=None, shape=MSO_SHAPE.RECTANGLE)
    tbox(slide, x + 0.1, y + 0.03, w - 0.2, 0.34, sno + " " + stitle, size=10, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER)
    ny = y + 0.52
    note_h = 0.3 if note else 0.0
    gapv = 0.12
    bh = (h - 0.58 - note_h - gapv * (len(nodes) - 1)) / len(nodes)
    for i, (txt, fill_, line_, sz) in enumerate(nodes):
        box(slide, x + 0.12, ny, w - 0.24, bh, txt, fill=fill_, line=line_, size=sz)
        if arrows_v and i < len(nodes) - 1:
            arrow(slide, x + w / 2, ny + bh + 0.01, x + w / 2, ny + bh + 0.10, w=1.2)
        ny += bh + gapv
    if note:
        tbox(slide, x + 0.12, y + h - 0.32, w - 0.24, 0.3, note, size=7.5, color=GRAY, align=PP_ALIGN.CENTER)

p1x, p2x, p3x, p4x = 0.55, 3.68, 6.81, 9.94
pw = 2.84
stage_panel(s, p1x, 2.35, pw, 2.25, "①", "顶层配置与权益发放", BLUE, [
    ("Project 企业项目\n(核心端主配置/MIS 补充)", BLUE_L, BLUE, 8.5),
    ("TeamOrder → Group → ProductPackage\n(P 员工包 / G 家属包 + C24·C59)", WHITE, LINE, 7.5),
    ("4 路权益：HR 导入 / 免密 SSO\n卡密兑换 / 自费购买", WHITE, LINE, 7.5),
], note="Benefit 体检权益（有效期/次数门禁）")
stage_panel(s, p2x, 2.35, pw, 2.25, "②", "鉴权与准入门禁", PURPLE, [
    ("白名单/免密登录\n自动绑定 User/Staff/Holder", PURPLE_L, PURPLE, 8.5),
    ("一级合规门禁：隐私与健康信息授权", WHITE, LINE, 8),
    ("商保直赔？→ ClaimApplication\n身份证 OCR+签名 PDF→SFTP 211", WHITE, LINE, 7.5),
], note="拒绝即阻断访问核心功能")
stage_panel(s, p3x, 2.35, pw, 2.25, "③", "智能选检与双向选购", TEAL, [
    ("AI 套餐推荐（问卷/历史报告异步打分）\n& 套餐对比（标准医学字典）", TEAL_L, TEAL, 7.5),
    ("双向选购与硬校验\n选套餐加项 ↔ 选分院排期", WHITE, LINE, 8.5),
    ("适检/互斥/预算帽/交集匹配\n屏蔽日/停业展示策略", WHITE, LINE, 7.5),
], note="推荐可选，失败降级自主选购")
stage_panel(s, p4x, 2.35, pw, 2.25, "④", "结算与主订单确立", GOLD, [
    ("CartItem 加车 → CombinationOrder\n合并结算（瞬态，支付即解体）", GOLD_L, GOLD, 7.5),
    ("积分两阶段冻结（镜像账本）+ 现金\n/ 0 元统付 + 15 分钟排期占容", WHITE, LINE, 7.5),
    ("Order 主订单（单持有人）\n+ SubOrder 明细落标", WHITE, LINE, 8.5),
], note="超时未付：释放占容+解冻积分")
arrow(s, 3.41, 3.5, 3.66, 3.5, w=1.4)
arrow(s, 6.54, 3.5, 6.79, 3.5, w=1.4)
arrow(s, 9.67, 3.5, 9.92, 3.5, w=1.4)

stage_panel(s, 0.55, 4.95, 3.95, 2.1, "⑤", "预约履约与异常变更", TEAL, [
    ("二级合规门禁：企业劳资健康承诺书", WHITE, LINE, 8),
    ("Appointment（主套餐+加项合并原子交付）\n线上直连 API 锁单 02 / 失败 07 ｜线下协调申请", TEAL_L, TEAL, 7),
    ("同店改期 / 取消重约（过期熔断）\n停业降级 / 超期释放 / 级联退款", WHITE, LINE, 7.5),
])
stage_panel(s, 4.72, 4.95, 3.95, 2.1, "⑥", "到检核销、报告与闭环", ORANGE, [
    ("双轨到检同步（已到检 04）\n确立供应商采购结算里程碑", ORANGE_L, ORANGE, 8),
    ("Report PDF → 大模型 OCR 解析\n→ 归档 HMES（外院报告隔离）", WHITE, LINE, 8),
    ("小诺 AI 免登 / C24·C59 解读\n在线客服 / 家庭共用 / HR 看板", WHITE, LINE, 7.5),
])
stage_panel(s, 8.89, 4.95, 3.89, 2.1, "⑦", "并行：报销与积分变现", GREEN, [
    ("体检代报销（与预约互斥 01 / 复检 02）\n双抬头发票 → 全额核准 → 财务打款", GREEN_L, GREEN, 7.5),
    ("积分报销（仅员工本人个人发票）\n三类积分源 1:1 冻结 → 打款回调转实扣", WHITE, LINE, 7.5),
    ("05 付款失败：原单改卡免复审直推", WHITE, LINE, 8),
])
arrow(s, 2.5, 4.62, 2.5, 4.93, w=1.4)
arrow(s, 6.67, 4.62, 6.67, 4.93, w=1.4)
tbox(s, 8.89, 4.62, 3.89, 0.28, "◀ 与 ①② 并行的旁路（不占排期）", size=8, color=GREEN, align=PP_ALIGN.CENTER)
page_no(s)

# =========================================================
# S3 子图1：上游配置、4 路权益发放与准入门禁
# =========================================================
s = new_slide()
header(s, "域1", "上游配置、4 路权益发放与准入门禁", "Config & Benefit Sources · Access Gates", TEAL,
       ["domain-flows", "子图 1", "ADR-011/013/014"], badge_size=13)
decision_bar(s, "核心端为主权威源、MIS 为补充；4 路权益汇入 Benefit 后先过一级隐私授权门禁，商保直赔团单再过理赔前置资料门禁方可进入选检。",
             TEAL)
tag(s, 0.55, 2.2, "上游配置链（1 : N 层级）", BLUE, size=10.5)
cfg = [("Project 企业项目\n长期规则/门户/屏蔽日\n停业策略/加项上限/AI 开关", BLUE_L, BLUE),
       ("TeamOrder 团单\n年度周期/团险保单同步\n理赔标识/承诺书周期", WHITE, LINE),
       ("Group 组别（数据层）\n按部门/职级/批次\n收敛权益范围", WHITE, LINE),
       ("ProductPackage 产品包\n员工包 P / 家属包 G\n分院白名单 / C24·C59", WHITE, LINE),
       ("MedicalPackage 体检套餐\n00 标准/02 升级\n03 加价/01 加项", WHITE, LINE)]
cx = 0.55
for i, (t, f_, l_) in enumerate(cfg):
    box(s, cx, 2.52, 2.32, 0.98, t, fill=f_, line=l_, size=7.5)
    if i < 4:
        arrow(s, cx + 2.34, 3.01, cx + 2.52, 3.01, w=1.2)
    cx += 2.53
tag(s, 0.55, 3.72, "4 路体检权益生成途径", GREEN, size=10.5)
srcs = ["1. HR 批量导入\nImportBatch → StaffMember",
        "2. ToB 免密 SSO 动态导入\n/jump/:projectCode + Apollo 岗位规则",
        "3. 健康商城卡密兑换\ncheckGardPassword 核销即锁死不可退",
        "4. 自费优惠套餐购买\n支付成功直接生成权益与待预约 Order"]
for i, t in enumerate(srcs):
    x = 0.55 + i * 2.53
    box(s, x, 4.04, 2.32, 0.72, t, fill=GREEN_L, line=GREEN, size=7.5)
    arrow(s, x + 1.16, 4.78, 4.0, 5.22, w=1.2)
box(s, 3.05, 5.18, 1.9, 0.56, "Benefit 体检权益\nEFFECTIVE 有效待预约", fill=TEAL, line=None, size=8.5, bold=True, color=WHITE)
arrow(s, 4.97, 5.46, 5.35, 5.46, w=1.3)
box(s, 5.37, 5.18, 1.85, 0.56, "白名单四要素/免密鉴权\n绑定 User+Staff+Holder", fill=WHITE, line=TEAL, size=7.5)
arrow(s, 7.24, 5.46, 7.55, 5.46, w=1.3)
box(s, 7.57, 5.06, 1.62, 0.8, "一级合规门禁\n隐私与健康信息授权", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=7.5)
arrow(s, 9.2, 5.24, 9.5, 5.24, label="同意", lx=0, ly=-0.22, w=1.2)
arrow(s, 8.38, 5.88, 8.38, 6.32, label="拒绝", lx=0.42, ly=-0.06, w=1.2)
box(s, 7.1, 6.32, 2.56, 0.44, "阻断访问核心功能", fill=RED_L, line=RED, size=8.5)
box(s, 9.52, 5.02, 1.72, 0.86, "团单/保单开启\n商保直赔 claimsType?", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=7)
arrow(s, 11.26, 5.22, 11.5, 5.22, label="是", lx=0, ly=-0.22, w=1.2)
arrow(s, 10.38, 5.9, 10.38, 6.32, label="否", lx=0.34, ly=-0.06, w=1.2)
box(s, 9.28, 6.32, 1.95, 0.44, "准入通过 → 选检首页", fill=GREEN_L, line=GREEN, size=8.5)
box(s, 11.45, 4.94, 1.33, 1.0, "理赔前置门禁\n身份证 OCR\n+ 实时手写签名", fill=PURPLE_L, line=PURPLE, size=7)
arrow(s, 11.5, 6.0, 11.5, 6.32, w=1.2)
box(s, 11.25, 6.32, 1.53, 0.44, "合成授权书 PDF\n→ SFTP 归档 211 核心", fill=PURPLE_L, line=PURPLE, size=6)
page_no(s)

# =========================================================
# S4 子图2：智能选检、双向选购与两阶段积分结算
# =========================================================
s = new_slide()
header(s, "域2", "智能选检、双向选购与两阶段积分结算", "Smart Selection & Two-Phase Point Settlement", TEAL,
       ["domain-flows", "子图 2", "ADR-001/003/004/006"], badge_size=13)
decision_bar(s, "推荐仅是可选决策辅助；硬校验五不变量守门；一体化路径经瞬态合单拆单，积分两阶段冻结（外部扣减 + 核心镜像账本）后支付确立。",
             TEAL)
# ---- 上：智能选检 ----
box(s, 0.55, 2.28, 5.7, 2.02, "", fill=PAPER, line=RGBColor(0xD8, 0xE0, 0xEC), lw=0.9, radius=0.06)
tag(s, 0.72, 2.32, "智能选检（可选决策辅助）", PURPLE, size=10)
box(s, 0.72, 2.66, 1.5, 0.66, "推荐入口\n问卷 / 历史报告", fill=WHITE, line=PURPLE, size=8)
arrow(s, 2.24, 2.99, 2.52, 2.99, w=1.2)
box(s, 2.54, 2.66, 1.62, 0.66, "RecommendationRecord\n01-推荐中（异步）", fill=WHITE, line=PURPLE, size=7.5)
arrow(s, 4.18, 2.99, 4.46, 2.99, w=1.2)
box(s, 4.48, 2.6, 1.62, 0.78, "02-完成：分值回填默认勾选\n03-失败：降级自主选购", fill=PURPLE_L, line=PURPLE, size=7.5)
box(s, 0.72, 3.52, 3.35, 0.5, "套餐对比 comparePacket：标准医学字典\n共有项 / 差异项 / 价格实时矩阵", fill=WHITE, line=PURPLE, size=7.5)
box(s, 4.28, 3.52, 1.82, 0.5, "直接选购（无推荐）", fill=WHITE, line=LINE, size=8)
# ---- 上：双向选购与硬校验 ----
box(s, 6.55, 2.28, 6.23, 2.02, "", fill=PAPER, line=RGBColor(0xD8, 0xE0, 0xEC), lw=0.9, radius=0.06)
tag(s, 6.72, 2.32, "双向选购与硬规则校验（5 条业务不变量）", BLUE, size=10)
rules = ["① 适检人口门禁（性别/婚否）", "② 主干单选互斥（00/02/03 选 1）",
         "③ 加项医学互斥 & 预算帽", "④ 套餐门店交集匹配 & 机构私有编码映射", "⑤ 项目屏蔽日 & 分院停业展示策略"]
for i, t in enumerate(rules):
    if i < 4:
        box(s, 6.72 + (i % 2) * 3.05, 2.66 + (i // 2) * 0.38, 2.95, 0.32, t, fill=WHITE, line=LINE, size=7.5)
    else:
        box(s, 6.72, 3.42, 6.0, 0.32, t, fill=WHITE, line=LINE, size=7.5)
tbox(s, 6.72, 3.82, 5.9, 0.26, "路径 A 先选套餐加项→后选分院排期 ｜ 路径 B 先选分院排期→后选套餐加项", size=8, bold=True, color=BLUE)
# ---- 汇流 → PICK ----
box(s, 0.55, 4.56, 1.9, 0.58, "双向选购 PICK\n路径 A / B 汇流", fill=TEAL, line=None, size=8.5, bold=True, color=WHITE)
arrow(s, 2.6, 4.32, 1.9, 4.54, w=1.1)
seg(s, 8.0, 4.32, 8.0, 4.42, color=ARROW, w=1.1)
seg(s, 8.0, 4.42, 2.62, 4.42, color=ARROW, w=1.1)
arrow(s, 2.62, 4.42, 2.49, 4.62, w=1.1)
arrow(s, 2.47, 4.85, 2.71, 4.85, w=1.3)
# ---- 结算主链 Row A ----
box(s, 2.73, 4.52, 1.8, 0.74, "结算与建单路径", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=8)
arrow(s, 4.55, 4.85, 4.77, 4.85, label="一体化", lx=0, ly=-0.24, w=1.2)
box(s, 4.79, 4.56, 2.1, 0.58, "CartItem 草稿不占容\n家属积分共济支付 G 包", fill=WHITE, line=BLUE, size=7.5)
arrow(s, 6.91, 4.85, 7.13, 4.85, w=1.2)
box(s, 7.15, 4.56, 2.3, 0.58, "CombinationOrder 瞬态合单\n按持有人拆为独立 Order（1:1）", fill=WHITE, line=BLUE, size=7.5)
arrow(s, 9.47, 4.85, 9.69, 4.85, w=1.2)
box(s, 9.71, 4.52, 1.3, 0.74, "0 元统付?", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=7.5)
arrow(s, 11.03, 4.85, 11.25, 4.85, label="是", lx=0, ly=-0.22, w=1.1)
box(s, 11.27, 4.56, 1.5, 0.58, "确立 Order\n自动进入预约", fill=GREEN, line=None, size=8, bold=True, color=WHITE)
# ---- Row B：非 0 元路径 + 两段式回流 ----
box(s, 0.55, 5.62, 3.3, 0.62, "已支付待预约 Order（优惠转单 / 取消重约）\n独立选分院排期后直接发起预约", fill=TEAL_L, line=TEAL, size=7.5)
arrow(s, 3.13, 5.26, 3.13, 5.6, label="两段式回流", lx=0.75, ly=-0.05, w=1.1)
box(s, 5.0, 5.62, 2.6, 0.62, "排期临时占容 15 分钟 + 积分预冻结\nShadowLedger 双边镜像（先升级后加项）", fill=WHITE, line=ORANGE, size=7)
arrow(s, 10.36, 5.26, 7.65, 5.75, label="否 · 扣积分/付现金", lx=0.1, ly=-0.22, w=1.1)
arrow(s, 7.62, 5.93, 7.85, 5.93, w=1.1)
box(s, 7.87, 5.54, 1.9, 0.78, "收银台支付结果", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=8)
box(s, 9.95, 5.62, 1.7, 0.62, "超时 / 取消未付\n释放占容 + 解冻积分", fill=RED_L, line=RED, size=7)
arrow(s, 9.79, 6.05, 9.93, 6.05, w=1.1)
arrow(s, 9.77, 5.56, 11.27, 5.05, label="成功 · 转实扣", lx=0.15, ly=-0.2, w=1.1)
# ---- 汇入阶段 5 ----
box(s, 10.9, 6.55, 1.88, 0.5, "进入阶段 5\n预约履约", fill=TEAL, line=None, size=8.5, bold=True, color=WHITE)
seg(s, 12.02, 5.16, 12.02, 6.53, color=ARROW, w=1.1)
arrow(s, 12.02, 6.53, 12.02, 6.55, w=1.1)
seg(s, 2.2, 6.26, 2.2, 6.85, color=ARROW, w=1.1)
arrow(s, 2.2, 6.85, 10.87, 6.85, w=1.1)
tbox(s, 4.3, 6.62, 4.4, 0.24, "支付成功回调：解体合单 / 清理 CartItem / OrderEvent", size=7, color=GRAY)
page_no(s)

# =========================================================
# S5 子图3：预约履约与异常变更
# =========================================================
s = new_slide()
header(s, "域3", "预约履约与异常变更", "Appointment Fulfillment & Exception Handling", TEAL,
       ["domain-flows", "子图 3", "ADR-002/007/008/014"], badge_size=13)
decision_bar(s, "主套餐+全部加项合并为单一 Appointment 原子交付；线上直连即时同步失败落 07，线下协调申请确认；六类变更事件各有明确边界。",
             TEAL)
box(s, 0.55, 2.3, 2.3, 0.56, "待预约 Order\n（主套餐+全部加项）", fill=TEAL_L, line=TEAL, size=8)
arrow(s, 2.87, 2.58, 3.15, 2.58, w=1.2)
box(s, 3.17, 2.24, 1.9, 0.68, "二级合规门禁\n劳资健康承诺书?", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=7.5)
arrow(s, 5.09, 2.44, 5.35, 2.44, label="需签", lx=0, ly=-0.22, w=1.1)
box(s, 5.37, 2.24, 1.95, 0.52, "在线签署 ConsentRecord\n哈希存证 + 邮件 PDF 留档", fill=WHITE, line=GOLD, size=7)
arrow(s, 7.34, 2.5, 7.6, 2.5, w=1.2)
box(s, 7.62, 2.24, 2.15, 0.68, "合并原子履约封装\n单一 Appointment", fill=TEAL, line=None, size=8.5, bold=True, color=WHITE)
# 免签/已签 elbow：G2 下方绕行到 BUNDLE
seg(s, 4.12, 2.94, 4.12, 3.16, color=ARROW, w=1.1)
seg(s, 4.12, 3.16, 8.68, 3.16, color=ARROW, w=1.1)
arrow(s, 8.68, 3.16, 8.68, 2.94, w=1.1)
tbox(s, 5.7, 3.2, 1.8, 0.22, "免签 / 当期已签", size=7, bold=True, color=ARROW, align=PP_ALIGN.CENTER)
arrow(s, 9.79, 2.58, 10.05, 2.58, w=1.2)
box(s, 10.07, 2.24, 1.9, 0.68, "履约类型与排期模式", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=7.5)
# 分流总线
seg(s, 11.02, 2.94, 11.02, 3.62, color=ARROW, w=1.1)
seg(s, 2.63, 3.62, 11.02, 3.62, color=ARROW, w=1.1)
arrow(s, 2.63, 3.62, 2.63, 3.84, w=1.1)
arrow(s, 7.03, 3.62, 7.03, 3.84, w=1.1)
arrow(s, 11.06, 3.62, 11.06, 3.84, w=1.1)
tag(s, 0.55, 3.44, "双轨履约", BLUE, size=10)
box(s, 0.55, 3.86, 4.15, 0.98, [("线上直连供应商（17+ 民营连锁 API）", 8.5, True, BLUE),
    ("实时调用独立适配器锁单：成功 → CONFIRMED(02) / Order APPOINTED / Benefit LOCKED", 7.5, False, INK),
    ("超时/售罄 → 即时落标 FAILED(07)，不异步死循环，提示用户重选", 7.5, False, RED)], fill=BLUE_L, line=BLUE, size=8)
box(s, 4.95, 3.86, 4.15, 0.98, [("线下公立医院 / 特批协调 / 团检报名(0030)", 8.5, True, PURPLE),
    ("PENDING 申请中 → 导出聚合 Excel 名单 → 客服人工对接医院加号", 7.5, False, INK),
    ("医院确认 → CONFIRMED(02)；团检日 GroupCheckDay 专属门店", 7.5, False, INK)], fill=PURPLE_L, line=PURPLE, size=8)
box(s, 9.35, 3.86, 3.43, 0.98, [("回滚补偿（锁单失败/事务回滚）", 8.5, True, RED),
    ("本地事务 AFTER_ROLLBACK 自动调 cancelAppointment 补偿外部锁单，失败发告警邮件", 7.5, False, INK)],
    fill=RED_L, line=RED, size=8)
tag(s, 0.55, 4.98, "CONFIRMED 后的六类履约前变更 / 异常事件", ORANGE, size=10)
ev = [
    ("1. 同店改期", "原分院内改期禁跨店，appointmentCode 不变；体检日当天允许改至后续日期（线下动态刷新 groupCheck）", GREEN_L, GREEN),
    ("2. 主动取消预约", "体检日当天默认禁止取消（保医疗备料），仅引导同店改期；非当日：取消→释放排期→Order 恢复待预约", GOLD_L, GOLD),
    ("3. 权益过期熔断", "取消后 benefitEndTime < Today：严禁再选店预约，锁死福利预算敞口；未过期方可重新预约", RED_L, RED),
    ("4. 分院停业/下线", "不静默退单：降级线下协调模式，客服外呼协助改约至同品牌临近分院", PURPLE_L, PURPLE),
    ("5. 超期未到检", "定时任务按工作日/节假日推算 → OVERDUE_RELEASED 自动释放排期，Order 恢复待预约", BLUE_L, BLUE),
    ("6. 申请退款（自费/混合）", "前置校验并级联取消关联 Appointment → 资金原路退款 → 回调驱动退积分（失败重试超限转人工）→ REFUNDED", ORANGE_L, ORANGE),
]
for i, (t, d, f_, l_) in enumerate(ev):
    x = 0.55 + (i % 3) * 4.18
    y = 5.32 + (i // 3) * 1.02
    box(s, x, y, 3.98, 0.92, [(t, 8.5, True, l_), (d, 7, False, INK)], fill=f_, line=l_, size=7)
page_no(s)

# =========================================================
# S6 子图4：双轨到检核销、报告解读与对账闭环
# =========================================================
s = new_slide()
header(s, "域4", "双轨到检核销、报告解读与对账闭环", "Check-in, Report Ingestion & Interpretation Pipeline", TEAL,
       ["domain-flows", "子图 4", "ADR-008/010/012/016"], badge_size=13)
decision_bar(s, "到检(04) 即确立供应商采购结算里程碑；全域 PDF 统一大模型 OCR 归档 HMES；C24/C59 手动+四条件自动申请并行，小诺 AI 国密免登。",
             TEAL)
box(s, 0.55, 2.3, 1.95, 0.52, "Appointment\nCONFIRMED (02)", fill=TEAL_L, line=TEAL, size=8)
arrow(s, 2.52, 2.56, 2.82, 2.56, w=1.2)
box(s, 2.84, 2.24, 1.75, 0.64, "到检 / 报告回传\n双轨通道", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=7.5)
arrow(s, 4.61, 2.4, 4.95, 2.4, label="线上", lx=0, ly=-0.22, w=1.1)
box(s, 4.97, 2.16, 2.35, 0.52, "定时轮询拉取到检名单+原版 PDF\n（原生 JSON 已弃用）", fill=BLUE_L, line=BLUE, size=7)
seg(s, 3.72, 2.9, 3.72, 3.14, color=ARROW, w=1.1)
arrow(s, 3.72, 3.14, 3.1, 3.3, label="线下", lx=-0.25, ly=0.05, w=1.1)
box(s, 2.0, 3.32, 2.6, 0.52, "MIS 批量导入 Excel\n或单笔核销上传扫描件", fill=PURPLE_L, line=PURPLE, size=7.5)
# MIS -> CHKIN elbow
seg(s, 4.62, 3.58, 4.62, 2.92, color=ARROW, w=1.1)
arrow(s, 4.62, 2.92, 7.68, 2.92, w=1.1)
arrow(s, 7.34, 2.42, 7.7, 2.66, w=1.1)
box(s, 7.72, 2.52, 2.25, 0.56, "CHECKED_IN 已到检(04)\nBenefit CONSUMED", fill=TEAL, line=None, size=8, bold=True, color=WHITE)
arrow(s, 8.85, 3.1, 8.85, 3.38, w=1.1)
box(s, 7.72, 3.38, 2.25, 0.5, "采购结算里程碑：对账核销\n（不等报告/解读）", fill=GREEN_L, line=GREEN, size=7)
box(s, 10.17, 3.38, 2.61, 0.5, "分院口碑评价（自愿）\n仅作选店参考不联动扣款", fill=PAPER, line=LINE, size=7)
arrow(s, 9.99, 2.85, 10.4, 3.36, w=1.1)
arrow(s, 8.85, 3.9, 8.85, 4.18, w=1.1)
box(s, 7.72, 4.18, 2.25, 0.5, "原版 PDF 报告 → 05\nOrder FINISHED", fill=WHITE, line=ORANGE, size=7.5)
arrow(s, 7.7, 4.43, 7.36, 4.43, w=1.1)
box(s, 5.06, 4.18, 2.27, 0.5, "统一大模型 OCR 结构化解析\n抽取检测值与 AbnormalFinding", fill=ORANGE_L, line=ORANGE, size=7)
arrow(s, 5.04, 4.43, 4.7, 4.43, w=1.1)
box(s, 2.35, 4.18, 2.32, 0.5, "归档 HMES 健康档案\n家庭报告共用查看", fill=ORANGE, line=None, size=7.5, bold=True, color=WHITE)
box(s, 0.55, 4.98, 2.05, 0.62, "用户自传外院历史报告\n物理隔离：仅个人查阅\n不入 HMES、不污染趋势", fill=RED_L, line=RED, size=6.2, dash=True)
arrow(s, 2.62, 5.1, 3.2, 4.72, dash=True, w=1.1)
# ---- 增值出口总线 ----
tbox(s, 3.6, 4.92, 6.0, 0.24, "报告归档后的增值出口（解读 / AI / 客服 / HR 看板）", size=8, bold=True, color=GRAY)
seg(s, 3.51, 4.7, 3.51, 5.36, color=ARROW, w=1.1)
seg(s, 3.51, 5.36, 11.86, 5.36, color=ARROW, w=1.1)
arrow(s, 4.55, 5.36, 4.55, 5.62, w=1.1)
arrow(s, 7.35, 5.36, 7.35, 5.62, w=1.1)
arrow(s, 9.75, 5.36, 9.75, 5.62, w=1.1)
arrow(s, 11.86, 5.36, 11.86, 5.62, w=1.1)
box(s, 2.85, 5.64, 3.4, 0.92, [("C24/C59 专业医生解读（工单制）", 8, True, PURPLE),
    ("手动前置门禁 01/02 + 四条件自动申请", 6.8, False, INK),
    ("合并机构+自传报告(≤30 份)→HMC 工单→专科医生核阅→结论回写", 6.8, False, INK)], fill=PURPLE_L, line=PURPLE, size=7)
box(s, 6.4, 5.64, 2.35, 0.92, [("小诺健康 AI 免登", 8, True, BLUE),
    ("多 Agent（解读/心理咨询）", 6.8, False, INK),
    ("pushCustomerInfoFlag 隐私门禁\nSM4+SM3 国密免登", 6.8, False, INK)], fill=BLUE_L, line=BLUE, size=7)
box(s, 8.9, 5.64, 1.85, 0.92, [("保险在线客服免登", 8, True, TEAL),
    ("BGJD 报告解读\nPTZX 普通咨询\nAES-GCM 加密跳转", 6.8, False, INK)], fill=TEAL_L, line=TEAL, size=7)
box(s, 10.9, 5.64, 1.88, 0.92, [("B 端 HR 异常监控看板", 8, True, GREEN),
    ("团队异常分布与解读概况\n脱敏合规\n解读结论永久挂载", 6.8, False, INK)], fill=GREEN_L, line=GREEN, size=7)
page_no(s)

# =========================================================
# S7 子图5：三态联动状态机
# =========================================================
s = new_slide()
header(s, "域5", "Benefit / Order / Appointment 三态联动状态机", "Aggregate State Machines & Cross-Aggregate Events", TEAL,
       ["domain-flows", "子图 5", "状态机"], badge_size=13)
decision_bar(s, "单链模型下三大聚合根各自收敛状态演进；跨聚合事件（预约/到检/取消/退款）驱动联动，任一状态变更可溯源、可回退、可闭环。",
             TEAL)

def state_col(slide, x, w, title, accent, states, y0=2.35):
    ph = 4.42
    box(slide, x, y0, w, ph, "", fill=WHITE, line=RGBColor(0xD8, 0xE0, 0xEC), lw=1.0, radius=0.05)
    box(slide, x, y0, w, 0.42, title, fill=accent, line=None, size=10.5, bold=True, color=WHITE, radius=0.1)
    box(slide, x, y0 + 0.22, w, 0.2, "", fill=accent, line=None, shape=MSO_SHAPE.RECTANGLE)
    y = y0 + 0.56
    gapv = 0.16
    n = len(states)
    hh = (ph - 0.68 - gapv * (n - 1)) / n
    for i, (st, tr, kind) in enumerate(states):
        h = hh
        f_ = {"start": PAPER, "main": WHITE, "hl": accent, "end": PAPER}.get(kind, WHITE)
        l_ = accent if kind in ("main", "hl") else LINE
        c_ = WHITE if kind == "hl" else INK
        box(slide, x + 0.14, y, w - 0.28, h, st, fill=f_, line=l_, size=7.5 if kind != "hl" else 8,
                bold=(kind == "hl"), color=c_)
        if i < n - 1:
            arrow(slide, x + w / 2, y + h + 0.015, x + w / 2, y + h + gapv - 0.02, w=1.0)
        if tr:
            tbox(slide, x + 0.14, y - 0.125, w - 0.28, 0.13, tr, size=5.5, color=GRAY, align=PP_ALIGN.CENTER)
        y += h + gapv
    return y

b_states = [
    ("[*] 导入/免密/卡密/自费购买", "", "start"),
    ("EFFECTIVE 有效待预约", "确认主订单并发起预约 ↓", "hl"),
    ("LOCKED 预约锁定中", "取消/超期释放(未过期)↑ / (已过期)→EXPIRED", "main"),
    ("CONSUMED 已核销闭环", "已到检 04 / 已出报告 05", "main"),
    ("EXPIRED 已过期失效", "超过 benefitEndTime", "main"),
    ("REVOKED 离职减员/退单作废", "HR 减员冻结 / 全额退款核销", "main"),
]
o_states = [
    ("[*] 自费/混合下单（15 分钟占容）", "", "start"),
    ("WAIT_BUYER_PAY 待支付 01", "支付成功回调（积分转实扣）↓ / 超时自动取消", "hl"),
    ("PAID_WAIT_APPOINT 已支付/待预约 02", "发起预约（线上锁单/线下申请）↓", "main"),
    ("APPOINTED 已预约/履约中", "取消/锁单失败 07/超期释放 ↑；到检出报告 ↓", "main"),
    ("FINISHED 已出报告闭环", "到检并出具报告", "main"),
    ("REFUNDED 已退款", "发起退款（回调驱动退积分）/ 级联先取消预约", "main"),
]
a_states = [
    ("[*] 线下协调→PENDING 申请中 01 / 线上锁单→CONFIRMED 02 / 失败 07", "", "start"),
    ("PENDING 申请中/待确认 01", "客服协调医院确认 ↓ / 取消申请 →CANCELLED", "main"),
    ("CONFIRMED 预约成功 02", "同店改期(自环单号不变) / 停业降级→PENDING", "hl"),
    ("CANCELLED 已取消 03", "主动取消（体检日当天默认禁止）", "main"),
    ("OVERDUE_RELEASED 超期释放", "超期未到检定时自动释放", "main"),
    ("CHECKED_IN 已到检 04 → REPORTED 已出报告 05", "双轨同步(触发采购结算) → PDF+OCR 归档", "main"),
    ("FAILED 预约失败 07", "线上锁单超时/售罄即时落标", "main"),
]
state_col(s, 0.55, 3.95, "Benefit 体检权益", BLUE, b_states)
state_col(s, 4.69, 3.95, "Order 主订单（单持有人）", TEAL, o_states)
state_col(s, 8.83, 3.95, "Appointment 预约单（合并原子履约）", PURPLE, a_states)
box(s, 0.55, 6.92, 12.23, 0.42, "", fill=PAPER, line=None, shape=MSO_SHAPE.RECTANGLE)
box(s, 0.55, 6.92, 0.09, 0.42, "", fill=TEAL, line=None, shape=MSO_SHAPE.RECTANGLE)
tbox(s, 0.75, 6.96, 12.0, 0.34,
     "跨聚合联动：预约确认 ⇒ Order APPOINTED + Benefit LOCKED ｜ 取消/超期 ⇒ Order 恢复待预约 + Benefit 释放（过期熔断） ｜ 到检 04 ⇒ Benefit CONSUMED + 采购结算 ｜ 退款 ⇒ 级联取消预约 + 回调退积分",
     size=8, bold=True, color=INK)
page_no(s)

# =========================================================
# S8 子图6：体检代报销与积分报销
# =========================================================
s = new_slide()
header(s, "域6", "体检代报销与积分报销全景", "Medical Reimbursement & Points Reimbursement", TEAL,
       ["domain-flows", "子图 6", "ADR-015"], badge_size=13)
decision_bar(s, "报销不占分院排期，但体检报销(01) 与线上预约在同一 Benefit 下严格互斥；全额核准不部分核减；05 付款失败原单改卡免复审直推。",
             TEAL)
box(s, 0.55, 2.32, 6.05, 4.7, "", fill=WHITE, line=GREEN, lw=1.1, radius=0.05)
box(s, 0.55, 2.32, 6.05, 0.42, "路径 A · 体检代报销 MedicalReimbursement（员工本人与家属）", fill=GREEN, line=None, size=10, bold=True, color=WHITE, radius=0.1)
box(s, 0.55, 2.54, 6.05, 0.2, "", fill=GREEN, line=None, shape=MSO_SHAPE.RECTANGLE)
box(s, 0.72, 2.9, 1.35, 0.56, "报销类型", fill=GREEN_L, line=GREEN, shape=MSO_SHAPE.DIAMOND, size=8)
arrow(s, 2.1, 3.05, 2.4, 3.05, label="01 体检报销", lx=0, ly=-0.24, w=1.1)
box(s, 2.42, 2.84, 1.85, 0.68, "权益互斥门禁\n已有预约/有效报销?", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=7)
arrow(s, 4.3, 3.02, 4.62, 3.02, label="否", lx=0, ly=-0.22, w=1.1)
box(s, 4.64, 2.82, 1.8, 0.72, "提交双抬头发票+凭证\n状态 01-审核中", fill=WHITE, line=GREEN, size=7.5)
box(s, 2.42, 3.62, 1.85, 0.4, "硬阻断：已使用权益", fill=RED_L, line=RED, size=7)
arrow(s, 3.35, 3.54, 3.35, 3.6, w=1.0)
box(s, 0.72, 3.68, 3.55, 0.5, [("02 复检报销：校验独立复检权益 reimburseRecheckCode → 直接进入提交", 6.8, True, GREEN)],
    fill=GREEN_L, line=GREEN, size=6.8, dash=True)
arrow(s, 5.54, 3.56, 5.54, 3.86, w=1.1)
box(s, 4.15, 3.88, 2.8, 0.5, "审核与用户操作", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=8)
arrow(s, 4.13, 4.13, 3.77, 4.13, w=1.0)
seg(s, 3.77, 4.13, 3.77, 4.46, color=ARROW, w=1.0)
box(s, 1.65, 4.46, 2.08, 0.36, "04-已取消 / 06-驳回(终态)", fill=RED_L, line=RED, size=6.8)
arrow(s, 5.54, 4.4, 5.54, 4.66, w=1.1)
box(s, 4.15, 4.68, 2.8, 0.5, "全额通过 → 02-待付款\n(08-寄原件核验后进入)", fill=GREEN_L, line=GREEN, size=7)
arrow(s, 5.54, 5.2, 5.54, 5.48, w=1.1)
box(s, 4.15, 5.5, 2.8, 0.5, "核心财务打款回调", fill=WHITE, line=GREEN, size=8)
arrow(s, 5.25, 6.02, 4.9, 6.28, w=1.0)
arrow(s, 5.95, 6.02, 6.3, 6.28, w=1.0)
box(s, 3.55, 6.28, 1.9, 0.5, "03-已付款（终态）", fill=GREEN, line=None, size=8, bold=True, color=WHITE)
box(s, 5.55, 6.28, 0.95, 0.5, "05-付款失败", fill=RED_L, line=RED, size=7)
seg(s, 6.02, 6.8, 6.02, 6.92, dash=True); seg(s, 6.02, 6.92, 5.2, 6.92, dash=True)
arrow(s, 5.2, 6.92, 5.2, 5.78, dash=True, w=1.0)
tbox(s, 2.6, 6.6, 2.6, 0.26, "05：原单改卡免复审直推 02", size=6.5, color=GRAY)

box(s, 6.73, 2.32, 6.05, 4.7, "", fill=WHITE, line=GOLD, lw=1.1, radius=0.05)
box(s, 6.73, 2.32, 6.05, 0.42, "路径 B · 积分报销 PointsReimbursement（仅员工本人个人发票）", fill=GOLD, line=None, size=10, bold=True, color=WHITE, radius=0.1)
box(s, 6.73, 2.54, 6.05, 0.2, "", fill=GOLD, line=None, shape=MSO_SHAPE.RECTANGLE)
box(s, 6.9, 2.92, 2.55, 0.62, "提交个人健康消费发票\n体检/疫苗/牙科/眼科/健身\n（无原件寄送）", fill=WHITE, line=GOLD, size=7)
arrow(s, 9.47, 3.23, 9.77, 3.23, w=1.1)
box(s, 9.79, 2.92, 2.8, 0.62, "1:1 预冻结积分\n核心/薪福通/福粒三类积分源\n状态 01-审核中", fill=GOLD_L, line=GOLD, size=7)
arrow(s, 11.19, 3.56, 11.19, 3.88, w=1.1)
box(s, 9.9, 3.9, 2.55, 0.5, "审核与用户操作", fill=GOLD_L, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=8)
arrow(s, 9.88, 4.15, 9.3, 4.15, w=1.0)
box(s, 7.6, 3.94, 1.68, 0.42, "撤销/驳回 → 解冻返还\n04/06（终态）", fill=RED_L, line=RED, size=6.5)
arrow(s, 11.19, 4.42, 11.19, 4.7, w=1.1)
box(s, 9.9, 4.72, 2.55, 0.5, "全额通过（不支持部分核减）\n→ 02-待付款", fill=GREEN_L, line=GREEN, size=7)
arrow(s, 11.19, 5.24, 11.19, 5.52, w=1.1)
box(s, 9.9, 5.54, 2.55, 0.5, "核心财务打款回调", fill=WHITE, line=GOLD, size=8)
arrow(s, 10.85, 6.06, 10.5, 6.32, w=1.0)
arrow(s, 11.55, 6.06, 11.95, 6.32, w=1.0)
box(s, 8.75, 6.32, 2.3, 0.5, "03-已付款\n冻结转实扣（终态）", fill=GOLD, line=None, size=7.5, bold=True, color=WHITE)
box(s, 11.2, 6.32, 1.4, 0.5, "05-付款失败\n保持冻结不退回", fill=RED_L, line=RED, size=6.5)
box(s, 6.9, 4.72, 2.45, 1.2, [("报销状态机（两路共用）", 8, True, INK),
    ("01 审核中 → 02 待付款 → 03 已付款", 7, False, INK),
    ("04 已取消 ｜ 06 审核未通过", 7, False, RED),
    ("05 付款失败：原单号不变改卡重推", 7, False, ORANGE),
    ("08 待寄原件：仅代报销公司抬头", 7, False, GRAY)], fill=PAPER, line=LINE, size=7)
page_no(s)

# =========================================================
# S8b 前端业务名词与口径对齐基线
# =========================================================
s = new_slide()
header(s, "端0", "前端业务名词与口径对齐基线", "Frontend Terms & Baseline Alignment", ORANGE,
       ["frontend-flows", "1.x / 4.x", "术语对照"], badge_size=13)
decision_bar(s, "4 处外部文档差异已按代码与 ADR 消解；前台 UI/代码词汇统一映射领域标准术语 —— 新 PRD、评审与后端模型一律使用标准名词。",
             ORANGE)
tag(s, 0.55, 2.28, "口径对齐说明（已消解的 4 处外部文档差异）", RED, size=10.5)
align = [
    ("体检报销与权益关系", "「报销不消耗权益」", "报销不占排期，但体检报销(01) 与线上预约在同一 Benefit 下严格互斥；复检报销(02) 独立共存；积分报销消耗福利积分"),
    ("「福利报销」命名", "「福利报销(KPMG 分支)」", "领域统一术语 = PointsReimbursement（积分报销）；前台「福利报销」/0006/KBX 旧文案仅 UI 兼容"),
    ("订单 / 预约状态码", "订单 09=已退款、预约 01=受理中", "ParamEnum 权威口径：订单 09=待审核/10=审核通过；预约 01=申请成功（线下待人工确认，不可当预约成功）"),
    ("AI 与报告解读体系", "将小诺等同于项目级普惠 AI", "区分 Dify 普惠 AI / 小诺多 Agent 国密免登 / 在线客服(BGJD) / C24·C59 医生解读 / AI 导医 五套体系"),
]
for i, (t, old_, new_) in enumerate(align):
    x = 0.55 + i * 3.1
    box(s, x, 2.62, 2.95, 1.62, [(t, 8.5, True, RED), ("外部说法：" + old_, 6.8, False, GRAY),
        ("权威口径：" + new_, 7, False, INK)], fill=WHITE, line=RED, size=7)
tag(s, 0.55, 4.42, "前台 UI / 代码词汇 ↔ 领域标准术语对照", TEAL, size=10.5)
box(s, 0.55, 4.76, 3.1, 0.32, "前台文案 / 代码字段", fill=TEAL, line=None, size=8, bold=True, color=WHITE)
box(s, 3.67, 4.76, 3.4, 0.32, "领域标准术语", fill=TEAL, line=None, size=8, bold=True, color=WHITE)
box(s, 7.09, 4.76, 5.69, 0.32, "改造注意事项", fill=TEAL, line=None, size=8, bold=True, color=WHITE)
terms_map = [
    ("体检人 checkUpPerson", "Holder（持有人）", "一笔主订单严格 1:1 绑定单一持有人"),
    ("福利报销 / KPMG（0006, KBX）", "Points Reimbursement（积分报销）", "新 PRD 与后端模型统一「积分报销」，仅 UI 兼容老文案"),
    ("体检报销（0005）", "Medical Reimbursement（体检代报销）", "含平级的体检报销(01) 与复检报销(02)"),
    ("团检报名（entryCode=0030）", "Group Checkup Enrollment（团检报名）", "复用标准线下预约单链，不另建独立实体"),
    ("组别 groupCode/groupName", "Group（组别）", "Project→TeamOrder→Group→Benefit，前台文案不露出「组别」"),
    ("容量 remainderVolume", "Schedule Capacity（档期容量）", "与下单 15 分钟占座动作 Capacity Hold 区分"),
    ("appointPeriodSwitch", "Schedule Period（排期时间段开关）", "需门店 supportsTimeSlot 同时满足才展示时段行"),
    ("displayCapacitySwitch 等开关", "项目级功能开关", "解读/外院上传/门店评价/卡密兑换入口显隐由项目配置下发"),
]
y = 5.1
for a, b, c in terms_map:
    box(s, 0.55, y, 3.1, 0.26, a, fill=PAPER, line=LINE, size=6.8)
    box(s, 3.67, y, 3.4, 0.26, b, fill=WHITE, line=LINE, size=6.8, bold=True)
    box(s, 7.09, y, 5.69, 0.26, c, fill=WHITE, line=LINE, size=6.8)
    y += 0.3
page_no(s)

# =========================================================
# S9 前台 · 员工体检五大页面主线
# =========================================================
s = new_slide()
header(s, "端", "前台主线 · 员工体检五大页面流转", "Frontend Main Line · Employee Checkup Pages", ORANGE,
       ["frontend-flows", "2.1 基准主线"], badge_size=13)
decision_bar(s, "页面衔接 3 条硬规则（改造必保）：上一页决定下一页可选范围；改上游必须清空下游；提交卡点通常在前置导航页而非日期页本身。",
             ORANGE)
flow = [
    ("企业项目落地页", "选角色 / 新老流程", BLUE_L, BLUE),
    ("① 导航页", "选权益 + 实名四要素\n+ 三项标的缓存态", WHITE, LINE),
    ("② 套餐页", "主干单选互斥 00/02/03\n+0~N 加项 + AI 推荐/对比", WHITE, LINE),
    ("③ 机构页", "城市→品牌→门店筛选\nVIP/提前天数/评分", WHITE, LINE),
    ("④ 日期页", "日历→时段→报告类型\n领取方式/同意书", WHITE, LINE),
    ("⑤⑥ 二次确认与支付", "积分/微信/支付宝/一网通\n15 分钟占容超时取消", GOLD_L, GOLD),
    ("⑦ 订单详情", "线上直连 vs 线下医院\n双轨预约状态机", WHITE, LINE),
    ("⑧ 体检报告", "列表 / 对比 / 解读", TEAL_L, TEAL),
]
cx = 0.55
for i, (t, d, f_, l_) in enumerate(flow):
    w = 1.4
    box(s, cx, 2.45, w, 1.15, [(t, 8, True, INK), (d, 6.5, False, RGBColor(0x4A, 0x55, 0x6C))], fill=f_, line=l_, size=7)
    if i < len(flow) - 1:
        arrow(s, cx + w + 0.005, 3.02, cx + w + 0.125, 3.02, w=1.2)
    cx += w + 0.13
rules3 = [
    ("规则 1 · 逐级收窄", "套餐 + 全部加项包经设备能力交集收窄机构页门店；机构是否线上直连 + appointPeriodSwitch 决定日期页时段行显隐", BLUE),
    ("规则 2 · 上游变更清空下游", "回导航页换权益/改套餐 → 门店与日期失效；回机构页换门店 → 日期与时段必须重选", ORANGE),
    ("规则 3 · 提交卡点前置定位", "日期页提交不可点，多因权益过期（Equity Expiry Guard）、实名缺项或未支付订单拦截（Pending Order）", RED),
]
for i, (t, d, acc) in enumerate(rules3):
    x = 0.55 + i * 4.18
    box(s, x, 3.95, 3.98, 1.0, [(t, 9.5, True, acc), (d, 7.5, False, INK)], fill=WHITE, line=acc, size=7.5)
tag(s, 0.55, 5.2, "订单中心与扩展模块要点", PURPLE, size=10.5)
mods = [
    ("订单中心 #/record-new/:index", "双页签：购买订单(type 1) / 购物车(type 2)；加车不占容，空车保留底栏 ¥0.00 灰态结算"),
    ("团检报名 entryCode=0030", "入口文案切换「团检报名」，收敛线下白名单门店，日期页仅团检日 groupCheck=Y，到检时间 groupCheckUpTime"),
    ("智能选检扩展", "AI 推荐：沿用上次测评 / 重新测评（8 题问卷或上传报告）；套餐对比 2 套并排 + 仅看差异项；承诺书 11 题 + 手写签名"),
]
for i, (t, d) in enumerate(mods):
    x = 0.55 + i * 4.18
    box(s, x, 5.54, 3.98, 1.0, [(t, 8.5, True, PURPLE), (d, 7.2, False, INK)], fill=PURPLE_L, line=PURPLE, size=7)
page_no(s)

# =========================================================
# S10 前台 · 家属体检与优惠套餐双入口
# =========================================================
s = new_slide()
header(s, "端2", "家属体检隐式上下文 与 优惠套餐双入口", "Family Mode Context & Dual-Entry Purchase", ORANGE,
       ["frontend-flows", "2.2 / 2.3"], badge_size=13)
decision_bar(s, "家属体检复用员工组件但 5 处关键差异 + 3 条隐式规则；优惠套餐购买双入口分水岭在「何时确认体检人」与「门店上下文」。",
             ORANGE)
tag(s, 0.55, 2.28, "家属体检（entryCode=0002 + Vuex flowMode=family）", TEAL, size=10.5)
fam = [
    ("入口与上下文", "entryCode=0002 且必须同步置 Vuex flowMode=family，否则按员工流程取数"),
    ("导航页形态", "顶部家属标签栏 + 权益卡，切标签即切换 Holder 与权益（全部标的重置）"),
    ("缺项拦截", "约 2 秒 toast 提示，跳整页完善信息（非弹窗）"),
    ("结算口径", "家属包 G 企业不统付：自费或员工积分共济"),
    ("门店范围", "受家属产品包与门店白名单约束，通常更少"),
]
y = 2.62
for t, d in fam:
    box(s, 0.55, y, 6.05, 0.52, [(t + "　", 8, True, TEAL), (d, 7.2, False, INK)], fill=WHITE, line=LINE, size=7)
    y += 0.6
box(s, 0.55, 5.66, 6.05, 0.78, [("隐式上下文硬规则", 8.5, True, RED),
    ("① 路由参数与 Vuex flowMode 必须同时成立；② 切换家属标签 = 换持有人+换权益，套餐/门店/日期全部清空", 7.2, False, INK)],
    fill=RED_L, line=RED, size=7)
tag(s, 6.73, 2.28, "优惠套餐购买：体检人前置 vs 后置", GOLD, size=10.5)
buy = [
    ("入口路径", "商品详情「立即购买」→ 前置导航页", "落地页一级页（推荐机构/热门套餐双页签）"),
    ("体检人确认", "进套餐页之前已选定", "日期页才补选，返回回显"),
    ("页面形态", "顺序独立路由，无页签栏", "一级双页签；二级隐藏页签与城市筛选"),
    ("可选套餐", "商品锁定（通常 1 个）仅叠项包", "开放多套餐，先店后包/先包后店"),
]
box(s, 6.73, 2.62, 2.0, 0.36, "维度", fill=GOLD, line=None, size=8, bold=True, color=WHITE)
box(s, 8.75, 2.62, 2.0, 0.36, "体检人前置", fill=GOLD_L, line=GOLD, size=8, bold=True)
box(s, 10.77, 2.62, 2.01, 0.36, "体检人后置", fill=GOLD_L, line=GOLD, size=8, bold=True)
y = 3.02
for t, a, b in buy:
    box(s, 6.73, y, 2.0, 0.5, t, fill=PAPER, line=LINE, size=7.5, bold=True)
    box(s, 8.75, y, 2.0, 0.5, a, fill=WHITE, line=LINE, size=6.8)
    box(s, 10.77, y, 2.01, 0.5, b, fill=WHITE, line=LINE, size=6.8)
    y += 0.58
box(s, 6.73, 5.42, 6.05, 1.02, [("双入口 6 条防踩坑硬规则（摘要）", 8.5, True, RED),
    ("一级/二级分界是门店上下文（ewp_from='choosesStore'）而非路由层级；二级页各有唯一入口；城市选择器随上下文整体隐藏；后置链路前两页不涉体检人；前置链路排序会重建列表上下文；套餐科目表异步加载", 6.8, False, INK)],
    fill=RED_L, line=RED, size=7)
page_no(s)

# =========================================================
# S11 前台 · 报销双通道与订单中心要点
# =========================================================
s = new_slide()
header(s, "端3", "报销双通道页面流转与隐藏约束", "Reimbursement Dual Channel & Hidden Constraints", ORANGE,
       ["frontend-flows", "2.4 / 2.5", "ADR-015"], badge_size=13)
decision_bar(s, "共享「健康服务专区」入口与收款/上传/提交组件，凭 specialProjectCode 分流：0005 体检代报销（4 步）｜0006 积分报销·前台称福利报销（3 步）。",
             ORANGE)
box(s, 0.55, 2.35, 3.9, 2.6, [("体检代报销 0005", 11, True, GREEN),
    ("MedicalReimbursement（体检报销 01 / 复检报销 02）", 7.5, False, GRAY),
    ("对象：员工本人及家属；院外体检/异常复检", 7.5, False, INK),
    ("四步：基本信息 → 收款信息(7 项含证件)", 7.5, False, INK),
    ("→ 影像上传(≤30 个，单个 ≤10M) → 提交成功", 7.5, False, INK),
    ("公司抬头初审后进入 08-寄送原件", 7.5, False, ORANGE),
    ("列表：queryUserReimburseListNew", 7.5, False, GRAY)], fill=GREEN_L, line=GREEN, size=7.5)
box(s, 4.73, 2.35, 3.9, 2.6, [("积分报销 0006（前台「福利报销」）", 11, True, GOLD),
    ("PointsReimbursement（旧称 isKPMG，单号前缀 KBX）", 7.5, False, GRAY),
    ("对象：仅员工本人；个人抬头健康消费", 7.5, False, INK),
    ("三步：收款信息(5 项不含证件)", 7.5, False, INK),
    ("→ 报销信息(积分类目+金额+单张发票) → 提交成功", 7.5, False, INK),
    ("无原件寄送环节", 7.5, False, ORANGE),
    ("列表：queryIntegralReimburseRecord", 7.5, False, GRAY)], fill=GOLD_L, line=GOLD, size=7.5)
box(s, 8.91, 2.35, 3.87, 2.6, [("报销前端 4 条隐藏约束与缺陷", 10, True, RED),
    ("① 详情页强依赖 Vuex expense.twoInfos：直接访问/刷新空白，仅列表「查看详情」写入", 7.2, False, INK),
    ("② H5 报销记录合并展示两套单据：不得按 KBX 前缀互斥过滤", 7.2, False, INK),
    ("③ 05 改卡重推：原单号不变、不解冻积分、免复审直回 02；旧端 mobile 入口条件与 new-mobile 有差异", 7.2, False, INK),
    ("④ 已知缺陷 D4：先选开户城市再选银行名称，只读框不刷新致下一步无响应", 7.2, False, RED)], fill=RED_L, line=RED, size=7)
tag(s, 0.55, 5.2, "报销状态流转（前后端共用码值）", GREEN, size=10.5)
st = [("01 审核中", WHITE), ("02 待付款", GREEN_L), ("03 已付款", GREEN), ("04 已取消", RED_L), ("05 付款失败", RED_L), ("06 审核未通过", RED_L), ("08 待寄原件", GOLD_L)]
cx = 0.55
for i, (t, f_) in enumerate(st):
    c = WHITE if f_ == GREEN else INK
    box(s, cx, 5.56, 1.55, 0.44, t, fill=f_, line=LINE, size=8, bold=True, color=c)
    if i < len(st) - 1:
        arrow(s, cx + 1.57, 5.78, cx + 1.71, 5.78, w=1.0)
    cx += 1.72
tbox(s, 0.55, 6.14, 12.2, 0.3, "关键流转：全额核准不部分核减；05 付款失败 → 原单改卡跳过复审直回 02；积分报销 04/06 原路返还积分、03 回调转实扣（失败自动回滚 02）",
     size=8, color=GRAY)
band(s, "术语对照", ["体检人→Holder", "福利报销→积分报销", "体检报销→体检代报销", "容量→Schedule Capacity",
                    "占座→Capacity Hold", "组别→Group（前台不露出）"], y=6.62)
page_no(s)

# =========================================================
# S12 前后端状态码字典
# =========================================================
s = new_slide()
header(s, "端4", "前后端状态码字典（改造对齐基准）", "Status Code Dictionary · Order / Appointment / Others", ORANGE,
       ["frontend-flows", "3.x", "ParamEnum"], badge_size=13)
decision_bar(s, "铁律：主订单与预约单分属两套独立码值且存在重号（01 订单=待支付，预约=申请成功/受理中）——任何条件判断必须先明确维度。",
             RED)
tag(s, 0.55, 2.32, "主订单 Order（01~10）", BLUE, size=10.5)
order_st = [("01 待支付", "建单未付款，触发重复下单拦截"), ("02 已支付", "到账/0 元统付，持待预约资格"),
            ("03/04 已发货/已收货", "商城实物物流履约态"), ("05 已取消", "释放 15 分钟占容与预冻结积分"),
            ("06/07/08 退款中/成功/失败", "混合退款回调驱动退积分"), ("09/10 待审核/审核通过", "需审核类订单")]
y = 2.66
for c, d in order_st:
    box(s, 0.55, y, 1.95, 0.36, c, fill=BLUE_L, line=BLUE, size=7.5, bold=True)
    box(s, 2.52, y, 4.08, 0.36, d, fill=WHITE, line=LINE, size=7)
    y += 0.44
tag(s, 6.85, 2.32, "预约单 Appointment（01~09）", TEAL, size=10.5)
apt_st = [("01 申请成功", "线下/特批待人工确认（前台或显「受理中」）"), ("02 预约成功", "线上锁单成功或线下确认排期"),
          ("03 取消预约", "释放档期，主单恢复待预约"), ("04 已到检", "确立采购结算里程碑"),
          ("05 已出报告", "履约终态，归档 HMES"), ("06/07 预约中/失败", "07 即时落标（同步失败策略）"),
          ("08/09 改期中/取消中", "变更在途态")]
y = 2.66
for c, d in apt_st:
    box(s, 6.85, y, 1.95, 0.36, c, fill=TEAL_L, line=TEAL, size=7.5, bold=True)
    box(s, 8.82, y, 3.96, 0.36, d, fill=WHITE, line=LINE, size=7)
    y += 0.44
tag(s, 0.55, 5.42, "档期日历不可选 4 类成因（不可混用）", PURPLE, size=10)
cal = [("RestDay 休息日", "机构公休"), ("Notopen 未开放", "尚未放号（约近一月）"),
       ("Aboutt 已约满", "当日容量余量为 0"), ("Blackout Dates", "项目屏蔽日（长假/封网）")]
cx = 0.55
for t, d in cal:
    box(s, cx, 5.76, 2.95, 0.5, [(t, 8, True, PURPLE), (d, 7, False, INK)], fill=PURPLE_L, line=PURPLE, size=7)
    cx += 3.07
tag(s, 0.55, 6.42, "报销单（共用 01~08）", GOLD, size=10)
tbox(s, 2.6, 6.42, 10.2, 0.3, "01 审核中 ｜ 02 待付款（含改卡重推直回）｜ 03 已付款（积分回调转实扣）｜ 04 已取消 ｜ 05 付款失败（改卡免复审）｜ 06 审核未通过 ｜ 08 待寄原件（仅代报销公司抬头）",
     size=7.5, color=INK)
tag(s, 0.55, 6.82, "电子发票（00~05）", TEAL, size=10)
tbox(s, 2.6, 6.82, 10.2, 0.3, "00 开票中 ｜ 01 已开票 ｜ 02 已作废 ｜ 03 开票失败 ｜ 04 红字已开 ｜ 05 未开具 —— 抬头 00 公司（必填税号）/ 01 个人；部分退款禁开票",
     size=7.5, color=INK)
page_no(s)

# =========================================================
# S13 集成 · 下游系统全景拓扑
# =========================================================
s = new_slide()
header(s, "集", "下游系统集成全景拓扑", "Integration Topology · 8 Downstream Systems", PURPLE,
       ["integration-flows", "拓扑图"], badge_size=15)
decision_bar(s, "HMSC 边端服务群 + 调度中心经核心中台网关、RabbitMQ、专线 SFTP 与国密免登网关协同 8 大下游系统；业务流程图不暴露接口，契约收敛于集成层。",
             PURPLE)
box(s, 0.55, 2.35, 3.15, 4.25, "", fill=WHITE, line=TEAL, lw=1.2, radius=0.05)
box(s, 0.55, 2.35, 3.15, 0.4, "HMSC 边端服务群 & 调度中心", fill=TEAL, line=None, size=9.5, bold=True, color=WHITE, radius=0.12)
hmsc = ["hmsc-edge-enterprise 企业体检核心边端", "hmsc-edge-provider 服务商/AI/咨询边端",
        "hmsc-edge-cmb 招行/EPAY 支付边端", "hmsc-edge-support 外部回调接收边端",
        "hmsc-innovate-jobs XXL-Job 轮询补偿"]
y = 2.86
for t in hmsc:
    box(s, 0.72, y, 2.81, 0.46, t, fill=TEAL_L, line=TEAL, size=7.5)
    y += 0.56
box(s, 0.72, 5.72, 2.81, 0.62, "分层约定：业务流程图不暴露 URL / Feign\nMQ 队列 / SFTP 路径", fill=PAPER, line=LINE, size=7, dash=True)
box(s, 4.05, 2.35, 2.3, 1.5, "", fill=WHITE, line=BLUE, lw=1.1, radius=0.06)
box(s, 4.05, 2.35, 2.3, 0.36, "核心代理层", fill=BLUE, line=None, size=9, bold=True, color=WHITE, radius=0.12)
box(s, 4.2, 2.82, 2.0, 0.42, "member-core-health\n/corehealth 统一内部网关", fill=BLUE_L, line=BLUE, size=6.8)
box(s, 4.2, 3.32, 2.0, 0.42, "member-core-sign\n/sign 电子签名服务", fill=BLUE_L, line=BLUE, size=6.8)
box(s, 4.05, 4.15, 2.3, 2.45, [("通道矩阵", 9, True, PURPLE),
    ("Feign HTTP 同步查询/锁单", 7, False, INK), ("RabbitMQ Direct 异步同步", 7, False, INK),
    ("专线 SFTP 理赔归档", 7, False, INK), ("SM4+SM3 / AES-GCM 免登", 7, False, INK),
    ("XXL-Job 轮询与补偿兜底", 7, False, INK), ("异步回调驱动状态闭环", 7, False, INK)],
    fill=PURPLE_L, line=PURPLE, size=7)
down = [
    ("1. HMC 核心系统", "项目/团单/权益/订单/预约/财务报销", BLUE),
    ("2. 积分福利平台 & 支付网关", "核心积分/福粒/薪福通/EPAY", GOLD),
    ("3. 17+ 线上直连体检供应商", "美年/爱康/瑞慈/嘉会等独立 API", TEAL),
    ("4. 大数据推荐 TBDS", "问卷/报告 AI 推荐 & 套餐对比", PURPLE),
    ("5. 211 保险核心", "商保直赔理赔资料 SFTP 归档", ORANGE),
    ("6. 健康档案 HMES & OCR", "大模型 OCR 解析与档案归档", GREEN),
    ("7. 报告解读服务", "Dify 普惠 AI & C24/C59 三方医生", RED),
    ("8. 小诺健康 AI & 保险客服", "国密多 Agent 免登 / AES-GCM 客服", PURPLE),
]
y = 2.35
for t, d, acc in down:
    box(s, 6.75, y, 6.03, 0.52, [(t + "　", 8, True, acc), (d, 7, False, INK)], fill=WHITE, line=acc, size=7)
    y += 0.53
arrow(s, 3.72, 3.1, 4.03, 3.1, label="Feign", lx=0, ly=-0.22, w=1.1)
arrow(s, 3.72, 4.0, 4.03, 4.6, w=1.1)
for i in range(8):
    arrow(s, 6.37, 2.6 + i * 0.53, 6.73, 2.6 + i * 0.53, w=1.0)
arrow(s, 6.75, 6.9, 2.55, 6.9, dash=True, w=1.1)
tbox(s, 3.2, 6.62, 3.6, 0.24, "支付/退款/打款/推荐/取消 异步回调", size=6.8, bold=True, color=ARROW, align=PP_ALIGN.CENTER)
page_no(s)

# =========================================================
# 时序图渲染器（lifeline + message）
# =========================================================
def seq_body(s, participants, messages, phases=None, y_top=2.32, y_bot=7.12):
    n = len(participants)
    x0, x1 = 1.42, 12.78
    bw = min(1.72, (x1 - x0) / n - 0.08)
    gap = ((x1 - x0) - n * bw) / max(n - 1, 1)
    centers = [x0 + bw / 2 + i * (bw + gap) for i in range(n)]
    # ---- y layout: phase strips + message rows ----
    y_cur = y_top + 0.68
    rows = []          # (kind, payload, y)
    n_ph = len(phases) if phases else 0
    step = (y_bot - y_cur - n_ph * 0.38) / max(len(messages), 1)
    step = max(0.185, min(step, 0.32))
    ph_by_start = {}
    if phases:
        for pi, (plabel, pcolor, i0, i1) in enumerate(phases):
            ph_by_start[i0] = (plabel, pcolor, i1, pi)
    ph_spans = []
    for i, msg in enumerate(messages):
        if i in ph_by_start:
            plabel, pcolor, i1, pi = ph_by_start[i]
            rows.append(("phase", (plabel, pcolor), y_cur))
            ph_spans.append([y_cur, y_cur, pcolor])
            y_cur += 0.38
        rows.append(("msg", (i, msg), y_cur + step * 0.5))
        if ph_spans:
            ph_spans[-1][1] = y_cur + step * 0.5
        y_cur += step
    # ---- phase background bands ----
    for (yA, yB, pcolor) in ph_spans:
        tint = RGBColor(min(pcolor[0] + 118, 255), min(pcolor[1] + 118, 255), min(pcolor[2] + 118, 255))
        box(s, 0.55, yA, 12.23, yB - yA + step * 0.55, "", fill=tint, line=None,
            shape=MSO_SHAPE.RECTANGLE)
    # ---- participant headers & lifelines ----
    for (label, acc), cx in zip(participants, centers):
        box(s, cx - bw / 2, y_top, bw, 0.54, label, fill=WHITE, line=acc, lw=1.2, size=7.5, bold=True, color=acc)
    for cx in centers:
        seg(s, cx, y_top + 0.54, cx, y_bot + 0.06, color=LINE, w=1.0, dash=True)
    # ---- phase strips & messages ----
    for kind, payload, y in rows:
        if kind == "phase":
            plabel, pcolor = payload
            box(s, 0.55, y - 0.02, 0.08, 0.22, "", fill=pcolor, line=None, shape=MSO_SHAPE.RECTANGLE)
            tbox(s, 0.7, y - 0.04, 7.6, 0.22, plabel, size=7.5, bold=True, color=pcolor)
            continue
        i, msg = payload
        f, t, text, kind2 = msg
        y0 = y
        tbox(s, 0.52, y0 - 0.105, 0.42, 0.22, f"{i + 1}.", size=6.5, color=GRAY, align=PP_ALIGN.RIGHT)
        if kind2 == "self":
            cx = centers[f]
            seg(s, cx + 0.05, y0 - 0.11, cx + 0.52, y0 - 0.11, color=ARROW, w=1.3)
            seg(s, cx + 0.52, y0 - 0.11, cx + 0.52, y0 + 0.07, color=ARROW, w=1.3)
            arrow(s, cx + 0.52, y0 + 0.07, cx + 0.07, y0 + 0.07, color=ARROW, w=1.3)
            tbox(s, cx + 0.58, y0 - 0.135, min(5.6, 12.78 - cx - 0.6), 0.19, text, size=7, color=INK)
        else:
            xa, xb = centers[f], centers[t]
            dash = (kind2 == "dash")
            col = GRAY if dash else ARROW
            off = 0.07 if xb > xa else -0.07
            arrow(s, xa + off, y0, xb - off, y0, color=col, w=1.4, dash=dash)
            mx = (xa + xb) / 2
            lw_ = min(abs(xb - xa) + 1.35, 6.6)
            tbox(s, mx - lw_ / 2, y0 - 0.225, lw_, 0.2, text, size=7, color=INK, align=PP_ALIGN.CENTER)

def seq_slide(label, title, en, accent, tags, decision, participants, messages, phases=None, page=0):
    s = new_slide()
    header(s, label, title, en, accent, tags, badge_size=13)
    decision_bar(s, decision, accent)
    seq_body(s, participants, messages, phases)
    page_no(s, page)
    return s

# =========================================================
# S14 时序图 1：HMC 核心系统同步链路
# =========================================================
seq_slide("时1", "HMC 核心系统同步链路（配置/权益/占容 + MQ 异步）",
    "Sequence 1 · HMC Core Sync via Feign & RabbitMQ", PURPLE,
    ["integration-flows", "时序 1"],
    "选检前同步 Feign 查询（Hystrix 降级）；下单占容 15 分钟；订单/预约/改期/取消经 RabbitMQ 异步同步 HMC，含增值服务组合单延迟补偿。",
    [("持有人\nPC / H5", TEAL), ("hmsc-edge-\nenterprise", BLUE), ("member-core-health\nIPhysicalExamFeign", BLUE),
     ("RabbitMQ\newp.hmc.hmcsc.*", GOLD), ("HMC 核心系统", PURPLE), ("hmsc-innovate-\njobs", GRAY)],
    [
        (0, 1, "进入项目 / 查询权益与可约套餐", ""),
        (1, 2, "queryProjectConfiguration / queryStaffMemberEffBenefits", ""),
        (2, 4, "读取项目配置与实时有效权益", ""),
        (4, 1, "返回项目规则、团单有效期与产品包", "dash"),
        (0, 1, "双向选检：选套餐 / 门店 / 排期", ""),
        (1, 2, "queryPacketListNew / queryStoreListNew / queryNewScheduleList", ""),
        (2, 1, "交集门店、排期余量、屏蔽日、金额校验结果", "dash"),
        (0, 1, "确认下单 / 提交预约", ""),
        (1, 2, "lockAppointNum 锁定分院当天排期容量 15 分钟", ""),
        (1, 1, "本地事务落库 Order / SubOrder / Appointment，发布领域事件", "self"),
        (1, 3, "Direct 消息 ordersync / appointsync / modifydatesync / ordercancelsync", ""),
        (3, 4, "异步消费落盘主订单/预约单/改期/取消状态", ""),
        (1, 1, "组合特殊单 dealAddPushOrder：仅落 mq_log(type=05)", "self"),
        (5, 1, "AddOrderSyncCompensationHandler 定时补偿 → syncOrderService", "dash"),
        (1, 2, "AFTER_ROLLBACK 释放占容 lockAppointNum", ""),
        (1, 2, "ewpPushRefundStatus 退款状态推送（失败定时补偿）", ""),
    ],
    phases=[("阶段 A · 选检前实时查询与硬校验（同步 Feign，Hystrix 降级）", BLUE, 0, 6),
            ("阶段 B · 下单占容与订单/预约同步（事务 AFTER_COMMIT 异步 MQ，失败即时重试 1 次 + mq_log 留痕）", GREEN, 7, 13),
            ("阶段 C · 回滚释放与退款状态同步", ORANGE, 14, 15)],
    page=15)

# =========================================================
# S15 时序图 2：积分福利平台 & 支付网关
# =========================================================
seq_slide("时2", "积分福利平台 & 支付网关两阶段结算与回调退积分",
    "Sequence 2 · Two-Phase Point Settlement & Callback Refund", PURPLE,
    ["integration-flows", "时序 2", "ADR-004/005/006"],
    "外部扣减/冻结 + 核心镜像账本双边并发；1 积分=1 元、SKU 级穿透；严格「资金退款成功回调驱动退积分」，失败反查终态落补偿表。",
    [("持有人", TEAL), ("hmsc-edge-\nenterprise", BLUE), ("member-core-health\n积分/财务网关", BLUE),
     ("外部积分平台\n福粒 / 薪福通", GOLD), ("hmsc-edge-cmb\n& EPAY", ORANGE), ("hmsc-innovate-\njobs", GRAY)],
    [
        (0, 1, "结算页查看可用积分余额", ""),
        (1, 3, "queryIntegral / getIntegralDetail（核心/福粒/薪福通）", ""),
        (3, 1, "可用积分（严格 1:1 人民币等值）", "dash"),
        (0, 1, "提交合并结算（CombinationOrder 拆单为独立 Order）", ""),
        (1, 1, "按优先级分摊写入 SubOrder：先主干升级/加价，后加项", "self"),
        (1, 2, "buildIntegralOrder（sku_items: partner_sku/quantity/unit_price）", ""),
        (2, 3, "外部平台下单扣减/冻结（timeOut→queryOrderResult 查单）", ""),
        (3, 1, "返回 thirdOrderCode", "dash"),
        (1, 2, "operationIntegral(type=01) 核心镜像账本预冻结", ""),
        (1, 4, "buildPayUrl 跳转收银台 → epayPayNotifyNew 验签回调", ""),
        (1, 1, "积分预冻结转实扣 → 清理 CartItem → 推 OrderEvent", "self"),
        (5, 1, "15 分钟超时：释放占容 + 并发释放外部与核心积分", "dash"),
        (0, 1, "申请退款（级联取消关联 Appointment）→ cmbApplyRefund", ""),
        (4, 1, "资金原路退回成功回调 epayRefundNotifyNew", "dash"),
        (1, 2, "并发退积分：撤销外部订单（异常落 exception_records）+ 释放镜像", ""),
        (5, 1, "CancelFuLiOrderHandler 定时补偿重试（超限告警转人工）", "dash"),
    ],
    phases=[("阶段 A · 积分余额查询", BLUE, 0, 2),
            ("阶段 B · 两阶段预冻结（外部实扣/冻结 + 核心双边镜像账本，SKU 级穿透）", GREEN, 3, 11),
            ("阶段 C · 混合退款：资金退款成功回调驱动退积分", RED, 12, 15)],
    page=16)

# =========================================================
# S16 时序图 3：17+ 线上直连供应商全生命周期
# =========================================================
seq_slide("时3", "17+ 线上直连体检供应商全生命周期链路",
    "Sequence 3 · Online Direct-Connected Suppliers Lifecycle", PURPLE,
    ["integration-flows", "时序 3", "ADR-007/008/012"],
    "合并原子履约 + 即时同步失败策略（07 不异步重试）；同店改期单号不变；XXL-Job 双轨轮询到检(04)与原版 PDF 报告(05)。",
    [("持有人", TEAL), ("hmsc-edge-\nenterprise", BLUE), ("member-core-health\nIAppointmentFeign", BLUE),
     ("供应商 API\n/{type}/* 17+ 适配器", GOLD), ("hmsc-innovate-\njobs", GRAY)],
    [
        (0, 1, "选择分院与就检日期 / 时间段", ""),
        (1, 3, "/{type}/queryScheduleList & queryStoreSchedulePeriod 号源时段", ""),
        (0, 1, "提交预约（主套餐 + 全部加项合并打包）", ""),
        (1, 2, "transformPacketCodeOffline 机构私有套餐编码映射", ""),
        (1, 3, "/{type}/customerAppointment 独立适配器实时锁单", ""),
        (3, 1, "成功→外部预约单号 CONFIRMED(02)；超时/售罄→FAILED(07) 即时落标", "dash"),
        (1, 1, "回滚 AFTER_ROLLBACK 自动 cancelAppointment 补偿（失败告警邮件）", "self"),
        (0, 1, "同店改期（体检日当天允许）→ modifyAppointmentDateV2", ""),
        (0, 1, "主动取消（当天默认禁止）→ cancelAppointment 释放排期", ""),
        (3, 1, "机构侧主动取消回调（如爱康 aiKangNotify）", "dash"),
        (4, 1, "No-show 超期：OVERDUE_RELEASED 恢复待预约", "dash"),
        (4, 1, "轮询到检 UpdateToCheckStateHandler 触发批量轮询", "dash"),
        (1, 3, "queryPhysicalExamStatus / queryAppointmentVid", ""),
        (3, 1, "已到检(04) → CHECKED_IN + Benefit CONSUMED（采购结算里程碑）", "dash"),
        (4, 1, "轮询报告：checkAppointmentReportCreated → downloadAppointmentReport", "dash"),
        (3, 1, "原版 PDF 落地 → REPORTED(05) / Order FINISHED", "dash"),
    ],
    phases=[("阶段 A · 排期查询与实时锁单（合并原子履约）", BLUE, 0, 6),
            ("阶段 B · 同店改期、取消与异常回调", GOLD, 7, 10),
            ("阶段 C · 双轨定时轮询到检(04)与 PDF 报告(05)", GREEN, 11, 15)],
    page=17)

# =========================================================
# S17 时序图 4：TBDS 大数据推荐
# =========================================================
seq_slide("时4", "大数据推荐 TBDS：智能选检推荐与套餐对比",
    "Sequence 4 · TBDS Recommendation & Package Comparison", PURPLE,
    ["integration-flows", "时序 4"],
    "问卷推荐同步返回、报告推荐双阶段异步回调（01 推荐中 → 02 完成 / 03 失败降级自主选购）；套餐对比无状态实时。",
    [("持有人", TEAL), ("hmsc-edge-enterprise\nAiQuestionnaire", BLUE), ("member-core-health\nITbdsFeignClient", BLUE),
     ("大数据推荐\nTBDS", PURPLE), ("hmsc-edge-support\nTbdsController", GREEN)],
    [
        (0, 1, "queryAIQuestionnaire（性别/年龄）请求推荐问卷", ""),
        (1, 3, "/inside/tbds/queryAIQuestionnaire 获取适龄健康风险问卷", ""),
        (0, 1, "提交答卷 queryAIQuestionnaireResult（可复用历史测评）", ""),
        (2, 3, "算法打分匹配主套餐与加项包", ""),
        (3, 0, "AiRecommendPackageResultDTO 自动勾选推荐项", "dash"),
        (0, 1, "上传/引用历史报告 recommendPacket/submitReport", ""),
        (1, 1, "校验姓名/证件号 → RecommendationRecord 01-推荐中", "self"),
        (1, 3, "aiRecommendPackageByReport（候选套餐 + 报告路径）", ""),
        (3, 1, "异步大模型解析任务即时 ACK 受理成功", "dash"),
        (3, 4, "updateReportRecommendedPacketResult 推荐结果回调", ""),
        (4, 1, "回写 02-推荐完成 / 03-推荐失败 与套餐分值", ""),
        (0, 1, "短轮询 queryRecommendResultByReport（03 失败则降级自主选购）", ""),
        (0, 1, "comparePacket / V2 多候选套餐对比", ""),
        (2, 3, "MedicalItem 标准医学字典比对", ""),
        (3, 0, "实时返回共有项 / 差异项 / 价格对比矩阵（无状态）", "dash"),
    ],
    phases=[("场景 A · 健康问卷测评推荐（同步）", BLUE, 0, 4),
            ("场景 B · 历史体检报告异步推荐（双阶段提交 + 异步回调）", GREEN, 5, 11),
            ("场景 C · 无状态套餐对比服务", GOLD, 12, 14)],
    page=18)

# =========================================================
# S18 时序图 5：211 保险核心商保直赔
# =========================================================
seq_slide("时5", "211 保险核心商保直赔与电子签名 SFTP 归档",
    "Sequence 5 · Insurance Claims & E-Sign SFTP Archiving", PURPLE,
    ["integration-flows", "时序 5", "ADR-013"],
    "理赔前置资料门禁：身份证 OCR + 实时手写签名校验，动态盖章合成授权书 PDF，双事件解耦本地落库与专线 SFTP 归档 211 核心。",
    [("持有人\n保单直赔用户", TEAL), ("hmsc-edge-enterprise\nClaimsDataServiceImpl", BLUE),
     ("member-core-sign\nIElectricSignFeign", BLUE), ("本地 / NAS\n文件存储", GRAY), ("211 保险核心\nSFTP", ORANGE)],
    [
        (0, 1, "上传身份证正反面影像（OCR 识别校验）", ""),
        (1, 3, "暂存 ewp/electricSign/temp/{yyyyMMdd}/{cardCode}/", ""),
        (0, 1, "提交实时手写电子签名轨迹 validateElectricSign", ""),
        (1, 2, "signCheck 签名轨迹合法性校验 → 生成 flowId（code=1000）", ""),
        (1, 2, "signWriting 合成电子签名图", ""),
        (0, 1, "确认提交理赔授权 mergeClaimsData", ""),
        (1, 2, "getSignFile 拉取《体检理赔申请授权书 PDF》", ""),
        (1, 3, "持久化保存身份证影像、签名图与理赔 PDF", ""),
        (1, 1, "发布领域事件 ClaimsDataEvent / SwpClaimsDataEvent", "self"),
        (1, 1, "事件① publishClaimsData 本地理赔资料落库", "self"),
        (1, 4, "事件② 清理临时文件 → SftpUtil.uploadLocalFile 专线上传", ""),
        (4, 1, "归档 {ftpPath}/ewp/electricSign/{yyyyMMdd}/{flowId}.pdf", "dash"),
        (1, 1, "上传失败：记录日志告警，待人工/重试补传", "self"),
        (1, 0, "理赔前置门禁放行，进入标准选检预约流程", "dash"),
    ],
    phases=[("理赔前置资料门禁（OCR + 电子签名 + PDF 动态盖章合成）", BLUE, 0, 8),
            ("双事件归档：本地落库 ⊕ 专线 SFTP 归档 211 核心（驱动自动化理赔结案）", GREEN, 9, 13)],
    page=19)

# =========================================================
# S19 时序图 6：报告 OCR / 解读 / 小诺 AI 免登
# =========================================================
seq_slide("时6", "报告 OCR 归档 HMES、C24/C59 解读与小诺 AI 免登",
    "Sequence 6 · Report OCR, Interpretation & XiaoNuo AI SSO", PURPLE,
    ["integration-flows", "时序 6", "ADR-010/016"],
    "全域 PDF 统一大模型 OCR 归档 HMES；解读分手动前置门禁与四条件自动申请；小诺国密免登带 pushCustomerInfoFlag 隐私门禁与 RSA 短效令牌回查。",
    [("持有人 / HR", TEAL), ("hmsc-innovate-\njobs", GRAY), ("hmsc-edge-\nenterprise", BLUE),
     ("member-core-health\nIHmes / IPhysicalExam", BLUE), ("大模型 OCR &\n健康档案 HMES", GREEN),
     ("HMC 托管 C24/C59\n三方医生解读", PURPLE), ("小诺健康 AI /\n保险在线客服", ORANGE)],
    [
        (1, 4, "NotifyCheckReportHandler 分页推送近 3 天 PDF（maxPushNum=2）", ""),
        (4, 4, "统一大模型 OCR 抽取临床指标与 AbnormalFinding", "self"),
        (2, 3, "pushReportToHmes（REPORTED(05) AFTER_COMMIT 触发）", ""),
        (3, 4, "归档官方报告至 HMES（外院历史报告物理隔离不推送）", ""),
        (1, 2, "PushReportToHmesHandler 按日期区间定时兜底补推", "dash"),
        (2, 2, "四条件自动申请门禁 → ReportInterpretationEvent 自动选子产品", "self"),
        (0, 2, "手动申请 interpretEwpReportApply（前置 01/02 门禁）", ""),
        (2, 3, "uploadHmesFile 合并机构+自传报告（≤30 份）归档；扣 remaindCount", ""),
        (2, 5, "HMC 创建/更新解读工单（XXL-Job 兜底补推）→ 专科医生核阅", ""),
        (5, 2, "结构化解读结论异步回写（永久挂载）", "dash"),
        (0, 2, "queryEwpInterpretReportList / Info 查询解读结论", ""),
        (1, 0, "SendInterpretTheReportHrHandler → B 端 HR 异常监控看板", "dash"),
        (0, 2, "小诺免登：getXiaoNuoLoginUrl / TargetUrl（ai/physical|pageType）", ""),
        (2, 2, "pushCustomerInfoFlag 隐私门禁 → SM4+SM3 加密免登 URL", "self"),
        (6, 2, "queryAllReportList 反向回查（RSA 短效 xiaonuologin 令牌）", ""),
        (2, 6, "返回 EWP+SWP 加密报告列表；AES-GCM 在线客服免登(BGJD/PTZX)", "dash"),
    ],
    phases=[("阶段 A · 大模型 OCR 结构化解析与 HMES 官方档案归档", GREEN, 0, 4),
            ("阶段 B · C24/C59 专业医生异步解读（手动 + 四条件自动申请）", PURPLE, 5, 11),
            ("阶段 C · 小诺健康 AI 国密免登、报告双向回查与在线客服", ORANGE, 12, 15)],
    page=20)

# =========================================================
# S20 时序图 7：报销财务推送与回调
# =========================================================
seq_slide("时7", "体检代报销与积分报销：财务推送、回调与改卡重推",
    "Sequence 7 · Reimbursement Finance Push & Retry", PURPLE,
    ["integration-flows", "时序 7", "ADR-015"],
    "权益互斥校验 → MIS 全额审核 → 推送核心财务打款 → 异步回调；05 付款失败原单改卡免复审直推；积分报销两阶段冻结/实扣。",
    [("持有人 / 员工", TEAL), ("MIS 审核后台", GRAY), ("hmsc-edge-\nenterprise", BLUE),
     ("member-core-health\n积分/财务网关", BLUE), ("RabbitMQ\nPushMqDataService", GOLD), ("HMC 核心财务", PURPLE)],
    [
        (0, 2, "addUserReimburseNew 提交个人/公司双抬头发票", ""),
        (2, 2, "ReimburseBenefitCheck：01 与线上预约互斥；02 校验复检权益", "self"),
        (1, 2, "审核：08-待寄原件 → 全额通过 02 | 整体驳回 06（不部分核减）", ""),
        (2, 5, "synReimburseToHmc / MQ 推送 EwpSynReimburseBo 打款", ""),
        (5, 2, "异步回调 updateReimburseStatus（03 已付款 | 05 付款失败）", "dash"),
        (2, 2, "ReimburseTx 事务更新报销单/复检权益流水 + 短信通知", "self"),
        (0, 2, "05 改卡：againSubmitReimburse（原单号改银行卡）", ""),
        (2, 5, "跳过复审直回 02 → pushReimburse 重推核心财务", ""),
        (0, 2, "addIntegralReimburse 积分报销（仅个人发票）", ""),
        (2, 3, "integralOperation(01 预冻结：核心/薪福通/福粒三类积分源)", ""),
        (1, 2, "撤销/驳回 → integralOperation(03) 原路解冻返还", ""),
        (1, 2, "MIS 全额审核通过（不支持部分核减）", ""),
        (2, 5, "synIntegralReimburseToHmc（02-待付款）", ""),
        (5, 2, "回调 updateIntegralReimburseStatus（03 | 05）", "dash"),
        (2, 3, "03→integralOperation(02) 冻结转实扣（失败自动回滚 02）", ""),
        (2, 2, "05→保持积分冻结不退回，改卡免复审重推财务", "self"),
    ],
    phases=[("路径 A · 体检代报销（01 体检报销 / 02 复检报销）", BLUE, 0, 7),
            ("路径 B · 积分报销（仅员工本人个人发票，积分两阶段）", GOLD, 8, 15)],
    page=21)

# =========================================================
# S21 收尾 · 接口契约总表与分层约定
# =========================================================
s = new_slide()
header(s, "尾", "下游核心接口契约总表（摘要）与分层约定", "Interface Contract Matrix · Summary", PURPLE,
       ["integration-flows", "契约总表"], badge_size=15)
decision_bar(s, "所有跨系统接口契约、同步/异步通道、重试与降级策略收敛于集成层；业务流程图保持纯业务语义，三层文档术语严格一致。",
             PURPLE)
rows = [
    ("HMC 核心系统", "Feign + RabbitMQ Direct", "同步查询/占容 + 异步同步 ordersync 等", "Hystrix 降级；mq_log 留痕重试；补偿 Job 兜底"),
    ("积分福利平台", "Feign 双边并发", "扣减/撤销/查单（SKU 级穿透）", "超时查单；exception_records + 定时补偿，超限转人工"),
    ("支付网关 EPAY", "Feign + HTTP 回调", "收银台/退款 + 支付退款回调", "回调验签幂等；退款回调驱动退积分；15 分钟释放"),
    ("17+ 直连供应商", "Feign /{type}/* 适配器", "实时锁单/改期/取消 + 轮询到检报告", "即时同步失败 07；回滚补偿；XXL-Job 双轨轮询"),
    ("TBDS 大数据推荐", "Feign + HTTP 回调", "问卷同步 + 报告异步推荐 + 对比", "推荐失败落 03 平滑降级自主选购"),
    ("211 保险核心", "电子签名 Feign + SFTP", "签章合成 PDF + 专线归档", "签章失败硬阻断；SFTP 异常告警补传"),
    ("HMES & 大模型 OCR", "Feign + XXL-Job", "pushReportToHmes / 分页推 OCR", "OCR 重试 2 次；按区间补推；外院报告隔离"),
    ("解读 / 小诺 / 客服", "Feign/SSE + 国密免登", "工单异步 + SM4/SM3 免登 + RSA 回查", "隐私门禁四要素；短效令牌控权；Job 兜底补推"),
]
box(s, 0.55, 2.35, 2.35, 0.38, "下游系统", fill=PURPLE, line=None, size=9, bold=True, color=WHITE)
box(s, 2.95, 2.35, 2.55, 0.38, "协议与通道", fill=PURPLE, line=None, size=9, bold=True, color=WHITE)
box(s, 5.55, 2.35, 3.5, 0.38, "核心接口 / 模式", fill=PURPLE, line=None, size=9, bold=True, color=WHITE)
box(s, 9.1, 2.35, 3.68, 0.38, "失败重试与降级策略", fill=PURPLE, line=None, size=9, bold=True, color=WHITE)
y = 2.78
for i, (a, b, c, d) in enumerate(rows):
    f_ = WHITE if i % 2 == 0 else PAPER
    box(s, 0.55, y, 2.35, 0.46, a, fill=f_, line=LINE, size=7.5, bold=True)
    box(s, 2.95, y, 2.55, 0.46, b, fill=f_, line=LINE, size=7)
    box(s, 5.55, y, 3.5, 0.46, c, fill=f_, line=LINE, size=7)
    box(s, 9.1, y, 3.68, 0.46, d, fill=f_, line=LINE, size=7)
    y += 0.53
box(s, 0.55, 6.98, 12.23, 0.42, "", fill=PAPER, line=None, shape=MSO_SHAPE.RECTANGLE)
box(s, 0.55, 6.98, 0.09, 0.42, "", fill=PURPLE, line=None, shape=MSO_SHAPE.RECTANGLE)
tbox(s, 0.75, 7.02, 12.0, 0.34,
     "配套材料：domain-flows.md（7 图）｜ frontend-flows.md（5 主线 + 状态码）｜ integration-flows.md（拓扑 + 7 时序）｜ ADR-0001~0016 —— 本 PPT 全部图形为原生形状，可直接编辑",
     size=8, bold=True, color=INK)
page_no(s)

# ---------------- save ----------------
OUT = "/home/user/learning/体检系统HMSC-业务与集成流程图.pptx"
prs.save(OUT)
print("saved:", OUT, "slides:", len(prs.slides._sldIdLst))
