#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
体检平台 HMSC · 架构决策与核心流程 PPT 生成器
基于 ADR 0001~0011，用 python-pptx 原生形状绘制流程图（16:9）。
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE as MSO_LINE
from pptx.oxml.ns import qn

# ---------------- palette ----------------
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

def panel(slide, x, y, w, h, fill=PAPER):
    return box(slide, x, y, w, h, "", fill=fill, line=RGBColor(0xDD, 0xE5, 0xF0), lw=0.75,
               shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)

def page_no(slide, n):
    tbox(slide, 12.35, 7.08, 0.85, 0.3, f"{n:02d}", size=9, color=GRAY, align=PP_ALIGN.RIGHT)

def header(slide, num, title, en, accent, tags, badge_size=19):
    box(slide, 0.55, 0.36, 0.68, 0.68, num, fill=accent, line=None, size=badge_size, bold=True,
        color=WHITE, radius=0.22)
    tbox(slide, 1.42, 0.28, 8.6, 0.55, title, size=23, bold=True, color=INK)
    tbox(slide, 1.44, 0.86, 8.6, 0.3, en, size=10.5, color=GRAY)
    # right-aligned tag chips
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
tbox(s, 0.75, 0.6, 8.0, 0.35, "HMSC · 企业健康体检平台", size=13, bold=True, color=RGBColor(0x8F, 0xB4, 0xE3))
tbox(s, 0.75, 1.75, 12.0, 1.05, "体检平台架构决策与核心流程", size=38, bold=True, color=WHITE)
tbox(s, 0.78, 2.85, 12.0, 0.45, "统一语言词表 × 11 项关键机制决策 × 端到端流程全景",
     size=15, color=RGBColor(0x9F, 0xC3, 0xE8))
seg(s, 0.8, 3.55, 6.2, 3.55, color=TEAL, w=2.5)
# 价值链小流程
cover_steps = ["商城 / 卡券", "权益", "下单", "支付", "预约", "到检", "报告", "增值解读"]
cx, cw, gap = 0.75, 1.28, 0.24
for i, t in enumerate(cover_steps):
    box(s, cx, 5.15, cw, 0.62, t, fill=None, line=RGBColor(0x5F, 0x7F, 0xA6), size=10.5,
        bold=True, color=RGBColor(0xCF, 0xE0, 0xF5), radius=0.24)
    if i < len(cover_steps) - 1:
        arrow(s, cx + cw + 0.02, 5.46, cx + cw + gap - 0.02, 5.46,
              color=RGBColor(0x5F, 0x7F, 0xA6), w=1.4)
    cx += cw + gap
tbox(s, 0.78, 6.75, 9.0, 0.3, "需求评审版 · 2026-10", size=10.5, color=RGBColor(0x7C, 0x93, 0xB8))

# =========================================================
# 统一语言 · 术语表（共 59 词条，7 组）
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
    page_no(s, glossary_slide._n)
    glossary_slide._n += 1
    return s

# ---- G0 总览 ----
s = new_slide()
header(s, "词", "建立统一语言 · 体检业务核心域名词表", "Ubiquitous Language · 59 Terms in 7 Groups",
       BLUE, ["统一语言", "59 词条", "7 组"], badge_size=15)
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
tbox(s, 0.55, 5.95, 12.2, 0.3, "配套阅读：P13 – P23 · 11 项架构决策流程图详解（词条与决策机制一一呼应）",
     size=9.5, color=GRAY)
# 主链路小流程
steps = ["权益", "选购", "建单", "支付", "预约", "到检", "报告", "解读"]
cx, cw2, step2 = 0.6, 1.58, 1.51
for i, t in enumerate(steps):
    box(s, cx, 6.45, cw2, 0.5, t, fill=[BLUE, PURPLE, TEAL, BLUE, TEAL, TEAL, ORANGE, PURPLE][i],
        line=None, shape=MSO_SHAPE.CHEVRON, size=9.5, bold=True, color=WHITE)
    cx += step2
page_no(s, 2)

# ---- G1 权益与交易 ----
glossary_slide._n = 3
s = glossary_slide("词1", "权益与交易", "Entitlements", BLUE,
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
s = glossary_slide("词2", "机构、门店与预约", "Supplier, Store & Appointment", TEAL,
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
s = glossary_slide("词3", "履约规则与边界", "Fulfillment Rules & Boundaries", GREEN,
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
s = glossary_slide("词4", "报告同步与档案", "Reporting & Health Record", ORANGE,
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
s = glossary_slide("词5", "解读增值服务", "Interpretation Value-Added Services", PURPLE,
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
s = glossary_slide("词6", "购物车与合并结算", "Cart & Aggregate Checkout", GREEN,
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
s = glossary_slide("词7", "积分与福利结算", "Points & Welfare Settlement", GOLD,
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
s = glossary_slide("词8", "套餐与项目模型", "Packages, Items & Customization", PURPLE,
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
s = glossary_slide("词9", "健康商城与卡券", "Health Shop & Vouchers", TEAL,
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
# S1 全景导航
# =========================================================
s = new_slide()
tbox(s, 0.55, 0.32, 9.0, 0.55, "11 项决策全景导航", size=23, bold=True, color=INK)
tbox(s, 0.57, 0.9, 9.0, 0.3, "ADR Map · 每张卡片对应一张流程图详解页", size=10.5, color=GRAY)
seg(s, 0.55, 1.32, 12.78, 1.32, color=RGBColor(0xD8, 0xE0, 0xEC), w=1.0)

cards = [
    ("01", "单一持有人", "下单拆单 → 1 人 1 单 → 独立闭环", TEAL),
    ("02", "双轨取消退款", "先取消后退款 ／ 退款级联取消预约", TEAL),
    ("07", "排期与改期边界", "同店改期 · 当天禁退可改 · 超期释放", TEAL),
    ("08", "合并履约与权益门禁", "主套餐+加项原子交付 · 到期拦截", TEAL),
    ("03", "组合订单瞬态包装", "合单收银 → 支付后解体为主订单", BLUE),
    ("04", "积分抵扣分摊", "1:1 等值 → 先升舱后加项 → 落子单", BLUE),
    ("05", "回调驱动退积分", "资金退款回调 → 释放下游积分", BLUE),
    ("06", "双账本镜像对账", "并发双冻结 → SKU 穿透 → 双释放", BLUE),
    ("09", "套餐层级与智能推荐", "单选互斥 · 差额升舱 · 问卷推荐", PURPLE),
    ("11", "商城分类与卡券兑换", "千企千面橱窗 · 卡密生成权益", PURPLE),
    ("10", "报告解读增值流水线", "LLM OCR → AI / 医生双轨解读", ORANGE),
]
xs = [0.55, 3.64, 6.73, 9.82]
ys = [1.55, 3.22, 4.89]
CW, CH = 2.91, 1.52
for i, (num, title, flow, acc) in enumerate(cards):
    x, y = xs[i % 4], ys[i // 4]
    box(s, x, y, CW, CH, "", fill=WHITE, line=RGBColor(0xD8, 0xE0, 0xEC), lw=1.0, radius=0.08)
    box(s, x, y, CW, 0.07, "", fill=acc, line=None, shape=MSO_SHAPE.RECTANGLE)
    tbox(s, x + 0.16, y + 0.14, 0.62, 0.34, num, size=14, bold=True, color=acc)
    tbox(s, x + 0.72, y + 0.16, CW - 0.85, 0.34, title, size=11.5, bold=True, color=INK)
    tbox(s, x + 0.18, y + 0.62, CW - 0.32, 0.78, flow, size=9, color=RGBColor(0x4A, 0x55, 0x6C))
# 图例卡
x, y = xs[3], ys[2]
box(s, x, y, CW, CH, "", fill=PAPER, line=RGBColor(0xD8, 0xE0, 0xEC), lw=1.0, radius=0.08)
tbox(s, x + 0.16, y + 0.12, 2.4, 0.3, "流程图图例", size=11, bold=True, color=INK)
legend = [("圆角框 = 动作 / 系统处理", BLUE), ("菱形 = 判断分支", GOLD),
          ("绿色 = 结果闭环", GREEN), ("红色 = 拦截 / 风险", RED)]
ly = y + 0.46
for txt, c in legend:
    box(s, x + 0.2, ly + 0.05, 0.18, 0.18, "", fill=c, line=None, shape=MSO_SHAPE.OVAL)
    tbox(s, x + 0.46, ly, 2.4, 0.28, txt, size=9, color=RGBColor(0x4A, 0x55, 0x6C))
    ly += 0.27
# 底部价值链
steps = ["权益获取", "选购", "建单", "混合支付", "预约履约", "到检", "报告", "增值解读"]
cx, cw, step = 0.6, 1.58, 1.51
for i, t in enumerate(steps):
    box(s, cx, 6.62, cw, 0.56, t, fill=BLUE if i < 7 else PURPLE, line=None,
        shape=MSO_SHAPE.CHEVRON, size=10, bold=True, color=WHITE)
    cx += step
page_no(s, 12)

# =========================================================
# 通用内容页构建器
# =========================================================
def content_slide(num, title, en, accent, tags, decision, bg_chips, eff_chips=None):
    s = new_slide()
    header(s, num, title, en, accent, tags)
    decision_bar(s, decision, accent)
    footer_chips = bg_chips if not eff_chips else None
    if eff_chips:
        band(s, "背景与权衡", bg_chips, y=6.32)
        band(s, "效果与影响", eff_chips, y=6.86)
    else:
        band(s, "背景与权衡", bg_chips, y=6.52)
    return s

# =========================================================
# S2 决策01 单一持有人
# =========================================================
s = content_slide("01", "单笔体检订单仅绑定单一持有人", "Single Holder per Order", TEAL,
    ["订单域", "强约束", "拆单"],
    "一笔主订单仅对应一个体检人；多人购买在下单时拆分为多笔独立主订单，预约、改期、取消与退款各自全生命周期独立流转。",
    ["早期家庭套餐：1 单多体检人", "部分取消/退款 → 主单状态难收敛", "爱康/美年等回传无法整单原子闭环", "部分退款与财务对账逻辑分裂"])
b1 = box(s, 0.6, 2.5, 1.95, 1.0, "购买家庭套餐\n或多人批量购买", fill=BLUE_L, line=BLUE, size=10.5)
b2 = box(s, 2.95, 2.5, 2.15, 1.0, "下单引擎自动拆单\n1 个体检人 → 1 笔主订单", fill=WHITE, line=BLUE, size=10.5)
b3 = box(s, 5.5, 2.5, 2.35, 1.0, "主订单 ↔ 持有人\n严格 1 : 1", fill=TEAL, line=None, size=13, bold=True, color=WHITE)
b4 = box(s, 8.25, 2.5, 2.1, 1.0, "N 笔独立主订单\n（各绑一张预约单）", fill=PURPLE_L, line=PURPLE, size=10.5)
arrow(s, 2.57, 3.0, 2.93, 3.0); arrow(s, 5.12, 3.0, 5.48, 3.0); arrow(s, 7.87, 3.0, 8.23, 3.0)
arrow(s, 9.3, 3.52, 9.3, 4.28)
box(s, 6.85, 4.32, 4.95, 0.85, [("预约 / 改期 / 取消 / 到检 / 退款", 11, True, GREEN), ("每单独立闭环 · 互不阻塞 · 状态可收敛", 9.5, False, INK)],
    fill=GREEN_L, line=GREEN, size=10)
box(s, 0.6, 4.32, 5.75, 0.85, [("反例：若 1 单多持有人", 10, True, RED),
    ("部分人取消/改期 → 主单状态无法收敛，供应商回传无法整单闭环", 9.5, False, INK)],
    fill=RED_L, line=RED, size=9.5, dash=True)
tbox(s, 6.85, 5.35, 4.95, 0.4, "多人员体检（家庭套餐 / 批量购买）在下单时直接拆单", size=9.5, color=GRAY)
tbox(s, 0.6, 5.35, 5.75, 0.4, "数据库 MEMBER_EWP_ORDER_HOLDER 物理可 1:N —— 业务上锁死 1:1", size=9.5, color=GRAY)
page_no(s, 13)

# =========================================================
# S3 决策02 双轨取消退款
# =========================================================
s = content_slide("02", "预约取消与退款的双轨联动", "Dual-Path Refund & Appointment Cancellation", TEAL,
    ["订单域 × 预约单域", "级联编排"],
    "支持「先取消预约、后续再退款」与「直接退款、系统自动级联取消预约」两条路径，确保外部机构档期释放与退款闭环。",
    ["预约成功即同步外部供应商（爱康/美年/瑞慈/中科）锁定排期", "用户心智①：仅改计划、保留权益", "用户心智②：一键退单退钱"])
tag(s, 0.6, 2.2, "路径一 · 先取消预约，后申请退款（分步独立）", TEAL, size=11)
b1 = box(s, 0.6, 2.55, 1.45, 0.85, "用户\n取消预约", fill=TEAL_L, line=TEAL, size=10)
b2 = box(s, 2.4, 2.55, 1.8, 0.85, "取消预约接口\n释放分院排期", fill=WHITE, line=TEAL, size=10)
b3 = box(s, 4.55, 2.55, 1.5, 0.85, "预约单\n03 已取消", fill=WHITE, line=TEAL, size=10)
b4 = box(s, 6.4, 2.55, 2.05, 0.85, "主单维持 02 待预约\n体检权益完好保留", fill=WHITE, line=TEAL, size=10)
arrow(s, 2.07, 2.98, 2.38, 2.98); arrow(s, 4.22, 2.98, 4.53, 2.98); arrow(s, 6.07, 2.98, 6.38, 2.98)
bb1 = box(s, 8.95, 2.28, 2.6, 0.6, "可随时重新预约（权益保留）", fill=GREEN_L, line=GREEN, size=9.5, dash=True)
bb2 = box(s, 8.95, 3.12, 2.6, 0.6, "再发起申请退款 → 06/07 闭环", fill=WHITE, line=TEAL, size=9.5)
arrow(s, 8.47, 2.85, 8.93, 2.6); arrow(s, 8.47, 3.1, 8.93, 3.4)
tag(s, 0.6, 4.2, "路径二 · 直接申请退款，系统级联取消预约（一键）", ORANGE, size=11)
c1 = box(s, 0.6, 4.55, 1.65, 0.85, "用户直接\n申请退款", fill=ORANGE_L, line=ORANGE, size=10)
c2 = box(s, 2.6, 4.55, 1.8, 0.85, "检测关联\n预约单状态", fill=WHITE, line=ORANGE, size=10)
d1 = box(s, 4.75, 4.45, 1.6, 1.05, "预约单是否\n已取消?", fill=WHITE, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=9.5)
c3 = box(s, 6.7, 4.55, 2.45, 0.85, "自动编排 cancelOrderAppoint\n释放外部机构排期", fill=WHITE, line=ORANGE, size=9.5)
c4 = box(s, 9.5, 4.55, 1.85, 0.85, "推进主单退款\n06 退款中 / 07 成功", fill=WHITE, line=ORANGE, size=9.5)
c5 = box(s, 11.6, 4.55, 1.18, 0.85, "一键同步\n闭环", fill=GREEN, line=None, size=10, bold=True, color=WHITE)
arrow(s, 2.27, 4.98, 2.58, 4.98); arrow(s, 4.42, 4.98, 4.73, 4.98)
arrow(s, 6.37, 4.9, 6.68, 4.9, label="否 · 未取消", lx=0.12, ly=-0.24)
arrow(s, 9.17, 4.98, 9.48, 4.98); arrow(s, 11.37, 4.98, 11.58, 4.98)
seg(s, 5.55, 5.52, 5.55, 5.95); arrow(s, 5.55, 5.95, 10.42, 5.95)
seg(s, 10.42, 5.95, 10.42, 5.42)
tbox(s, 5.72, 5.6, 1.6, 0.3, "是 · 已取消", size=8.5, bold=True, color=ARROW)
page_no(s, 14)

# =========================================================
# S4 决策03 组合订单瞬态
# =========================================================
s = content_slide("03", "组合订单：支付瞬态包装器", "Combination Order as Ephemeral Payment Wrapper", BLUE,
    ["订单域 × 商城", "收银台", "15 分钟超时"],
    "组合订单仅在支付结算期内存在：聚合多笔主订单一次性扣款，支付成功即刻解体，不承担任何履约与售后职责。",
    ["员工为多位家属合单合并付款", "长生命周期大单 → 状态爆炸", "购物车项仅支付回调后物理清理（DELETE）"])
stages = ["购物车", "下单", "收银台", "回调", "支付后"]
sx = [0.6, 3.11, 5.62, 8.13, 10.64]
for t, x in zip(stages, sx):
    box(s, x + 0.55, 2.22, 1.05, 0.3, t, fill=BLUE_L, line=None, size=9, bold=True, color=BLUE, radius=0.5)
m1 = box(s, 0.6, 2.62, 2.14, 1.05, "购物车暂存\n多持有人合单\n不占名额", fill=WHITE, line=BLUE, size=9.5)
m2 = box(s, 3.11, 2.62, 2.14, 1.05, "生成组合订单\ncombinationOrderCode\n触发临时占容", fill=WHITE, line=BLUE, size=9.5)
m3 = box(s, 5.62, 2.62, 2.14, 1.05, "聚合应付金额\n三方网关合并扣款\n招行 / 微信 / 支付宝", fill=WHITE, line=BLUE, size=9.5)
m4 = box(s, 8.13, 2.62, 2.14, 1.05, "支付成功回调", fill=BLUE, line=None, size=11.5, bold=True, color=WHITE)
m5 = box(s, 10.64, 2.62, 2.14, 1.05, "组合订单解体 → N 笔独立主订单\nDELETE 购物车项", fill=GREEN_L, line=GREEN, size=9.5)
for i in range(4):
    arrow(s, sx[i] + 2.16, 3.15, sx[i + 1] - 0.02, 3.15)
arrow(s, 1.67, 3.69, 1.67, 4.62, dash=True)
tag(s, 0.6, 4.28, "异常分支 · 15 分钟未支付", RED, size=10.5)
k1 = box(s, 0.6, 4.62, 2.6, 0.75, "定时任务自动取消\n待支付订单", fill=WHITE, line=RED, size=9.5)
k2 = box(s, 3.55, 4.62, 2.2, 0.75, "释放分院\n排期容量", fill=WHITE, line=RED, size=9.5)
k3 = box(s, 6.1, 4.62, 2.2, 0.75, "对应项回退\n用户购物车", fill=WHITE, line=RED, size=9.5)
arrow(s, 3.22, 5.0, 3.53, 5.0); arrow(s, 5.77, 5.0, 6.08, 5.0)
box(s, 8.75, 4.62, 4.03, 0.75, [("用户端「我的订单」/ 后台管理", 9.5, True, INK),
    ("仅呈现解体后的 N 笔主订单，各显各人、各持预约单", 9, False, INK)],
    fill=PAPER, line=None, size=9.5)
page_no(s, 15)

# =========================================================
# S5 决策04 积分抵扣与子订单分摊
# =========================================================
s = content_slide("04", "积分抵扣与子订单分摊落标", "Point Deduction & SubOrder Allocation", BLUE,
    ["结算引擎", "1 : 1 等值", "先套餐后加项"],
    "锁死 1 积分 = 1 元；积分先抵主套餐升舱/加价差额，再抵自选加项；积分与现金精确分摊落标到每个子订单。",
    ["浮动兑换比例 → 对账与开票争议", "主单笼统记账 → 退订/拆票无法溯源", "支持 100% 全额积分抵扣"])
r1 = box(s, 0.6, 2.42, 2.6, 0.72, "1 积分 = 1 元 绝对等值\n忽略后台浮动比例配置", fill=GOLD_L, line=GOLD, size=9.5)
r2 = box(s, 0.6, 3.42, 2.6, 0.72, "packageIntegralLimit=01\n支持 100% 全额抵扣", fill=GOLD_L, line=GOLD, size=9.5)
r3 = box(s, 0.6, 4.42, 2.6, 0.72, "不设强制自费比例门槛", fill=GOLD_L, line=GOLD, size=9.5)
seg(s, 1.9, 3.14, 1.9, 3.42, color=GOLD, w=1.2, dash=True)
seg(s, 1.9, 4.14, 1.9, 4.42, color=GOLD, w=1.2, dash=True)
tag(s, 3.6, 2.14, "法定抵扣优先级", ORANGE, size=10.5)
p1 = box(s, 3.6, 2.48, 3.1, 0.66, "混合应付（现金 + 积分）", fill=WHITE, line=ORANGE, size=10)
p2 = box(s, 3.6, 3.4, 3.1, 0.66, "① 抵扣主套餐升级 / 加价差额（02/03）", fill=ORANGE_L, line=ORANGE, size=9.5)
p3 = box(s, 3.6, 4.32, 3.1, 0.66, "② 剩余积分抵扣自选加项包（01）", fill=ORANGE_L, line=ORANGE, size=9.5)
p4 = box(s, 3.6, 5.24, 3.1, 0.66, "余额现金 payCurrencyValue 补足", fill=WHITE, line=ORANGE, size=9.5)
arrow(s, 5.15, 3.14, 5.15, 3.38); arrow(s, 5.15, 4.06, 5.15, 4.3); arrow(s, 5.15, 4.98, 5.15, 5.22)
tag(s, 7.3, 2.14, "子订单精细落标", BLUE, size=10.5)
box(s, 7.3, 2.48, 5.45, 2.32, "", fill=WHITE, line=BLUE, lw=1.2, radius=0.05)
tbox(s, 7.5, 2.56, 5.1, 0.3, "MEMBER_EWP_ORDER_SUB（每个子项独立记账）", size=9.5, bold=True, color=BLUE)
sb1 = box(s, 7.55, 2.92, 4.95, 0.52, [("子订单 A · 升级套餐　", 9.5, True, INK), ("积分 300 ＋ 现金 0", 9.5, False, BLUE)], fill=BLUE_L, line=None)
sb2 = box(s, 7.55, 3.52, 4.95, 0.52, [("子订单 B · 加项胃镜　", 9.5, True, INK), ("积分 100 ＋ 现金 100", 9.5, False, BLUE)], fill=BLUE_L, line=None)
sb3 = box(s, 7.55, 4.12, 4.95, 0.52, [("子订单 C · 加项腹部超声　", 9.5, True, INK), ("积分 0 ＋ 现金 200", 9.5, False, BLUE)], fill=BLUE_L, line=None)
arrow(s, 6.72, 3.9, 7.28, 3.7)
tbox(s, 5.85, 3.98, 1.5, 0.24, "scoreValue 分摊写入", size=8, bold=True, color=ARROW, align=PP_ALIGN.CENTER)
box(s, 7.3, 5.24, 5.45, 0.66, "财务分账 · 发票拆分 · 售后退款 —— 每笔构成原子级可溯",
    fill=GREEN_L, line=GREEN, size=10, bold=True)
arrow(s, 10.02, 4.82, 10.02, 5.22)
page_no(s, 16)

# =========================================================
# S6 决策05 回调驱动退积分
# =========================================================
s = content_slide("05", "资金回调驱动退积分", "Callback-driven Point Refund", BLUE,
    ["逆向退款", "异步联动", "总账在下游"],
    "资金退款成功回调驱动下游积分释放：钱先退、积分后返；积分生命周期绑定体检权益，总账由外部系统托管对账。",
    ["现金通道与积分中心是异构结算主体", "并发双边退款 → 单边账损失风险", "HMSC 自建积分总账 → 双写不一致"])
e1 = box(s, 0.6, 2.5, 1.75, 0.85, "用户申请退款\n（现金+积分混合单）", fill=BLUE_L, line=BLUE, size=9)
e2 = box(s, 2.7, 2.5, 1.7, 0.85, "向三方网关发起\n资金退款请求", fill=WHITE, line=BLUE, size=9)
d2 = box(s, 4.75, 2.4, 1.55, 1.05, "网关确认\n退款成功?", fill=WHITE, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=9)
e3 = box(s, 6.65, 2.5, 1.9, 0.85, "回调方法内触发\n释放退还积分\n（福粒/信福通）", fill=TEAL_L, line=TEAL, size=9)
e4 = box(s, 8.9, 2.5, 1.65, 0.85, "双边闭环完成\n绝不单边死账", fill=GREEN, line=None, size=9.5, bold=True, color=WHITE)
arrow(s, 2.37, 2.92, 2.68, 2.92); arrow(s, 4.42, 2.92, 4.73, 2.92)
arrow(s, 6.32, 2.92, 6.63, 2.92, label="是", lx=0.0, ly=-0.24)
arrow(s, 8.57, 2.92, 8.88, 2.92)
f1 = box(s, 5.0, 4.35, 1.95, 0.62, "回调事务抛异常回滚", fill=WHITE, line=RED, size=9)
seg(s, 5.52, 3.47, 5.52, 4.33, dash=True)
f2 = box(s, 7.4, 4.35, 1.8, 0.62, "网关重新推送通知重试", fill=WHITE, line=RED, dash=True, size=9)
arrow(s, 6.97, 4.66, 7.38, 4.66)
arrow(s, 8.3, 4.33, 7.9, 3.37, dash=True, label="重新回调", lx=0.3, ly=0.1)
f3 = box(s, 0.6, 4.35, 4.0, 0.62, "超过最大重试阈值 → 异常落标 · 人工介入", fill=RED_L, line=RED, size=9.5)
arrow(s, 4.98, 4.66, 4.62, 4.66)
box(s, 10.95, 2.35, 1.83, 3.35, [
    ("积分架构定位", 10.5, True, TEAL),
    ("① 生命周期严格绑定权益有效期", 8.5, False, INK),
    ("② 总账下沉下游\nHMSC 仅消费与调度", 8.5, False, INK),
    ("③ 正向：预冻结 → 回调转实扣", 8.5, False, INK),
    ("④ 逆向：待付取消原路释放", 8.5, False, INK)],
    fill=PAPER, line=None, size=9, align=PP_ALIGN.LEFT)
page_no(s, 17)

# =========================================================
# S7 决策06 双账本镜像对账
# =========================================================
s = content_slide("06", "外部积分平台 × 核心镜像双冻结对账", "Dual-Account Shadow Ledger & Concurrent Freeze", BLUE,
    ["正向双冻结", "SKU 穿透", "逆向双释放"],
    "外部渠道冻结 + 核心镜像并发双冻结防超扣；子订单 SKU 级明细穿透 1:1 对应；并行双释放 + 异常补偿托底最终一致。",
    ["多终端并发 / 重试 → 积分超扣风险", "粗粒度总额扣减 → 无法还原 SKU 构成", "外部超时缺乏审计镜像"],
    ["高一致性：阻断超扣与重放抵扣", "明细可溯：银行级财务对账", "韧性托底：异常补偿 + 人工通道"])
tag(s, 0.6, 2.12, "① 正向 · 并发双冻结（Stream 并发触发）", TEAL, size=11)
q0 = box(s, 0.6, 2.5, 1.7, 0.85, "IntegralStrategy\n.freezeIntegral", fill=BLUE_L, line=BLUE, size=8.5)
qa = box(s, 3.05, 2.42, 2.35, 0.6, "外部平台预冻结\nFuLi / XinFuTong", fill=WHITE, line=BLUE, size=9)
qb = box(s, 3.05, 3.2, 2.35, 0.6, "核心镜像冻结（Shadow）\nCoreIntegralService 落流水", fill=WHITE, line=BLUE, size=9)
qg = box(s, 6.15, 2.8, 3.0, 0.75, "双边实时对齐\n本地水位锁 + 外部凭据 → 阻断超扣", fill=TEAL, line=None, size=9, bold=True, color=WHITE)
qs = box(s, 9.85, 2.5, 2.9, 1.05, [("子订单 → sku_items", 9.5, True, INK),
    ("{ partner_sku, quantity, unit_price }", 8.5, False, BLUE),
    ("与加项包颗粒度 1:1 穿透", 8.5, False, INK)], fill=WHITE, line=BLUE, size=9)
arrow(s, 2.32, 2.75, 3.03, 2.68); arrow(s, 2.32, 3.1, 3.03, 3.52)
arrow(s, 5.42, 2.72, 6.13, 3.05); arrow(s, 5.42, 3.5, 6.13, 3.32)
arrow(s, 9.17, 3.17, 9.83, 3.05)
tag(s, 0.6, 3.98, "② 逆向 · 并行双释放与异常补偿（traceId 全链路透传）", ORANGE, size=11)
r0 = box(s, 0.6, 4.35, 2.0, 0.9, "取消 / 超时未付\nreleaseIntegral 并行流", fill=ORANGE_L, line=ORANGE, size=9)
ra = box(s, 3.3, 4.28, 2.25, 0.6, "外部撤单\ncancelIntegralOrder", fill=WHITE, line=ORANGE, size=9)
rb = box(s, 3.3, 5.03, 2.25, 0.6, "核心镜像释放\n（双边留痕）", fill=WHITE, line=ORANGE, size=9)
rd = box(s, 6.1, 4.5, 1.5, 0.9, "外部撤单\n成功?", fill=WHITE, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=9)
re = box(s, 8.15, 4.3, 2.3, 0.6, "二次反查外部状态\n（福粒 7 = 已撤销?）", fill=WHITE, line=ORANGE, size=8.5)
rf = box(s, 8.15, 5.05, 2.3, 0.62, "仍失败 → EXCEPTION_LOG\n异常补偿任务", fill=RED_L, line=RED, size=8.5)
rg = box(s, 10.9, 4.42, 1.85, 0.6, "双边释放完成", fill=GREEN, line=None, size=9.5, bold=True, color=WHITE)
arrow(s, 2.62, 4.65, 3.28, 4.58); arrow(s, 2.62, 5.0, 3.28, 5.33)
arrow(s, 5.57, 4.58, 6.08, 4.85)
arrow(s, 7.62, 4.85, 8.13, 4.6)
tbox(s, 7.55, 4.28, 0.5, 0.24, "否", size=8.5, bold=True, color=ARROW, align=PP_ALIGN.CENTER)
arrow(s, 9.3, 4.92, 9.3, 5.12)
tbox(s, 9.45, 4.93, 1.1, 0.2, "仍未撤销", size=8, bold=True, color=ARROW)
seg(s, 6.85, 5.4, 6.85, 5.92); seg(s, 6.85, 5.92, 11.82, 5.92)
arrow(s, 11.82, 5.92, 11.82, 5.04)
tbox(s, 7.0, 5.94, 0.8, 0.26, "是", size=8.5, bold=True, color=ARROW)
page_no(s, 18)

# =========================================================
# S8 决策07 排期容量与改期边界
# =========================================================
s = content_slide("07", "分院排期容量、改期边界与超期释放", "Store Schedule, Capacity & Reschedule Boundaries", TEAL,
    ["供应商域 × 预约单域", "同店改期", "No-show 释放"],
    "同店改期约束 + 体检当天「禁退可改」不对称策略 + 线上线下双轨容量 + 超期未到检自动释放闭环。",
    ["跨店改期 → 加项交集重算 + 跨系统分布式事务", "当天任意退 → 试剂/排班空置损失", "No-show 不清理 → 权益沉没"],
    ["履约边界清晰", "兼顾供需利益", "资源高效周转"])
# A 容量双轨
panel(s, 0.5, 2.08, 5.85, 1.82)
tag(s, 0.65, 2.16, "容量双轨排期", TEAL, size=10.5)
a1 = box(s, 0.65, 2.52, 2.6, 0.72, "线上民营机构\n供应商 API 实时日历", fill=WHITE, line=TEAL, size=9)
a2 = box(s, 3.6, 2.52, 2.6, 0.72, "线下公立医院\nHMSCS 配额 · 提前 3~7 天", fill=WHITE, line=TEAL, size=9)
chip(s, 0.65, 3.38, "项目级屏蔽日拦截", fill=TEAL_L, line=None, color=TEAL, size=8.5)
chip(s, 2.6, 3.38, "时段细分（可降级全天）", fill=TEAL_L, line=None, color=TEAL, size=8.5)
# B 改期边界
panel(s, 6.5, 2.08, 6.28, 1.82)
tag(s, 6.65, 2.16, "改期边界 · 原分院同店约束", TEAL, size=10.5)
b1 = box(s, 6.65, 2.52, 1.3, 0.72, "改期申请", fill=WHITE, line=TEAL, size=9.5)
b2 = box(s, 8.3, 2.52, 2.15, 0.72, "仅改日期 / 时段\n（原门店内）✓", fill=GREEN_L, line=GREEN, size=9)
b3 = box(s, 10.8, 2.52, 1.55, 0.72, "变更分院 ✗", fill=RED_L, line=RED, size=9.5)
b4 = box(s, 8.3, 3.38, 4.05, 0.42, "换店唯一路径：取消预约 → 恢复待预约 → 重新选店", fill=PAPER, line=None, size=8.5)
arrow(s, 7.97, 2.88, 8.28, 2.88); arrow(s, 10.47, 2.88, 10.78, 2.88)
arrow(s, 11.57, 3.26, 11.57, 3.36, dash=True)
# C 当天不对称
panel(s, 0.5, 4.0, 5.85, 1.85)
tag(s, 0.65, 4.08, "体检当天不对称改退", TEAL, size=10.5)
c1 = box(s, 0.65, 4.48, 2.6, 0.85, "主动取消入口关闭 ✗\n保护已配试剂与排班", fill=RED_L, line=RED, size=9)
c2 = box(s, 3.6, 4.48, 2.6, 0.85, "原店改期保留 ✓\n可延后至后续可用日期", fill=GREEN_L, line=GREEN, size=9)
tbox(s, 0.65, 5.45, 5.6, 0.32, "「禁退可改」：机构成本与员工救济的人性化平衡", size=9, color=GRAY)
# D 需协调 & 超期
panel(s, 6.5, 4.0, 6.28, 1.85)
tag(s, 6.65, 4.08, "需协调特批 & 超期自动释放", TEAL, size=10.5)
d1 = box(s, 6.65, 4.48, 1.85, 0.6, "日期标记「需协调」", fill=WHITE, line=GOLD, size=8.5)
d2 = box(s, 8.85, 4.48, 2.2, 0.72, "客服特批 → 预约单 01\n线下协调加号加配额", fill=GOLD_L, line=GOLD, size=8.5)
d3 = box(s, 6.65, 5.32, 1.85, 0.6, "No-show 超体检日", fill=WHITE, line=RED, size=8.5)
d4 = box(s, 8.85, 5.28, 2.75, 0.68, "定时任务自动取消\n释放占容 · 主单恢复待预约", fill=GREEN_L, line=GREEN, size=8.5)
arrow(s, 8.52, 4.78, 8.83, 4.82); arrow(s, 8.52, 5.62, 8.83, 5.62)
tbox(s, 11.25, 4.55, 1.5, 0.9, "权益有效期内\n可重新履约", size=8.5, color=GRAY)
page_no(s, 19)

# =========================================================
# S9 决策08 合并履约 / 权益门禁 / 双轨同步
# =========================================================
s = content_slide("08", "合并履约、权益到期换店拦截与双轨同步", "Bundled Fulfillment, Equity Expiry Guard & Dual-Track Ingestion", TEAL,
    ["履约域", "原子交付", "状态同步"],
    "预约单是主套餐 + 全部加项包的唯一履约容器；跨店换店唯一路径受权益到期熔断拦截；线上轮询 + 线下导入双轨推进状态。",
    ["加项须与主套餐同天同店统一采血", "换店 = 先取消再重新预约的解耦动作", "民营 API vs 公立离线的行业现状"])
# P1
tag(s, 0.6, 2.12, "① 主+加项合并原子交付", TEAL, size=10.5)
p1a = box(s, 0.6, 2.5, 3.6, 0.75, "预约单 = 唯一履约容器\n主套餐 + 全部自选加项包", fill=TEAL_L, line=TEAL, size=9.5)
p1b = box(s, 0.6, 3.5, 3.6, 0.62, "线上民营：同一笔外部预约单打包 · 单一就检编号", fill=WHITE, line=TEAL, size=8.5)
p1c = box(s, 0.6, 4.32, 3.6, 0.62, "线下公立：对接 Excel 单条聚合记录交付医院", fill=WHITE, line=TEAL, size=8.5)
p1d = box(s, 0.6, 5.2, 3.6, 0.6, "单人 · 单店 · 单次 一站式完成", fill=GREEN_L, line=GREEN, size=9.5, bold=True)
arrow(s, 2.4, 3.27, 2.4, 3.48); arrow(s, 2.4, 4.14, 2.4, 4.3); arrow(s, 2.4, 4.96, 2.4, 5.18)
# P2
tag(s, 4.55, 2.12, "② 换店唯一路径 × 权益到期门禁", TEAL, size=10.5)
t1 = box(s, 4.55, 2.5, 2.0, 0.5, "取消原预约", fill=WHITE, line=PURPLE, size=9)
t2 = box(s, 4.55, 3.12, 2.0, 0.5, "释放原店排期", fill=WHITE, line=PURPLE, size=9)
t3 = box(s, 4.55, 3.74, 2.0, 0.5, "主单恢复待预约", fill=WHITE, line=PURPLE, size=9)
arrow(s, 5.55, 3.0, 5.55, 3.1); arrow(s, 5.55, 3.62, 5.55, 3.72)
d3 = box(s, 4.7, 4.4, 1.75, 0.85, "权益已过期?\nequityEndDate<今日", fill=WHITE, line=GOLD, shape=MSO_SHAPE.DIAMOND, size=8.5)
arrow(s, 5.55, 4.24, 5.6, 4.38)
o1 = box(s, 4.55, 5.5, 1.85, 0.66, "否 · 重新选新店\n预约 ✓", fill=GREEN_L, line=GREEN, size=8.5)
o2 = box(s, 6.55, 5.5, 1.75, 0.66, "是 · 拦截新预约 ✗\n（取消前强警示）", fill=RED_L, line=RED, size=8.5)
arrow(s, 5.15, 5.27, 5.3, 5.48); arrow(s, 6.1, 5.27, 7.2, 5.48)
# P3
tag(s, 8.75, 2.12, "③ 双轨到检与报告同步", TEAL, size=10.5)
s1 = box(s, 8.75, 2.5, 3.95, 0.75, "线上民营 · 定时轮询拉取\nPullAppointJsonReportHandler", fill=WHITE, line=ORANGE, size=9)
s2 = box(s, 8.75, 3.45, 3.95, 0.62, "拉取到检名单 + 原版 PDF（LLM OCR 提取）", fill=WHITE, line=ORANGE, size=8.5)
w1 = box(s, 8.75, 4.3, 1.16, 0.52, "02 预约成功", fill=PAPER, line=LINE, size=8)
w2 = box(s, 10.13, 4.3, 1.16, 0.52, "04 已到检", fill=PAPER, line=LINE, size=8)
w3 = box(s, 11.51, 4.3, 1.19, 0.52, "05 已出报告", fill=PAPER, line=LINE, size=8)
arrow(s, 9.93, 4.56, 10.11, 4.56); arrow(s, 11.31, 4.56, 11.49, 4.56)
s4 = box(s, 8.75, 5.05, 3.95, 0.7, "线下公立 · MIS 运营导入\nExcel 名单 / 核销上传扫描件 → 人工推进同一状态机", fill=WHITE, line=ORANGE, size=8.5)
arrow(s, 10.72, 4.09, 10.72, 3.95, dash=True)
page_no(s, 20)

# =========================================================
# S10 决策09 套餐模型与智能推荐
# =========================================================
s = content_slide("09", "套餐层级、家属积分共济与问卷推荐", "Package Hierarchy, Family Points Sharing & Recommendation", PURPLE,
    ["产品域", "单选互斥", "适检门禁"],
    "主干套餐 1 of N 单选互斥、差额升舱；标准医学字典 + 适检属性门禁；家属包全额自费可用员工积分共济；问卷推荐自动勾选。",
    ["统付 / 自费分界失真风险", "禁忌项目合规（如未婚女性经阴道超声）", "千人一面 → 高风险漏筛"],
    ["层级严密厘清统付与自费", "全家共济提升积分活力", "精准预防提升早筛覆盖"])
tag(s, 0.6, 2.12, "主干套餐 · 单选互斥（1 of N）", PURPLE, size=10.5)
g0 = box(s, 0.6, 2.55, 2.15, 0.75, "主干套餐\n（必选其一）", fill=PURPLE, line=None, size=10, bold=True, color=WHITE)
h1 = box(s, 3.35, 2.35, 2.95, 0.62, "00 标准主套餐 · 企业统付", fill=WHITE, line=PURPLE, size=9)
h2 = box(s, 3.35, 3.12, 2.95, 0.62, "02 升级套餐 · 仅付差额（售价−基准价）", fill=WHITE, line=PURPLE, size=9)
h3 = box(s, 3.35, 3.89, 2.95, 0.62, "03 加价套餐 · 网点溢价 extraPrice", fill=WHITE, line=PURPLE, size=9)
arrow(s, 2.77, 2.75, 3.33, 2.62); arrow(s, 2.77, 2.95, 3.33, 3.4); arrow(s, 2.77, 3.15, 3.33, 4.18)
h4 = box(s, 3.35, 4.78, 2.95, 0.66, "01 加项包 0~N · 医学互斥\n受企业预算帽（Budget Cap）管控", fill=ORANGE_L, line=ORANGE, size=8.5)
seg(s, 4.82, 4.53, 4.82, 4.76, color=ORANGE)
tbox(s, 0.6, 3.55, 2.5, 1.2, "差额部分支持\n现金自费 或\n企业积分 1:1 抵扣", size=9, color=GRAY)
# 右上 医学字典与门禁
tag(s, 6.7, 2.12, "标准医学字典 × 适检门禁", PURPLE, size=10.5)
j1 = box(s, 6.7, 2.5, 2.9, 0.85, "平台标准医学字典库\n爱康/美年/瑞慈/公立 → 入库映射对齐", fill=WHITE, line=PURPLE, size=8.5)
j2 = box(s, 9.9, 2.5, 2.88, 0.85, "适检人群属性门禁\n性别 × 婚姻状态 · 过滤+硬校验", fill=RED_L, line=RED, size=8.5)
arrow(s, 9.62, 2.92, 9.88, 2.92)
# 右中 家属共济
tag(s, 6.7, 3.55, "员工包 P × 家属包 G · 积分共济", PURPLE, size=10.5)
k1 = box(s, 6.7, 3.92, 2.9, 0.7, "员工产品包（P）\n企业统付 / 升舱共付", fill=WHITE, line=PURPLE, size=9)
k2 = box(s, 9.9, 3.92, 2.88, 0.7, "家属产品包（G）\n全额自费 · 可扣员工福利积分", fill=TEAL_L, line=TEAL, size=9)
arrow(s, 9.62, 4.27, 9.88, 4.27, label="积分划扣", lx=0, ly=-0.26)
# 右下 问卷推荐
tag(s, 6.7, 4.85, "问卷驱动智能推荐 · 自动勾选", PURPLE, size=10.5)
q1 = box(s, 6.7, 5.22, 1.4, 0.85, "健康问卷\n病史/习惯\n关注点", fill=WHITE, line=PURPLE, size=8.5)
q2 = box(s, 8.27, 5.22, 1.4, 0.85, "风险模型\n动态计算\n健康风险", fill=WHITE, line=PURPLE, size=8.5)
q3 = box(s, 9.84, 5.22, 1.4, 0.85, "匹配推荐\n主套餐\n+ 加项包", fill=WHITE, line=PURPLE, size=8.5)
q4 = box(s, 11.41, 5.22, 1.37, 0.85, "界面默认\n自动勾选 ✓", fill=GREEN_L, line=GREEN, size=8.5, bold=True)
arrow(s, 8.12, 5.64, 8.25, 5.64); arrow(s, 9.69, 5.64, 9.82, 5.64); arrow(s, 11.26, 5.64, 11.39, 5.64)
page_no(s, 21)

# =========================================================
# S11 决策10 报告解读增值流水线
# =========================================================
s = content_slide("10", "报告解读增值服务流水线", "Report Interpretation Pipeline & HR Monitoring", ORANGE,
    ["档案域 × 活动域", "LLM OCR", "AI + 医生双轨"],
    "全域 PDF + 大模型 OCR 统一结构化（原生 JSON 弃用）；免费 AI 即时解读与异步三方医生解读双轨；C24/C59 随权益子产品导入。",
    ["N 套私有 JSON 解析器维护灾难", "即时科普 vs 深度研判的服务分层", "员工健康数据 PII 隐私合规"],
    ["全域指标大一统归档", "服务分层各司其职", "B 端健康管理黏性提升"])
t1 = box(s, 0.6, 2.42, 2.75, 0.85, "报告归集\n线上 API 轮询 PDF ｜ 线下 MIS 导入", fill=WHITE, line=ORANGE, size=9)
t2 = box(s, 3.75, 2.42, 2.9, 0.85, "大模型 OCR 统一结构化\n项目/实测值/单位/参考区间/异常标识", fill=ORANGE_L, line=ORANGE, size=9)
t3 = box(s, 7.05, 2.42, 2.5, 0.85, "映射平台标准医学字典\n（原生 JSON 链路已弃用 ✗）", fill=WHITE, line=ORANGE, size=9)
t4 = box(s, 9.95, 2.42, 2.83, 0.85, "归档健康档案 HMES\n支撑历年趋势比对", fill=TEAL_L, line=TEAL, size=9)
arrow(s, 3.37, 2.84, 3.73, 2.84); arrow(s, 6.67, 2.84, 7.03, 2.84); arrow(s, 9.57, 2.84, 9.93, 2.84)
tb1 = box(s, 0.6, 3.55, 5.0, 0.6, "外院自传历史报告 → 仅个人端查看\n不入健康档案 · 不参与正式趋势比对 ✗", fill=RED_L, line=RED, dash=True, size=8.5)
arrow(s, 1.9, 3.29, 1.9, 3.53, dash=True)
box(s, 6.0, 3.55, 6.78, 0.6, "官方履约档案只保留机构原件抽取结果，捍卫档案真实性",
    fill=PAPER, line=None, size=9, color=GRAY)
tag(s, 0.6, 4.35, "普惠 AI 即时解读 · 小诺", BLUE, size=10.5)
u1 = box(s, 0.6, 4.72, 5.9, 0.9, "项目启用 AI 开关后全员可用：免费 · 即时\n指标成因分析 + 生活方式建议（广度科普）", fill=BLUE_L, line=BLUE, size=9.5)
tag(s, 6.85, 4.35, "异步三方医生解读 · 工单制（C24 / C59）", PURPLE, size=10.5)
u2 = box(s, 6.85, 4.72, 5.93, 0.9, "结构化数据+病史 → 推送三方解读中心 → 医生限时核阅\n异步回调 → 结论以结构化数据回写权益与报告（深度研判）", fill=PURPLE_L, line=PURPLE, size=9)
n1 = box(s, 0.6, 5.82, 4.75, 0.55, "C24/C59 非商城零售 · 随企业权益子产品导入赋权", fill=GOLD_L, line=GOLD, size=8.5)
n2 = box(s, 5.55, 5.82, 3.4, 0.55, "B 端 HR 异常指标看板 · 脱敏合规授权", fill=PAPER, line=LINE, size=8.5)
n3 = box(s, 9.15, 5.82, 3.63, 0.55, "家庭报告归集员工账户 · 切换持有人查看", fill=PAPER, line=LINE, size=8.5)
page_no(s, 22)

# =========================================================
# S12 决策11 商城分类与卡券兑换
# =========================================================
s = content_slide("11", "商城多租户分类、卡密兑换与子产品边界", "Shop Custom Categories & Voucher Redemption to Benefits", PURPLE,
    ["商品域 × 权益域", "卡密核验", "非商城零售"],
    "项目级自定义分类实现千企千面；卡券经卡密核验在核心域生成体检权益；C24/C59 不零售、随权益导入；优惠套餐支付后直接转履约单。",
    ["硬编码分类不适配多租户", "卡密盗刷套利风险", "直接生成裸订单会绕过权益校验"],
    ["新大客户上线成本大幅降低", "以权益为契约沉淀至核心", "客服审核 + 兑换锁死守住资金线"])
v0 = box(s, 10.15, 2.42, 2.63, 1.85, [("项目级自定义分类", 10, True, PURPLE),
    ("企业项目配置动态类目\nMIS 双轨标签：优惠套餐购买 /\n健康商城分类\n→ 千企千面商品橱窗", 8.5, False, INK)],
    fill=WHITE, line=PURPLE, size=9)
tag(s, 0.6, 2.12, "路径 A · 优惠套餐即时转单", PURPLE, size=10.5)
a1 = box(s, 0.6, 2.46, 1.95, 0.72, "体检端购买\n优惠套餐", fill=WHITE, line=PURPLE, size=9)
a2 = box(s, 2.9, 2.46, 2.1, 0.72, "支付成功\n（积分 1:1 抵扣）", fill=WHITE, line=PURPLE, size=9)
a3 = box(s, 5.35, 2.46, 2.1, 0.72, "直接生成待预约\n体检主订单", fill=PURPLE_L, line=PURPLE, size=9)
a4 = box(s, 7.8, 2.46, 1.95, 0.72, "立即选分院\n排期预约", fill=GREEN_L, line=GREEN, size=9)
arrow(s, 2.57, 2.82, 2.88, 2.82); arrow(s, 5.02, 2.82, 5.33, 2.82); arrow(s, 7.47, 2.82, 7.78, 2.82)
tag(s, 0.6, 3.42, "路径 B · 卡券兑换生成核心权益", PURPLE, size=10.5)
b1 = box(s, 0.6, 3.78, 1.95, 0.72, "商城购买体检卡券\n获得卡密", fill=WHITE, line=TEAL, size=9)
b2 = box(s, 2.9, 3.78, 2.1, 0.72, "H5/PC 输入卡密\ncheckGardPassword 核验", fill=WHITE, line=TEAL, size=9)
b3 = box(s, 5.35, 3.78, 2.1, 0.72, "hmscs 核心域生成\n正式体检权益 Benefit", fill=TEAL_L, line=TEAL, size=9)
b4 = box(s, 7.8, 3.78, 1.95, 0.72, "体检侧动态感知\n→ 标准体检流程", fill=GREEN_L, line=GREEN, size=9)
arrow(s, 2.57, 4.14, 2.88, 4.14); arrow(s, 5.02, 4.14, 5.33, 4.14); arrow(s, 7.47, 4.14, 7.78, 4.14)
x1 = box(s, 0.6, 4.85, 5.3, 0.58, "实物商品售后：未发货即时退 ｜ 已发货退货退款（寄回验收）", fill=PAPER, line=LINE, size=8.5)
x2 = box(s, 6.15, 4.85, 3.6, 0.58, "混合退款：资金回调驱动退积分（双边一致）", fill=PAPER, line=LINE, size=8.5)
xb = box(s, 0.6, 5.62, 9.15, 0.55, "边界红线：C24/C59 医疗增值服务不在商城零售 → 随权益子产品导入赋权",
    fill=RED_L, line=RED, dash=True, size=9, bold=True)
tag(s, 10.15, 4.45, "卡券退款守卫", RED, size=10)
y1 = box(s, 10.15, 4.8, 2.63, 0.58, "未兑换：关闭自助退款\n客服介入 · MIS 核实原路退", fill=WHITE, line=GOLD, size=8)
y2 = box(s, 10.15, 5.5, 2.63, 0.58, "已兑换生成权益\n永久锁死 · 不可退款 ✗", fill=RED_L, line=RED, size=8)
page_no(s, 23)

# =========================================================
# S13 端到端总流程
# =========================================================
s = new_slide()
tbox(s, 0.55, 0.32, 10.0, 0.55, "端到端主流程总览", size=23, bold=True, color=INK)
tbox(s, 0.57, 0.9, 10.0, 0.3, "End-to-End Value Stream · 正向履约主线 × 逆向退款主线 × 关键护栏", size=10.5, color=GRAY)
seg(s, 0.55, 1.32, 12.78, 1.32, color=RGBColor(0xD8, 0xE0, 0xEC), w=1.0)
tag(s, 0.6, 1.52, "正向履约主线", TEAL, size=11)
steps = ["企业权益获取", "选套餐·加项", "建单 1人1单", "混合支付", "预约排期", "到检", "报告 OCR", "增值解读"]
cx, cw, step = 0.6, 1.62, 1.51
for i, t in enumerate(steps):
    box(s, cx, 1.9, cw, 1.0, t, fill=[BLUE, BLUE, TEAL, BLUE, TEAL, TEAL, ORANGE, PURPLE][i],
        line=None, shape=MSO_SHAPE.CHEVRON, size=9.5, bold=True, color=WHITE)
    cx += step
caps = [("组合单瞬态", 3), ("双冻结+回调", 4), ("容量双轨", 5), ("状态双轨", 6), ("LLM 结构化", 7)]
for t, i in caps:
    tbox(s, 0.6 + i * step + 0.08, 2.98, 1.5, 0.28, t, size=8, color=GRAY, align=PP_ALIGN.CENTER)
tag(s, 0.6, 3.5, "逆向退款主线", ORANGE, size=11)
rsteps = ["申请取消 / 退款", "级联取消预约 · 释放排期", "主单状态收敛", "资金退款成功回调", "释放下游积分", "对账 · 异常补偿"]
cx, cw, step = 0.6, 2.0, 2.05
for i, t in enumerate(rsteps):
    box(s, cx, 3.88, cw, 0.85, t, fill=ORANGE_L, line=ORANGE, size=9, color=INK)
    if i < len(rsteps) - 1:
        arrow(s, cx - 0.03, 4.3, cx - 0.2 + 0.0, 4.3) if False else None
    cx += step
# 逆向箭头（从右往左连）
for i in range(len(rsteps) - 1):
    x_right_box_left = 0.6 + (i + 1) * step
    arrow(s, x_right_box_left - 0.02, 4.3, 0.6 + i * step + cw + 0.02, 4.3)
tag(s, 0.6, 5.05, "关键护栏（贯穿全程）", GOLD, size=11)
gx = 0.6
for t in ["1 积分 = 1 元等值", "子订单分摊落标", "双账本镜像对账", "权益有效期门禁", "同店改期", "当天禁退可改", "异常补偿 + 人工托底", "家庭报告共聚"]:
    w = chip_w(t, 9.5)
    box(s, gx, 5.42, w, 0.44, t, fill=GOLD_L, line=GOLD, size=9.5, bold=True, color=RGBColor(0x7A, 0x59, 0x0B), radius=0.5)
    gx += w + 0.18
# 主线串联说明
box(s, 0.6, 6.15, 12.18, 0.85, [("主线契约：", 10.5, True, INK),
    ("商城/卡券/企业导入统一沉淀为「权益（Benefit）」→ 履约以「主订单 1:1 持有人」为基石 → 资金以「回调驱动 + 镜像对账」保一致 → 数据以「LLM OCR + 标准字典」大一统归档。", 10.5, False, INK)],
    fill=PAPER, line=None, align=PP_ALIGN.LEFT)
page_no(s, 24)

# =========================================================
# S14 收尾 · 效果与影响
# =========================================================
s = new_slide()
tbox(s, 0.55, 0.32, 10.0, 0.55, "效果与影响 · 四大价值面", size=23, bold=True, color=INK)
tbox(s, 0.57, 0.9, 10.0, 0.3, "Outcomes · 11 项决策叠加后的系统性收益", size=10.5, color=GRAY)
seg(s, 0.55, 1.32, 12.78, 1.32, color=RGBColor(0xD8, 0xE0, 0xEC), w=1.0)
cols = [
    ("交易与资金安全", BLUE, ["双账本镜像对账，阻断超扣与单边账", "回调驱动退积分，资金-积分异步联动", "子订单落标，退款/发票原子级溯源"]),
    ("履约边界与体验", TEAL, ["同店改期 + 当天禁退可改，边界清晰", "主套餐+加项合并原子交付不漏检", "超期 No-show 自动释放，权益不沉没"]),
    ("数据与档案资产", ORANGE, ["LLM OCR 大一统，公立医院无障碍归档", "标准医学字典跨机构可比对齐", "官方档案纯净，外院报告隔离存放"]),
    ("B 端与家庭价值", PURPLE, ["千企千面橱窗，大客户上线降本", "HR 异常指标看板，健康干预决策", "家属积分共济 + 家庭报告共聚"]),
]
xs = [0.55, 3.64, 6.73, 9.82]
for (title, acc, items), x in zip(cols, xs):
    box(s, x, 1.7, 2.91, 3.6, "", fill=WHITE, line=RGBColor(0xD8, 0xE0, 0xEC), lw=1.0, radius=0.07)
    box(s, x, 1.7, 2.91, 0.09, "", fill=acc, line=None, shape=MSO_SHAPE.RECTANGLE)
    tbox(s, x + 0.18, 1.92, 2.6, 0.4, title, size=13, bold=True, color=acc)
    ly = 2.5
    for it in items:
        box(s, x + 0.2, ly + 0.07, 0.1, 0.1, "", fill=acc, line=None, shape=MSO_SHAPE.OVAL)
        tbox(s, x + 0.42, ly - 0.04, 2.35, 0.85, it, size=9.5, color=INK)
        ly += 0.92
box(s, 1.4, 5.75, 10.53, 0.85, "以「权益」为中心 · 以「主订单 1:1 持有人」为基石 · 以「回调驱动 + 镜像对账」保一致\n支撑企业健康福利的规模化、可审计、可追溯履约",
    fill=TEAL_L, line=TEAL, size=13, bold=True, color=RGBColor(0x0A, 0x5C, 0x64))
page_no(s, 25)

# ---------------- save ----------------
prs.core_properties.title = "体检平台架构决策与核心流程"
prs.core_properties.author = "HMSC 架构组"
OUT = "/home/user/learning/体检平台架构决策与核心流程.pptx"
prs.save(OUT)
print("saved:", OUT, "slides:", len(prs.slides.__iter__.__self__._sldIdLst))
