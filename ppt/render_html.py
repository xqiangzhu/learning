# -*- coding: utf-8 -*-
"""
网页速览版渲染器：把同一份 deck_content.SLIDES 渲染成单文件 HTML。

用途
  * 不装 PowerPoint / WPS 也能先在浏览器里过一遍内容与版面；
  * 与 .pptx 共用同一份内容模型和同一套版面数学（1in = 96px），因此两版结构一致；
  * 自带打印样式，可直接「打印成 PDF」当讲义用。

注意：这是速览版，字体度量与 PPTX 的自动排版不完全等价，最终交付以 .pptx 为准。
"""
import html
import os
from urllib.parse import quote

from deck_content import (SLIDES, C, FOOTER, DW, DH, DOMAINS, META, SOURCE,
                          anchor_points)

# 版面常量（英寸，与 render_pptx 保持一致）
SW, SH = 13.333, 7.5
ML = 0.72
CW = SW - 2 * ML
BODY_TOP_WITH_LEDE = 1.98
BODY_TOP_PLAIN = 1.62
BODY_BOT = 6.62
FN_Y = 6.72
FT_Y = 7.10
PX = 96.0                      # 1 英寸 = 96px


def IN(v):
    return round(v * PX, 2)


def PT(v):
    return round(v * PX / 72.0, 2)


def esc(t):
    return html.escape(str(t if t is not None else ""))


def col(key):
    return "#" + C.get(key, key)


def body_geom(spec):
    top = BODY_TOP_WITH_LEDE if spec.get("lede") else BODY_TOP_PLAIN
    bot = BODY_BOT
    cal = spec.get("callout")
    if cal:
        ch = 0.46 if len(cal["text"]) < 62 else 0.62
        return top, bot - ch - 0.16, (ML, bot - ch, CW, ch)
    return top, bot, None


# ------------------------------------------------------------------ 部件 ----
def h_header(spec, dark=False):
    out = []
    y = 0.44
    if spec.get("kicker"):
        out.append('<div class="kicker" style="top:%dpx">%s</div>'
                   % (IN(y), esc(spec["kicker"])))
        y = 0.70
    if spec.get("title"):
        out.append('<div class="htitle%s" style="top:%dpx">%s</div>'
                   % (" dark" if dark else "", IN(y), esc(spec["title"])))
    out.append('<div class="hrule" style="top:%dpx;left:%dpx"></div>'
               % (IN(1.28), IN(ML)))
    out.append('<div class="hline" style="top:%dpx;left:%dpx;width:%dpx"></div>'
               % (IN(1.303), IN(ML + 0.78), IN(CW - 0.78)))
    if spec.get("lede"):
        out.append('<div class="hlede%s" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
                   % (" dark" if dark else "", IN(1.40), IN(ML), IN(CW - 0.2),
                      esc(spec["lede"])))
    return "".join(out)


def h_footer(page, total, dark=False):
    cls = " dark" if dark else ""
    return ('<div class="fline%s" style="top:%dpx;left:%dpx;width:%dpx"></div>'
            '<div class="footl%s" style="top:%dpx;left:%dpx">%s</div>'
            '<div class="footr%s" style="top:%dpx;left:%dpx;width:%dpx">%02d / %d</div>'
            % (cls, IN(FT_Y - 0.06), IN(ML), IN(CW),
               cls, IN(FT_Y), IN(ML), esc(FOOTER),
               cls, IN(FT_Y), IN(ML + CW - 1.2), IN(1.2), page, total))


def h_footnote(spec, dark=False):
    if not spec.get("footnote"):
        return ""
    return ('<div class="fnote%s" style="top:%dpx;left:%dpx;width:%dpx">※ %s</div>'
            % (" dark" if dark else "", IN(FN_Y), IN(ML), IN(CW),
               esc(spec["footnote"])))


def h_callout(spec, cal_rect):
    if not cal_rect:
        return ""
    cal = spec["callout"]
    x, y, w, h = cal_rect
    c = cal.get("color", "accent")
    fillk = (c + "_l") if (c + "_l") in C else "accentl"
    return ('<div class="callout" style="top:%dpx;left:%dpx;width:%dpx;height:%dpx;'
            'background:%s;border-left:5px solid %s"><span>%s</span></div>'
            % (IN(y), IN(x), IN(w), IN(h), col(fillk), col(c), esc(cal["text"])))


def h_meter(x, y, w, vals):
    b, g = vals
    seg = ""
    if b:
        seg += ('<i style="left:0;width:%.2f%%;background:%s"></i>'
                % (max(b, 2.0), col("blue")))
    if g:
        seg += ('<i style="right:0;width:%.2f%%;background:%s"></i>'
                % (max(g, 2.0), col("green")))
    return ('<div class="meter" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
            '<div class="mcap" style="top:%dpx;left:%dpx;width:%dpx">流量权重 '
            '<b style="color:%s">蓝 %d</b> : <b style="color:%s">绿 %d</b></div>'
            % (IN(y), IN(x), IN(w), seg, IN(y + 0.22), IN(x), IN(w),
               col("blue"), b, col("green"), g))


# ------------------------------------------------------------------ 版式 ----
def r_cover(spec, page, total):
    badges = "".join(
        '<div class="cbadge" style="left:%dpx;top:%dpx;width:%dpx">%s</div>'
        % (IN(ML + i * 2.31), IN(4.42), IN(2.05), esc(b))
        for i, b in enumerate(spec["badges"]))
    return ('<div class="slide dark">' + deco() +
            '<div class="ckick" style="top:%dpx;left:%dpx">%s</div>'
            '<div class="ctitle" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
            '<div class="crule" style="top:%dpx;left:%dpx"></div>'
            '<div class="csub" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
            '%s'
            '<div class="cmeta" style="top:%dpx;left:%dpx">%s</div>'
            '%s%s</div>'
            % (IN(1.42), IN(ML), esc(spec["kicker"]),
               IN(1.92), IN(ML), IN(CW - 1.2), esc(spec["title"]),
               IN(3.02), IN(ML),
               IN(3.28), IN(ML), IN(CW - 1.6), esc(spec["subtitle"]),
               badges,
               IN(6.30), IN(ML), esc(spec["meta"]),
               bottom_bar(), h_footer(page, total, dark=True)))


def deco():
    rings = "".join('<i style="width:%dpx;height:%dpx;left:%dpx;top:%dpx;'
                    'background:%s"></i>'
                    % (IN(d), IN(d), IN(SW - 0.9 - d / 2), IN(-0.55 - d / 2), col(c))
                    for d, c in ((5.6, "navy2"), (3.7, "1B3E63"), (2.0, "0F5F6B")))
    return '<div class="rings">%s</div>' % rings


def bottom_bar():
    return ('<div class="bbar">'
            '<i style="left:0;width:%dpx;background:%s"></i>'
            '<i style="left:%dpx;width:%dpx;background:%s"></i>'
            '<i style="left:%dpx;width:%dpx;background:%s"></i></div>'
            % (IN(5.4), col("blue"), IN(5.4), IN(2.5), col("accent"),
               IN(7.9), IN(SW - 7.9), col("green")))


def r_toc(spec, page, total):
    items = spec["items"]
    top = BODY_TOP_WITH_LEDE if spec.get("lede") else BODY_TOP_PLAIN
    rh = min(0.94, (BODY_BOT - top) / len(items))
    out = []
    for i, it in enumerate(items):
        y = top + i * rh
        out.append(
            '<div class="tno" style="top:%dpx;left:%dpx;width:%dpx;height:%dpx">%s</div>'
            '<div class="ttitle" style="top:%dpx;left:%dpx">%s<span>%s</span></div>'
            '<div class="tdesc" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
            '<div class="tn" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
            % (IN(y + 0.08), IN(ML), IN(0.66), IN(rh - 0.26), esc(it["no"]),
               IN(y + 0.12), IN(ML + 0.94), esc(it["title"]), esc(it["en"]),
               IN(y + 0.50), IN(ML + 0.94), IN(CW - 2.9), esc(it["desc"]),
               IN(y + 0.24), IN(ML + CW - 1.28), IN(1.28), esc(it["n"])))
        if i < len(items) - 1:
            out.append('<div class="rowline" style="top:%dpx;left:%dpx;width:%dpx"></div>'
                       % (IN(y + rh - 0.03), IN(ML + 0.94), IN(CW - 0.94)))
    return ('<div class="slide">' + h_header(spec) + "".join(out) +
            h_footnote(spec) + h_footer(page, total) + '</div>')


def r_divider(spec, page, total):
    x, y = ML, 5.02
    pills = []
    for t in spec["terms"]:
        w = len(t) * 11 / 72.0 + 0.52
        if x + w > ML + CW:
            x, y = ML, y + 0.60
        pills.append('<div class="dpill" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
                     % (IN(y), IN(x), IN(w), esc(t)))
        x += w + 0.24
    return ('<div class="slide dark">' + deco() +
            '<div class="dno" style="top:%dpx;left:%dpx">%s</div>'
            '<div class="dtitle" style="top:%dpx;left:%dpx">%s</div>'
            '<div class="den" style="top:%dpx;left:%dpx">%s</div>'
            '<div class="crule" style="top:%dpx;left:%dpx"></div>'
            '<div class="dlede" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
            '%s%s%s</div>'
            % (IN(0.80), IN(ML - 0.06), esc(spec["no"]),
               IN(2.46), IN(ML), esc(spec["title"]),
               IN(3.24), IN(ML), esc(spec["en"]),
               IN(3.72), IN(ML),
               IN(3.96), IN(ML), IN(CW - 2.6), esc(spec["lede"]),
               "".join(pills), bottom_bar(), h_footer(page, total, dark=True)))


def r_points(spec, page, total):
    top, bot, cal = body_geom(spec)
    items = spec["items"]
    rh = (bot - top) / len(items)
    out = []
    for i, it in enumerate(items):
        y = top + i * rh
        out.append(
            '<div class="pchip" style="top:%dpx;left:%dpx;height:%dpx">%02d</div>'
            '<div class="phead" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
            '<div class="pbody" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
            % (IN(y + 0.14), IN(ML), IN(rh - 0.36), i + 1,
               IN(y + 0.14), IN(ML + 0.80), IN(2.5), esc(it["head"]),
               IN(y + 0.13), IN(ML + 3.48), IN(CW - 3.48), esc(it["body"])))
        if i < len(items) - 1:
            out.append('<div class="rowline" style="top:%dpx;left:%dpx;width:%dpx"></div>'
                       % (IN(y + rh - 0.05), IN(ML + 0.80), IN(CW - 0.80)))
    return ('<div class="slide">' + h_header(spec) + "".join(out) +
            h_callout(spec, cal) + h_footnote(spec) + h_footer(page, total) + '</div>')


def r_cards(spec, page, total):
    top, bot, cal = body_geom(spec)
    cards = spec["cards"]
    cols = spec.get("cols", len(cards))
    gap = 0.30
    cw = (CW - gap * (cols - 1)) / cols
    ch = bot - top
    fs = {2: {"title": 15, "en": 9.5, "body": 11.5, "tag": 9},
          3: {"title": 13.5, "en": 8.5, "body": 10.5, "tag": 8.5}}[cols]
    pad = 0.28 if cols == 2 else 0.24
    out = []
    for i, cd in enumerate(cards):
        x = ML + i * (cw + gap)
        acc = cd.get("accent", "accent")
        head = ""
        if cd.get("badge"):
            head = ('<div class="cbadge2" style="top:%dpx;left:%dpx;width:%dpx;'
                    'height:%dpx;background:%s">%s</div>'
                    % (IN(top + 0.30), IN(x + cw - pad - 0.46), IN(0.46), IN(0.46),
                       col(acc), esc(cd["badge"])))
        elif cd.get("tag"):
            tw = len(cd["tag"]) * fs["tag"] / 72.0 + 0.34
            fillk = (acc + "_l") if (acc + "_l") in C else "accentl"
            head = ('<div class="ctag" style="top:%dpx;left:%dpx;width:%dpx;'
                    'background:%s;color:%s">%s</div>'
                    % (IN(top + 0.30), IN(x + cw - pad - tw), IN(tw), col(fillk),
                       col(acc), esc(cd["tag"])))
        y = top + 0.30 + fs["title"] * 1.25 / 72 + 0.04
        en = ('<div class="cen" style="top:%dpx;left:%dpx;width:%dpx;color:%s">%s</div>'
              % (IN(y), IN(x + pad), IN(cw - 2 * pad), col(acc), esc(cd.get("en", ""))))
        y += 0.30
        meter = ""
        if cd.get("meter"):
            meter = h_meter(x + pad, y, cw - 2 * pad, cd["meter"])
            y += 0.52
        rule = ('<div class="rowline" style="top:%dpx;left:%dpx;width:%dpx"></div>'
                % (IN(y), IN(x + pad), IN(cw - 2 * pad)))
        y += 0.16
        bullets = "".join('<li><b style="color:%s">\u25aa</b>%s</li>'
                          % (col(acc), esc(b)) for b in cd["body"])
        out.append(
            '<div class="card" style="top:%dpx;left:%dpx;width:%dpx;height:%dpx">'
            '<i class="strip" style="background:%s;left:%dpx;width:%dpx"></i>%s'
            '<div class="ctitle" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
            '%s%s%s'
            '<ul class="cbody%s" style="top:%dpx;left:%dpx;width:%dpx;'
            'bottom:%dpx">%s</ul></div>'
            % (IN(top), IN(x), IN(cw), IN(ch), col(acc), IN(pad), IN(cw - 2 * pad),
               head, IN(top + 0.26), IN(x + pad), IN(cw - 2 * pad - 0.6),
               esc(cd["title"]), en, meter, rule,
               " small" if cols == 3 else "", IN(y), IN(x + pad), IN(cw - 2 * pad),
               IN(0.20), bullets))
    return ('<div class="slide">' + h_header(spec) + "".join(out) +
            h_callout(spec, cal) + h_footnote(spec) + h_footer(page, total) + '</div>')


def r_timeline(spec, page, total):
    top, bot, cal = body_geom(spec)
    steps = spec["steps"]
    n = len(steps)
    out = []
    if spec.get("horizontal"):
        gap = 0.34
        cw = (CW - gap * (n - 1)) / n
        out.append('<div class="spine" style="top:%dpx;left:%dpx;width:%dpx"></div>'
                   % (IN(top + 0.33), IN(ML + cw / 2), IN(CW - cw)))
        for i, st in enumerate(steps):
            x = ML + i * (cw + gap)
            out.append(
                '<div class="tlcircle" style="top:%dpx;left:%dpx">%s</div>'
                '<div class="tltitle c" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
                '<div class="tlbody c" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
                % (IN(top), IN(x + cw / 2 - 0.33), esc(st["tag"]),
                   IN(top + 0.86), IN(x), IN(cw), esc(st["title"]),
                   IN(top + 1.26), IN(x + 0.06), IN(cw - 0.12), esc(st["body"])))
    else:
        rh = (bot - top) / n
        big = n <= 3
        out.append('<div class="spine v" style="top:%dpx;left:%dpx;height:%dpx"></div>'
                   % (IN(top + 0.24), IN(ML + 0.37), IN(rh * (n - 1))))
        for i, st in enumerate(steps):
            y = top + i * rh
            out.append(
                '<div class="tltag" style="top:%dpx;left:%dpx">%s</div>'
                '<div class="tltitle%s" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
                '<div class="tlbody%s" style="top:%dpx;left:%dpx;width:%dpx">%s</div>'
                % (IN(y + 0.07), IN(ML), esc(st["tag"]),
                   " big" if big else "", IN(y + 0.06), IN(ML + 1.02), IN(2.72),
                   esc(st["title"]),
                   " big" if big else "", IN(y + 0.05), IN(ML + 3.90), IN(CW - 3.90),
                   esc(st["body"])))
            if i < n - 1:
                out.append('<div class="rowline" style="top:%dpx;left:%dpx;'
                           'width:%dpx"></div>'
                           % (IN(y + rh - 0.06), IN(ML + 1.02), IN(CW - 1.02)))
    return ('<div class="slide">' + h_header(spec) + "".join(out) +
            h_callout(spec, cal) + h_footnote(spec) + h_footer(page, total) + '</div>')


def r_table(spec, page, total):
    top = BODY_TOP_WITH_LEDE if spec.get("lede") else BODY_TOP_PLAIN
    heads, rows, widths = spec["headers"], spec["rows"], spec["widths"]
    compact = spec.get("compact", False)
    scale = CW / float(sum(widths))
    n = len(rows)
    avail = BODY_BOT - top
    head_h = 0.40
    row_h = min(0.60, (avail - head_h) / n)
    th = head_h + row_h * n
    ty = top + max(0.0, (avail - th) / 2)
    tag_col = spec.get("tag_col")
    row_colors = spec.get("row_colors")

    cols = "".join('<col style="width:%dpx">' % IN(w * scale) for w in widths)
    thead = "".join('<th%s>%s</th>'
                    % (' class="ctr"' if (compact and j == len(heads) - 1) else "",
                       esc(h)) for j, h in enumerate(heads))
    body = []
    for i, row in enumerate(rows):
        tds = []
        for j, val in enumerate(row):
            if tag_col is not None and j == tag_col:
                dom = DOMAINS.get(val, {"label": val, "color": "muted"})
                tds.append('<td class="tag ctr" style="color:%s">%s</td>'
                           % (col(dom["color"]), esc(dom["label"])))
            elif j == 0:
                c = row_colors[i] if (row_colors and row_colors[i]) else "ink"
                tds.append('<td class="c0" style="color:%s">%s</td>'
                           % (col(c), esc(val)))
            else:
                tds.append('<td>%s</td>' % esc(val))
        body.append('<tr class="%s" style="height:%dpx">%s</tr>'
                    % ("even" if i % 2 == 0 else "odd", IN(row_h), "".join(tds)))
    fsz = (';--bs:%.1fpx;--hs:%.1fpx' % (PT(spec["bs"]), PT(spec["hs"]))
           if spec.get("bs") or spec.get("hs") else '')
    tbl = ('<table class="tbl%s" style="top:%dpx;left:%dpx;width:%dpx%s">%s'
           '<thead><tr style="height:%dpx">%s</tr></thead>'
           '<tbody>%s</tbody></table>'
           % (" compact" if compact else "", IN(ty), IN(ML), IN(CW), fsz,
              "<colgroup>%s</colgroup>" % cols, IN(head_h), thead, "".join(body)))
    return ('<div class="slide">' + h_header(spec) + tbl + h_footnote(spec) +
            h_footer(page, total) + '</div>')


def r_diagram(spec, page, total):
    top, bot, cal = body_geom(spec)
    d = spec["diagram"]
    avail_h = bot - top
    w = min(CW, avail_h * DW / DH)
    h = w * DH / DW
    x0 = (SW - w) / 2.0
    y0 = top + max(0.0, (avail_h - h) / 2.0)
    k = w / float(DW)
    nodes = {n["id"]: n for n in d["nodes"]}

    # 连线（SVG，px 坐标，无 viewBox，箭头方向随线）
    colors = sorted({e.get("color", "navy2") for e in d["edges"]})
    markers = "".join(
        '<marker id="ah-%s" markerWidth="9" markerHeight="9" refX="7.5" refY="3.2" '
        'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L7,3.2 L0,6.4 Z" '
        'fill="%s"/></marker>' % (c, col(c)) for c in colors)
    lines = []
    for e in d["edges"]:
        (sx, sy), (tx, ty) = anchor_points(nodes[e["from"]], nodes[e["to"]])
        c = e.get("color", "navy2")
        dash = ' stroke-dasharray="6 4"' if e.get("kind") == "dashed" else ""
        lines.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                     'stroke-width="1.7"%s marker-end="url(#ah-%s)"/>'
                     % (sx * k, sy * k, tx * k, ty * k, col(c), dash, c))
        if e.get("label"):
            mx, my = (sx + tx) / 2 * k, (sy + ty) / 2 * k
            lw = 60
            lines.append('<rect x="%.1f" y="%.1f" width="%.1f" height="13" rx="6.5" '
                         'fill="%s"/><text x="%.1f" y="%.1f" class="elab" fill="%s">'
                         '%s</text>'
                         % (mx - lw / 2, my - 6.5, lw, col("bg"), mx, my + 3.4, col(c),
                            esc(e["label"])))
    svg = ('<svg width="%d" height="%d" style="position:absolute;left:%dpx;top:%dpx">'
           '<defs>%s</defs>%s</svg>'
           % (IN(w), IN(h), IN(x0), IN(y0), markers, "".join(lines)))

    # 图例 + 右上说明
    lg = []
    for i, item in enumerate(d.get("legend", [])):
        yy = 2 + i * 20
        c = "muted" if item["kind"] == "dashed" else "navy2"
        dash = ' stroke-dasharray="5 4"' if item["kind"] == "dashed" else ""
        lg.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                  'stroke-width="1.7"%s/><text x="%.1f" y="%.1f" class="lgd">%s</text>'
                  % (20 * k, (yy + 8) * k, 54 * k, (yy + 8) * k, col(c), dash,
                     62 * k, (yy + 12) * k, esc(item["text"])))
    lg.append('<text x="%.1f" y="%.1f" class="lgd b r" text-anchor="end">%s</text>'
              % (1180 * k, 14 * k,
                 esc("两站同机房 · 同一内网拓扑 · RTT 对等（延迟忽略不计）")))
    svg2 = ('<svg width="%d" height="%d" style="position:absolute;left:%dpx;top:%dpx">'
            '%s</svg>' % (IN(w), IN(h * 0.2), IN(x0), IN(y0), "".join(lg)))

    # 节点
    divs = []
    for nd in d["nodes"]:
        st = nd["style"]
        zone = nd.get("zone")
        x, y, nw, nh = x0 + nd["x"] * k, y0 + nd["y"] * k, nd["w"] * k, nd["h"] * k
        base = 'style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"' % (IN(x), IN(y),
                                                                     IN(nw), IN(nh))
        if st == "band":
            divs.append('<div class="nband" %s>%s</div>' % (base, esc(nd["title"])))
            continue
        klass, tstyle, bstyle = "node " + st, "", ""
        if st == "zone":
            klass += " " + zone
            tstyle = "color:%s;font-size:%dpx" % (col(zone), PT(11.5))
            bstyle = "font-size:%dpx" % PT(9)
        elif st == "actor":
            tstyle = "font-size:%dpx" % PT(10.5)
            bstyle = "font-size:%dpx" % PT(8)
        elif st == "gateway":
            tstyle = "font-size:%dpx" % PT(11.5)
            bstyle = "font-size:%dpx" % PT(9)
        elif st == "inner":
            klass += " " + (zone or "")
            tstyle = "font-size:%dpx" % PT(10)
            bstyle = "font-size:%dpx" % PT(8)
        elif st == "registry":
            tstyle = "font-size:%dpx" % PT(9.5)
            bstyle = "font-size:%dpx" % PT(7.5)
        else:
            tstyle = "font-size:%dpx" % PT(10.5)
            bstyle = "font-size:%dpx" % PT(8.5)
        body = ('<div class="nb" style="%s">%s</div>' % (bstyle, esc(nd["body"]))
                if nd.get("body") else "")
        divs.append('<div class="%s" %s><div class="nt" style="%s">%s</div>%s</div>'
                    % (klass, base, tstyle, esc(nd["title"]), body))

    return ('<div class="slide">' + h_header(spec) + svg + svg2 + "".join(divs) +
            h_callout(spec, cal) + h_footnote(spec) + h_footer(page, total) + '</div>')


def r_checklist(spec, page, total):
    top, bot, cal = body_geom(spec)
    groups = spec["groups"]
    gap = 0.30
    cw = (CW - gap * (len(groups) - 1)) / len(groups)
    ch = bot - top
    out = []
    for i, g in enumerate(groups):
        x = ML + i * (cw + gap)
        acc = g.get("accent", "accent")
        items = "".join('<li><b style="color:%s">\u25a1</b>%s</li>'
                        % (col(acc), esc(it)) for it in g["items"])
        out.append(
            '<div class="card plain" style="top:%dpx;left:%dpx;width:%dpx;'
            'height:%dpx"><div class="ckhead" style="background:%s">%s'
            '<em>%d 项</em></div><ul class="cklist" style="top:%dpx;left:%dpx;'
            'width:%dpx;bottom:%dpx">%s</ul></div>'
            % (IN(top), IN(x), IN(cw), IN(ch), col(acc), esc(g["title"]),
               len(g["items"]), IN(0.66), IN(0.22), IN(cw - 0.44), IN(0.20),
               items))
    return ('<div class="slide">' + h_header(spec) + "".join(out) +
            h_callout(spec, cal) + h_footnote(spec) + h_footer(page, total) + '</div>')


def r_closing(spec, page, total):
    n = len(spec["stats"])
    gap = 0.34
    cw = (CW - 2.2 - gap * (n - 1)) / n
    stats = []
    for i, st in enumerate(spec["stats"]):
        x = ML + i * (cw + gap)
        stats.append('<div class="stat" style="top:%dpx;left:%dpx;width:%dpx">'
                     '<i></i><b>%s</b><span>%s</span></div>'
                     % (IN(3.86), IN(x), IN(cw), esc(st["num"]),
                        esc(st["label"]).replace("\n", "<br>")))
    return ('<div class="slide dark">' + deco() +
            '<div class="etitle" style="top:%dpx;left:%dpx">%s</div>'
            '<div class="crule" style="top:%dpx;left:%dpx"></div>'
            '<div class="esub" style="top:%dpx;left:%dpx">%s</div>'
            '%s<div class="cmeta" style="top:%dpx;left:%dpx">%s</div>%s%s</div>'
            % (IN(1.62), IN(ML), esc(spec["title"]), IN(2.62), IN(ML),
               IN(2.86), IN(ML), esc(spec["subtitle"]), "".join(stats),
               IN(6.24), IN(ML), esc(spec["meta"]), bottom_bar(),
               h_footer(page, total, dark=True)))


RENDERERS = {"cover": r_cover, "toc": r_toc, "divider": r_divider,
             "points": r_points, "cards": r_cards, "timeline": r_timeline,
             "table": r_table, "diagram": r_diagram, "checklist": r_checklist,
             "closing": r_closing}

# ------------------------------------------------------------------- CSS ----
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#22303f;font-family:"Microsoft YaHei","PingFang SC","Hiragino Sans GB",
 "Noto Sans CJK SC","Source Han Sans SC",sans-serif;color:#1B2733;padding:26px 0 60px}
.bar{position:sticky;top:0;z-index:50;background:rgba(14,32,56,.96);color:#fff;
 padding:10px 24px;display:flex;gap:16px;align-items:center;flex-wrap:wrap;
 border-bottom:1px solid #1d3a5c}
.bar h1{font-size:14px;font-weight:700;letter-spacing:.4px}
.bar .sub{font-size:11.5px;color:#9FB4C9}
.bar a{font-size:12px;color:#0E2038;background:#12A5B8;padding:6px 12px;border-radius:14px;
 text-decoration:none;font-weight:700}
.bar a.ghost{background:#17324F;color:#9FB4C9;border:1px solid #24486e}
.bar .nav{margin-left:auto;display:flex;gap:4px;flex-wrap:wrap;max-width:52%}
.bar .nav button{background:#17324F;color:#9FB4C9;border:1px solid #24486e;font-size:11px;
 width:26px;height:22px;border-radius:4px;cursor:pointer;font-family:inherit}
.bar .nav button:hover,.bar .nav button.on{background:#12A5B8;color:#08242a;border-color:#12A5B8}
.slot{position:relative;width:100%;margin:0 auto 22px}
.slide{position:absolute;left:50%;top:0;margin-left:-640px;width:1280px;height:720px;
 background:#F4F7FA;transform-origin:top center;overflow:hidden;
 box-shadow:0 12px 34px rgba(0,0,0,.42)}
.slide.dark{background:#0E2038}
.slide>div,.slide>ul,.slide>table,.slide>svg{position:absolute}
.slide [style*="top:"]{position:absolute}
.rings i{position:absolute;border-radius:50%;display:block}
.bbar{position:absolute;left:0;bottom:0;width:1280px;height:13px}
.bbar i{position:absolute;top:0;height:13px;display:block}
/* 页眉页脚 */
.kicker{left:69px;font-size:13.3px;font-weight:700;color:#12A5B8;letter-spacing:1.5px}
.htitle{left:69px;font-size:33.3px;font-weight:700;color:#1B2733;line-height:1.15;
 width:1142px}
.htitle.dark,.dlede.dark{color:#fff}
.hrule{width:63px;height:4.3px;background:#12A5B8}
.hline{height:1px;background:#DCE3EC}
.hlede{font-size:15.3px;color:#6B7A8D;line-height:1.35}
.hlede.dark{color:#CBD6E2}
.fline{height:1px;background:#DCE3EC}.fline.dark{background:#17324F}
.footl,.footr{font-size:11.3px;color:#6B7A8D}.footr{text-align:right}
.footl.dark,.footr.dark{color:#8FA3B8}
.fnote{font-size:12px;color:#6B7A8D;line-height:1.3}.fnote.dark{color:#8FA3B8}
.callout{border-radius:9px;padding:9px 16px;display:flex;align-items:center}
.callout span{font-size:14px;line-height:1.32;color:#1B2733}
.rowline{height:1px;background:#DCE3EC}
.spine{height:2px;background:#DCE3EC}.spine.v{width:2px;height:auto}
/* 封面 */
.ckick{left:69px;font-size:16px;font-weight:700;color:#12A5B8;letter-spacing:2px}
.ctitle{left:69px;font-size:58.6px;font-weight:700;color:#fff;line-height:1.1}
.crule{width:110px;height:5.3px;background:#12A5B8}
.csub{left:69px;font-size:20px;color:#CBD6E2;line-height:1.35}
.cbadge{height:52px;line-height:50px;text-align:center;color:#fff;font-size:15.3px;
 font-weight:700;background:#17324F;border:1px solid #0F5F6B;border-radius:26px}
.cmeta{left:69px;font-size:13.3px;color:#8FA3B8}
/* 目录 */
.tno{background:#0E2038;color:#12A5B8;font-size:22.6px;font-weight:700;border-radius:11px;
 display:flex;align-items:center;justify-content:center}
.ttitle{font-size:19.3px;font-weight:700;color:#1B2733}
.ttitle span{font-size:13.3px;color:#12A5B8;font-weight:700;margin-left:12px}
.tdesc{font-size:14px;color:#6B7A8D;line-height:1.3}
.tn{height:33px;line-height:33px;text-align:center;background:#E4F6F8;color:#0B7C8B;
 font-size:12.6px;font-weight:700;border-radius:17px}
/* 章节页 */
.dno{left:63px;font-size:117px;font-weight:700;color:#1D3E60;line-height:1}
.dtitle{left:69px;font-size:45.3px;font-weight:700;color:#fff}
.den{left:69px;font-size:16.6px;font-weight:700;color:#12A5B8;letter-spacing:1.2px}
.dlede{left:69px;font-size:16.6px;color:#CBD6E2;line-height:1.35}
.dpill{height:42px;line-height:40px;padding:0 16px;text-align:center;color:#fff;
 font-size:14.6px;font-weight:700;background:#17324F;border:1px solid #0F5F6B;
 border-radius:21px}
/* 要点 */
.pchip{left:69px;width:50px;background:#E4F6F8;color:#0B7C8B;font-size:18.6px;
 font-weight:700;border-radius:10px;display:flex;align-items:center;justify-content:center}
.phead{font-size:19.3px;font-weight:700;color:#1B2733}
.pbody{font-size:15.3px;color:#6B7A8D;line-height:1.42}
/* 卡片 */
.card{background:#fff;border:1px solid #DCE3EC;border-radius:9px}
.card.plain{padding:0}
.card .strip{position:absolute;top:0;height:8px;border-radius:4px}
.ctitle{font-size:20px;font-weight:700;color:#1B2733;line-height:1.2}
.cen{font-size:12.6px;font-weight:700;letter-spacing:.4px}
.ctag{height:31px;line-height:31px;text-align:center;font-size:12px;font-weight:700;
 border-radius:16px}
.cbadge2{border-radius:50%;color:#fff;font-size:24px;font-weight:700;display:flex;
 align-items:center;justify-content:center}
.meter{height:16px;background:#E7EDF4;border-radius:8px;position:absolute}
.meter i{position:absolute;top:0;height:16px;border-radius:8px;display:block}
.mcap{font-size:11.3px;color:#6B7A8D}
.cbody{list-style:none;font-size:15.3px;line-height:1.35}
.cbody.small{font-size:14px}
.cbody li{position:relative;padding-left:17px;margin-bottom:9px;color:#1B2733}
.cbody li>b{position:absolute;left:0;top:0;font-weight:700}
/* 时间轴 */
.tlcircle{width:63px;height:63px;border-radius:50%;background:#0E2038;border:2px solid #12A5B8;
 color:#fff;font-size:22.6px;font-weight:700;display:flex;align-items:center;
 justify-content:center;margin-left:0}
.tltag{width:71px;height:33px;line-height:33px;text-align:center;background:#0E2038;
 color:#12A5B8;font-size:14px;font-weight:700;border-radius:17px}
.tltitle{font-size:18px;font-weight:700;color:#1B2733}
.tltitle.big{font-size:19.3px}
.tltitle.c{text-align:center;font-size:18.6px}
.tlbody{font-size:14px;color:#6B7A8D;line-height:1.4}
.tlbody.big{font-size:15.3px}
.tlbody.c{text-align:center;font-size:15.3px}
/* 表格 */
.tbl{border-collapse:collapse;left:69px}
.tbl th{background:#0E2038;color:#fff;font-size:var(--hs,14.6px);font-weight:700;text-align:left;
 padding:6px 10px;border:1px solid #0E2038}
.tbl td{font-size:var(--bs,14.6px);color:#1B2733;padding:6px 10px;border:1px solid #DCE3EC;
 line-height:1.3;vertical-align:middle}
.tbl.compact{--hs:13.3px;--bs:12.6px}
.tbl tr.even td{background:#fff}.tbl tr.odd td{background:#F2F6FA}
.tbl td.c0{font-weight:700}
.tbl td.tag{font-weight:700;font-size:12px}
.tbl .ctr,.tbl th.ctr{text-align:center}
/* 拓扑图 */
.node{border-radius:8px;padding:8px 10px;overflow:hidden}
.node .nt{font-weight:700;line-height:1.2}
.node .nb{color:#6B7A8D;line-height:1.25;margin-top:2px}
.node.actor{background:#0E2038;border-radius:16px;text-align:center;padding:5px}
.node.actor .nt{color:#fff}.node.actor .nb{color:#CBD6E2}
.node.gateway{background:#17324F;border:1.5px solid #12A5B8;border-radius:12px;
 text-align:center;padding:6px}
.node.gateway .nt{color:#fff}.node.gateway .nb{color:#9FE3EC}
.node.zone{border-radius:10px;padding:9px 12px}
.node.zone.blue{background:#E9F1FA;border:1.5px solid #2E6FB7}
.node.zone.green{background:#E7F6EF;border:1.5px solid #2E9E6B}
.node.zone .nb{color:#1B2733}
.node.inner{background:#fff;border-radius:7px;padding:6px 9px}
.node.inner.blue{border:1px solid #2E6FB7}.node.inner.green{border:1px solid #2E9E6B}
.node.inner .nt{color:#1B2733}
.node.registry{background:#fff;border:1px dashed #B7C4D2;border-radius:8px;padding:5px 9px}
.node.registry .nt{color:#0B7C8B}
.node.shared{background:#EDF2F8;border:1px solid #B9C9D9;border-radius:7px;padding:9px 11px}
.node.shared .nt{color:#1B2733}
.nband{text-align:center;color:#6B7A8D;font-size:13.3px;font-weight:700;line-height:1.6}
svg text.elab{font-size:11px;font-weight:700;text-anchor:middle;
 font-family:inherit}
svg text.lgd{font-size:11px;fill:#6B7A8D;font-family:inherit}
svg text.lgd.b{font-weight:700;fill:#0B7C8B}
/* 清单 */
.ckhead{position:absolute;top:0;left:0;right:0;height:44px;border-radius:9px 9px 0 0;
 color:#fff;font-size:16.6px;font-weight:700;display:flex;align-items:center;
 padding:0 20px;gap:10px}
.ckhead em{font-style:normal;font-size:12.6px;opacity:.85}
.cklist{list-style:none;font-size:14px;line-height:1.32}
.cklist li{position:relative;padding-left:21px;margin-bottom:10px;color:#1B2733}
.cklist li>b{position:absolute;left:0;top:0;font-weight:700}
/* 结尾 */
.etitle{left:69px;font-size:48px;font-weight:700;color:#fff}
.esub{left:69px;font-size:17.3px;color:#CBD6E2}
.stat{height:165px;background:#17324F;border:1px solid #0F5F6B;border-radius:8px;
 padding:24px}
.stat i{display:block;width:40px;height:5px;background:#12A5B8;margin-bottom:14px}
.stat b{display:block;color:#fff;font-size:36px;font-weight:700;line-height:1.1}
.stat span{display:block;color:#9FB4C9;font-size:14px;line-height:1.4;margin-top:10px}
.tip{color:#8FA3B8;font-size:12px;text-align:center;margin-top:6px}
@media print{
 body{background:#fff;padding:0}
 .bar,.tip{display:none}
 .slot{height:auto!important;page-break-after:always;margin:0}
 .slide{position:relative;left:0;margin:0;transform:none!important;box-shadow:none}
}
"""

JS = """
(function(){
  var slots=[].slice.call(document.querySelectorAll('.slot'));
  var btns=[].slice.call(document.querySelectorAll('.nav button'));
  function fit(){
    var s=Math.min(1,(document.documentElement.clientWidth-40)/1280);
    slots.forEach(function(el){
      el.style.height=(720*s)+'px';
      el.firstElementChild.style.transform='scale('+s+')';
    });
  }
  function go(i){
    i=Math.max(0,Math.min(slots.length-1,i));
    slots[i].scrollIntoView({behavior:'smooth',block:'start'});
  }
  function cur(){
    var y=window.scrollY+120,best=0;
    slots.forEach(function(el,i){if(el.offsetTop<=y)best=i;});
    return best;
  }
  btns.forEach(function(b,i){b.onclick=function(){go(i);};});
  document.addEventListener('keydown',function(e){
    var c=cur();
    if(e.key==='ArrowRight'||e.key==='PageDown'||e.key===' '){e.preventDefault();go(c+1);}
    if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();go(c-1);}
    if(e.key==='Home'){go(0);} if(e.key==='End'){go(slots.length-1);}
  });
  var t;window.addEventListener('scroll',function(){
    clearTimeout(t);t=setTimeout(function(){
      var c=cur();btns.forEach(function(b,i){b.classList.toggle('on',i===c);});
    },80);
  });
  window.addEventListener('resize',fit);fit();
})();
"""


def build(out_path, pptx_name=None, slides=None, meta=None, extra_links=""):
    """slides: 指定要渲染的幻灯片列表（默认 deck_content.SLIDES）。"""
    slides = SLIDES if slides is None else slides
    meta = META if meta is None else meta
    total = len(slides)
    parts = []
    navs = []
    for i, spec in enumerate(slides, 1):
        inner = RENDERERS[spec["kind"]](spec, i, total)
        parts.append('<div class="slot" id="s%d">%s</div>' % (i, inner))
        navs.append('<button title="%s">%02d</button>'
                    % (esc(spec.get("title", spec["kind"])), i))
    dl = ('<a href="%s" download>下载 .pptx</a>' % quote(pptx_name)
          if pptx_name else "")
    doc = ("<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
           "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
           "<title>%s · 网页速览版</title><style>%s</style></head><body>"
           "<div class=\"bar\"><h1>%s</h1><span class=\"sub\">网页速览版 · %d 页 · "
           "← → 翻页 · 可打印为 PDF</span>%s%s"
           "<div class=\"nav\">%s</div></div>%s"
           "<p class=\"tip\">最终以 .pptx 为准：网页版仅用于快速校对内容与版面。</p>"
           "<script>%s</script></body></html>"
           % (esc(meta["title"]), CSS, esc(meta["title"]), total, dl, extra_links,
              "".join(navs), "".join(parts), JS))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return out_path
