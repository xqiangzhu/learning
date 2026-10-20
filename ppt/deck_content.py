# -*- coding: utf-8 -*-
"""
体检系统升级 V2 · 领域术语表 —— PPT 内容模型（单一事实来源）

内容严格来自 CONTEXT.md（领域术语表），不新增未经文档证实的实现细节；
凡属"按术语关系推导"的编排（如切流时序、检查清单），均在页脚显式标注。

同一份 SLIDES 数据被两个渲染器消费：
  * render_pptx.py  -> .pptx（交付物）
  * render_html.py  -> index.html（网页速览版，便于在浏览器里先过一遍）

布局类型（kind）：
  cover / toc / divider / points / cards / timeline / table / diagram / checklist / closing
"""

# ---------------------------------------------------------------- 视觉规范 ----

FONT = "Microsoft YaHei"          # 与仓库 PlantUML 图内字体保持一致
FONT_HEAD = "Microsoft YaHei"

C = {
    "navy":    "0E2038",          # 深色底（封面 / 章节页 / 结尾）
    "navy2":   "17324F",
    "ink":     "1B2733",          # 正文
    "muted":   "6B7A8D",          # 次要文字
    "line":    "DCE3EC",          # 分隔线
    "bg":      "F4F7FA",          # 内容页底
    "card":    "FFFFFF",
    "accent":  "12A5B8",          # 主强调（青）
    "accentd": "0B7C8B",
    "accentl": "E4F6F8",
    "blue":    "2E6FB7",          # 蓝区 / 超算区
    "blue_l":  "E9F1FA",
    "green":   "2E9E6B",          # 绿区 / 南湾区
    "green_l": "E7F6EF",
    "red":     "C9435A",          # 红线 / 禁止
    "red_l":   "FDECEE",
    "amber":   "D98A2B",          # 风险 / 门禁
    "amber_l": "FCF2E2",
    "white":   "FFFFFF",
}

META = {
    "title": "体检系统升级V2 · 领域术语表与切流发布架构",
    "author": "体检系统升级V2 架构组",
    "subject": "统一语言 / 蓝绿双站 / 整站全量原子切流",
    "comments": "由 CONTEXT.md（领域术语表）生成，配套 ADR 0001-0005",
}

FOOTER = "体检系统升级 V2 · 领域术语表（Ubiquitous Language）"
SOURCE = "来源：CONTEXT.md · 关联决策：ADR 0001–0005 · 生成日期 2026-10-20"

# 术语域（用于章节页 / 速查表标签）
DOMAINS = {
    "site":  {"label": "站点",       "color": "blue"},
    "route": {"label": "路由",       "color": "accent"},
    "db":    {"label": "数据库",     "color": "amber"},
    "cut":   {"label": "发布过渡",   "color": "green"},
}

# ------------------------------------------------------------ 图形坐标系 ----
# diagram 使用 1200 x 490 的归一化坐标（宽高比与内容区一致），
# PPTX 按内容区等比映射，HTML 按百分比定位。
DW, DH = 1200, 425

TOPOLOGY = {
    "nodes": [
        # --- 顶部：用户 -> L0 总开关 ---
        {"id": "user", "x": 470, "y": 0, "w": 260, "h": 48, "style": "actor",
         "title": "用户 / 客户端", "body": "浏览器 · App · 第三方接入"},

        {"id": "l0", "x": 150, "y": 62, "w": 900, "h": 52, "style": "gateway",
         "title": "L0 统一入口 · 整站全量流量总开关",
         "body": "前置高可用入口反向代理层｜权重严格 100:0 或 0:100 原子切换"},

        # --- 蓝区（超算区） ---
        {"id": "zblue", "x": 20, "y": 130, "w": 570, "h": 176, "style": "zone",
         "zone": "blue", "title": "超算区 / 蓝区 · 10.142 网段",
         "body": "原有应用集群 · 常态主业务流量 · 挂载全量数据层"},
        {"id": "bl1", "x": 46, "y": 186, "w": 210, "h": 48, "style": "inner",
         "zone": "blue", "title": "L1 站点接入层",
         "body": "本站静态资源分发 + API 反向代理"},
        {"id": "bapp", "x": 286, "y": 186, "w": 278, "h": 48, "style": "inner",
         "zone": "blue", "title": "应用集群  CLUSTER_ZONE=blue",
         "body": "本站前端必调本站后端 · RPC 严格同区"},
        {"id": "breg", "x": 286, "y": 242, "w": 278, "h": 46, "style": "registry",
         "zone": "blue", "title": "独立注册中心集群（蓝）",
         "body": "服务发现与绿区互不干扰"},

        # --- 绿区（南湾区） ---
        {"id": "zgreen", "x": 610, "y": 130, "w": 570, "h": 176, "style": "zone",
         "zone": "green", "title": "南湾区 / 绿区 · 10.20 网段",
         "body": "新建应用集群 · 同机房同内网 · RTT 与超算对等（延迟忽略不计）"},
        {"id": "gl1", "x": 636, "y": 186, "w": 210, "h": 48, "style": "inner",
         "zone": "green", "title": "L1 站点接入层",
         "body": "本站静态资源分发 + API 反向代理"},
        {"id": "gapp", "x": 876, "y": 186, "w": 278, "h": 48, "style": "inner",
         "zone": "green", "title": "应用集群  CLUSTER_ZONE=green",
         "body": "切流后承接 100% 生产流量（窗口承压）"},
        {"id": "greg", "x": 876, "y": 242, "w": 278, "h": 46, "style": "registry",
         "zone": "green", "title": "独立注册中心集群（绿）",
         "body": "服务发现与蓝区互不干扰"},

        # --- 共享层标签 + 三个共享组件 ---
        {"id": "band", "x": 380, "y": 308, "w": 440, "h": 20, "style": "band",
         "title": "共享层 · 两站共用（网络共生，数据不分裂）"},
        {"id": "db", "x": 20, "y": 330, "w": 372, "h": 86, "style": "shared",
         "title": "共享单数据库 · 全量数据层",
         "body": "膨胀与收缩（Expand & Contract）：只增不改，稳定≥1 周期后再收缩"},
        {"id": "redis", "x": 414, "y": 330, "w": 372, "h": 86, "style": "shared",
         "title": "统一 Redis（集中部署在超算站）",
         "body": "跨站会话共享：分布式 Token 共享，切流瞬间免于重新登录"},
        {"id": "mq", "x": 808, "y": 330, "w": 372, "h": 86, "style": "shared",
         "title": "MQ 消费 + 定时任务（单活）",
         "body": "仅接流集群激活，待命端自动挂起，杜绝并发竞争与重复记账"},
    ],
    "edges": [
        {"from": "user",  "to": "l0",    "kind": "solid"},
        {"from": "l0",    "to": "bl1",   "kind": "solid", "label": "100%"},
        {"from": "l0",    "to": "gl1",   "kind": "dashed", "label": "0% 待命",
         "color": "muted"},
        {"from": "bl1",   "to": "bapp",  "kind": "solid"},
        {"from": "gl1",   "to": "gapp",  "kind": "solid"},
        {"from": "bapp",  "to": "breg",  "kind": "dashed", "color": "muted"},
        {"from": "gapp",  "to": "greg",  "kind": "dashed", "color": "muted"},
        {"from": "zblue", "to": "db",    "kind": "solid", "color": "muted"},
        {"from": "zgreen", "to": "mq",   "kind": "solid", "color": "muted"},
    ],
    "legend": [
        {"kind": "solid",  "text": "常态流量路径"},
        {"kind": "dashed", "text": "待命 / 服务发现（控制面）"},
    ],
    "callout": {"color": "red",
                "text": "区域亲和路由（ADR 0003）：两站同机房同内网、网络层可直通，"
                        "隔离靠「独立注册中心 + CLUSTER_ZONE 标签」实现，杜绝同内网跨站串门调用"},
}

# ------------------------------------------------------------------ 幻灯片 ----

SLIDES = [

    # 01 封面 -----------------------------------------------------------------
    {"kind": "cover",
     "kicker": "体检系统升级 V2 · CONTEXT.md",
     "title": "领域术语表与切流发布架构",
     "subtitle": "统一语言 Ubiquitous Language｜蓝绿双站 · 整站全量原子切流",
     "badges": ["4 个术语域", "14 个核心术语", "5 篇 ADR"],
     "meta": SOURCE},

    # 02 导读 -----------------------------------------------------------------
    {"kind": "points",
     "kicker": "HOW TO READ",
     "title": "这份 PPT 讲什么",
     "lede": "只收录领域术语定义，不含临时实现细节；术语与 ADR 一一对应，评审时统一说法。",
     "items": [
         {"head": "一个核心判断",
          "body": "所谓「双端 / 双站」不是物理异地双机房，而是网络共生、逻辑完全隔离的蓝绿发布集群。"},
         {"head": "一条流量主线",
          "body": "L0 做 100:0 ↔ 0:100 的整站原子拨动，不做渐进式金丝雀；验证全部走站点直连内部域名。"},
         {"head": "三条配套铁律",
          "body": "数据库只增不改（膨胀与收缩）、任务与 MQ 消费单活、前端 HTML 零缓存并自愈重载。"},
         {"head": "阅读顺序",
          "body": "站点 → 网关与路由 → 数据库演进 → 发布过渡机制 → 术语速查 / ADR 索引 / 落地检查清单。"},
     ],
     "footnote": "术语口径以 CONTEXT.md 为准；实现细节以 ADR 与发布手册为准。"},

    # 03 目录 -----------------------------------------------------------------
    {"kind": "toc",
     "kicker": "AGENDA",
     "title": "目录",
     "items": [
         {"no": "01", "title": "基础设施 · 站点",
          "en": "Site / Cluster Zone",
          "desc": "超算区（蓝区）· 南湾区（绿区）· 逻辑双站", "n": "3 个术语"},
         {"no": "02", "title": "网关与流量路由",
          "en": "Routing & Ingress",
          "desc": "L0 统一入口 · L1 站点接入层 · 区域亲和路由 · 整站全量原子切流", "n": "4 个术语"},
         {"no": "03", "title": "数据库与演进模型",
          "en": "Database Evolution",
          "desc": "膨胀与收缩 Expand & Contract · 破坏性变更一票否决", "n": "2 个术语"},
         {"no": "04", "title": "发布与过渡机制",
          "en": "Cutover Mechanics",
          "desc": "连接排空 · 跨站会话共享 · 单活任务/消费者 · HTML 零缓存自愈 · 发版窗口承压",
          "n": "5 个术语"},
         {"no": "05", "title": "速查与落地",
          "en": "Reference & Checklist",
          "desc": "术语速查表 · ADR 索引 · 落地检查清单", "n": "3 页"},
     ]},

    # 04 一页看懂（拓扑图） ----------------------------------------------------
    {"kind": "diagram",
     "kicker": "ARCHITECTURE IN ONE PAGE",
     "title": "一页看懂：网络共生、逻辑隔离的蓝绿双站",
     "lede": "同一机房同一内网的两套应用集群，通过独立注册中心 + 区域标签隔离；"
             "数据层与缓存集中共享，任务与消费单活。",
     "diagram": TOPOLOGY},

    # 05 章节页 01 ------------------------------------------------------------
    {"kind": "divider", "no": "01", "title": "基础设施 · 站点",
     "en": "Site / Cluster Zone",
     "terms": ["超算区 / 蓝区", "南湾区 / 绿区", "逻辑双站 / 蓝绿集群"],
     "lede": "先厘清「双站到底是什么」：不是异地双机房，而是同内网里的两套蓝绿集群。"},

    # 06 蓝区 vs 绿区 ---------------------------------------------------------
    {"kind": "cards",
     "kicker": "站点 · SITE / CLUSTER ZONE",
     "title": "蓝区与绿区：同机房同内网的两套集群",
     "cols": 2,
     "cards": [
         {"title": "超算区 / 蓝区", "en": "Supercomputing Zone",
          "tag": "常态主业务流量", "accent": "blue",
          "meter": [100, 0],
          "body": ["原有应用集群，10.142 网段",
                   "与南湾区同机房、同一内网",
                   "承载常态主业务流量",
                   "挂载全量数据层",
                   "统一 Redis 集中部署在本站（跨站会话共享）"]},
         {"title": "南湾区 / 绿区", "en": "Nanwan Zone",
          "tag": "新建 · 待命 / 接流", "accent": "green",
          "meter": [0, 100],
          "body": ["新建应用集群，10.20 网段",
                   "同属同机房同一内网拓扑",
                   "RTT 与超算对等，延迟忽略不计",
                   "独立注册中心集群，服务发现互不干扰",
                   "切流后独自承接 100% 生产流量"]},
     ],
     "footnote": "两站通过各自独立的注册中心集群隔离服务发现 —— 网络共生，逻辑隔离。"},

    # 07 逻辑双站 -------------------------------------------------------------
    {"kind": "table",
     "kicker": "站点 · SITE / CLUSTER ZONE",
     "title": "逻辑双站 / 蓝绿集群：四个维度的准确口径",
     "lede": "Logical Dual Clusters —— 评审时最容易说错的一个词，按下面四行统一说法。",
     "headers": ["维度", "CONTEXT.md 口径"],
     "widths": [2.5, 9.4],
     "rows": [
         ["本质", "网络共生、逻辑完全隔离的蓝绿发布集群；不是物理异地双机房"],
         ["目的", "实现环境隔离与快速切流；不追求物理异地双机房形态"],
         ["网络位置", "同机房、同一内网拓扑；RTT 与超算对等，跨站网络延迟忽略不计"],
         ["隔离手段", "各自独立的注册中心集群隔离服务发现 + CLUSTER_ZONE 区域亲和路由"],
     ],
     "row_colors": ["blue", None, None, "green"],
     "footnote": "推论：网络层不阻断跨站调用，隔离责任落在「注册中心 + 标签路由」上（详见 ADR 0003）。"},

    # 08 章节页 02 ------------------------------------------------------------
    {"kind": "divider", "no": "02", "title": "网关与流量路由",
     "en": "Routing & Ingress",
     "terms": ["L0 统一入口", "L1 站点接入层", "区域亲和路由", "整站全量原子切流"],
     "lede": "两层网关决定「流量去哪个站、站内前后端如何闭合」，标签路由决定「不许跨站串门」。"},

    # 09 L0 / L1 --------------------------------------------------------------
    {"kind": "cards",
     "kicker": "路由 · ROUTING & INGRESS",
     "title": "两层网关：L0 管去向，L1 管闭合",
     "cols": 2,
     "cards": [
         {"title": "L0 统一入口", "en": "L0 Ingress Gateway",
          "tag": "整站总开关", "accent": "accent",
          "body": ["部署于前置的高可用入口反向代理层",
                   "承担整站全量流量的「总开关」角色",
                   "控制超算与南湾的权重分配",
                   "严格执行 100:0 或 0:100 原子切换",
                   "不提供中间态权重（无金丝雀）"]},
         {"title": "L1 站点接入层", "en": "L1 Site Ingress",
          "tag": "站内闭合", "accent": "blue",
          "body": ["站点内部的前置接入层",
                   "分发本站静态前端资源",
                   "反向代理后端 API 请求",
                   "铁律：本站前端必调本站后端",
                   "上线验证可直连本站内部域名"]},
     ],
     "footnote": "L0 只做「全量拨向哪一站」；站内前后端的对应关系由 L1 保证，两层职责不混用。"},

    # 10 区域亲和路由 ---------------------------------------------------------
    {"kind": "timeline",
     "kicker": "路由 · ROUTING & INGRESS｜ADR 0003",
     "title": "区域亲和路由：Zone-Affinity Routing",
     "lede": "同内网意味着网络层默认可达，跨站「串门」只能靠元数据标签与注册中心隔离来杜绝。",
     "horizontal": True,
     "steps": [
         {"tag": "①", "title": "注入标签",
          "body": "微服务实例启动时注入所属集群元数据标签 CLUSTER_ZONE"},
         {"tag": "②", "title": "同区调用",
          "body": "RPC 客户端严格只调用同一区域的服务实例"},
         {"tag": "③", "title": "隔离生效",
          "body": "杜绝同内网跨站串门调用，蓝绿两站互不干扰"},
     ],
     "callout": {"color": "red",
                 "text": "红线：出现跨区 RPC 调用即视为隔离失效 —— 会让「原子切流」失去意义，"
                         "用户在两个版本之间被混调。"},
     "footnote": "决策依据：ADR 0003 cross-cluster-service-isolation（跨集群服务隔离）。"},

    # 11 整站全量原子切流 -----------------------------------------------------
    {"kind": "cards",
     "kicker": "路由 · ROUTING & INGRESS｜ADR 0005",
     "title": "整站全量原子切流：Atomic All-or-Nothing Cutover",
     "cols": 3,
     "cards": [
         {"title": "切换前", "en": "100 : 0", "tag": "蓝区接全量",
          "accent": "blue", "meter": [100, 0],
          "body": ["超算区承载常态主业务流量", "南湾区待命：任务与消费挂起", "版本 N 在线上运行"]},
         {"title": "瞬时拨动", "en": "No Canary", "tag": "不做金丝雀",
          "accent": "amber",
          "body": ["不采用渐进式金丝雀权重", "流量只在 100:0 与 0:100 之间瞬时拨动", "无中间态、无按用户比例灰度"]},
         {"title": "切换后", "en": "0 : 100", "tag": "绿区接全量",
          "accent": "green", "meter": [0, 100],
          "body": ["南湾区承接全量生产流量", "上线验证依托站点直连内部域名", "版本 N+1 生效"]},
     ],
     "callout": {"color": "accent",
                 "text": "目的：杜绝用户在两个版本间反复横跳；代价：接流站必须独自扛住 100% 流量"
                         "（见「发版窗口承压」）。"},
     "footnote": "决策依据：ADR 0005 atomic-cutover-no-canary（原子切流、不做金丝雀）。"},

    # 12 章节页 03 ------------------------------------------------------------
    {"kind": "divider", "no": "03", "title": "数据库与演进模型",
     "en": "Database Evolution",
     "terms": ["膨胀与收缩 Expand and Contract", "破坏性变更一票否决"],
     "lede": "共享单数据库是原子切流的前提，也是最大的回滚风险点：所以 Schema 只能先膨胀、后收缩。"},

    # 13 膨胀与收缩 -----------------------------------------------------------
    {"kind": "timeline",
     "kicker": "数据库 · DATABASE EVOLUTION｜ADR 0002",
     "title": "膨胀与收缩：Expand and Contract",
     "lede": "针对共享单数据库系统的两阶段架构演进模式，用「时间差」换「可回滚」。",
     "steps": [
         {"tag": "Expand", "title": "膨胀：只新增，不修改",
          "body": "发布新版时只新增字段或表，同时兼顾新旧两个版本的读写；老字段保持原样可用。"},
         {"tag": "Soak", "title": "稳定期：至少一个周期",
          "body": "新版本稳定运行至少一个周期后再动手清理；这段时间就是回滚窗口。"},
         {"tag": "Contract", "title": "收缩：物理下线老字段",
          "body": "确认无需回滚后，物理下线并删除老字段，收敛数据模型。"},
     ],
     "callout": {"color": "green",
                 "text": "验收口径：回滚至旧版本代码时，数据库仍可无痛读写 —— 这是 Expand 阶段"
                         "「兼顾新旧版本」的唯一目的。"},
     "footnote": "决策依据：ADR 0002 database-expand-and-contract（数据库膨胀与收缩）。"},

    # 14 破坏性变更一票否决 ---------------------------------------------------
    {"kind": "cards",
     "kicker": "数据库 · DATABASE EVOLUTION",
     "title": "破坏性变更一票否决：Destructive DDL Ban",
     "lede": "线上发版前严格禁止以下三类 DDL —— 任何一条都会让「回滚到旧版本代码」直接失败。",
     "cols": 3,
     "cards": [
         {"title": "字段重命名", "en": "RENAME COLUMN", "badge": "×", "accent": "red",
          "body": ["旧版本代码按老名字读写", "发版即报错、回滚也报错", "替代：新增新名字段，兼容新旧版本"]},
         {"title": "存量表加非空字段", "en": "ADD NOT NULL", "badge": "×", "accent": "red",
          "body": ["存量行没有值，写入即失败", "旧版本 INSERT 不带新列", "替代：新增可空字段，应用层写默认值"]},
         {"title": "即时删表 / 删列", "en": "DROP TABLE/COLUMN", "badge": "×", "accent": "red",
          "body": ["跳过稳定期直接物理下线", "回滚窗口被一次性销毁", "替代：留到稳定期后的 Contract 阶段"]},
     ],
     "callout": {"color": "amber",
                 "text": "口径：破坏性 DDL 不是「谨慎执行」，而是「发版前一票否决」；"
                         "清理动作只允许出现在稳定期之后的 Contract 阶段。"},
     "footnote": "替代做法列为 Expand & Contract 模式的直接推论（ADR 0002）。"},

    # 15 章节页 04 ------------------------------------------------------------
    {"kind": "divider", "no": "04", "title": "发布与过渡机制",
     "en": "Cutover Mechanics",
     "terms": ["连接排空", "跨站会话共享", "单活任务 / 消费者管控",
               "HTML 零缓存与自愈重载", "发版窗口承压"],
     "lede": "原子拨动只是一瞬间；真正决定发版成败的是拨动前后的这五个过渡机制。"},

    # 16 切流时序 -------------------------------------------------------------
    {"kind": "timeline",
     "kicker": "发布过渡 · CUTOVER MECHANICS",
     "title": "切流时序：拨动前后各发生什么",
     "lede": "按 CONTEXT.md 的术语关系推导的顺序示意，用于评审对齐；具体 SOP 以发布手册与演练脚本为准。",
     "steps": [
         {"tag": "T1", "title": "L0 原子拨动",
          "body": "整站全量原子切流：权重 100:0 → 0:100 瞬时拨动，不设中间态。"},
         {"tag": "T2", "title": "用户无感接管",
          "body": "跨站会话共享：统一 Redis（超算站）共享 Token，切流瞬间免于重新登录。"},
         {"tag": "T3", "title": "单活任务切换",
          "body": "新接流站激活 MQ 拉取消费与定时任务调度，原接流站自动挂起，杜绝重复记账。"},
         {"tag": "T4", "title": "旧站连接排空",
          "body": "切断新请求流入后，允许在途写事务与长请求自然收敛结束，等待活跃连接归零。"},
         {"tag": "T5", "title": "旧站方可动工",
          "body": "活跃连接归零后才允许关闭或更新应用，避免事务中断与数据悬空。"},
         {"tag": "T6", "title": "窗口承压观察",
          "body": "接流站以精简合署节点扛全量：P95 恶化 <20% 为门禁，超限触发扩容预案。"},
     ],
     "callout": {"color": "accent",
                 "text": "前端并行生效：HTML 零缓存 + Chunk 加载异常捕获，发现版本落后即自动优雅重载，"
                         "避免老页面调新接口白屏（ADR 0004）。"},
     "footnote": "T1–T6 为按术语依赖关系推导的示意顺序，非 CONTEXT.md 原文编号。"},

    # 17 三大保障 -------------------------------------------------------------
    {"kind": "cards",
     "kicker": "发布过渡 · CUTOVER MECHANICS",
     "title": "拨动瞬间的三大保障：会话、任务、前端",
     "cols": 3,
     "cards": [
         {"title": "跨站会话共享", "en": "Cross-site Shared Session",
          "tag": "用户不重登", "accent": "blue",
          "body": ["统一 Redis 集中部署在超算站", "实现分布式 Token 共享",
                   "切流瞬间用户免于重新登录"]},
         {"title": "单活任务 / 消费者管控", "en": "Single-Active Task & MQ Consumer",
          "tag": "ADR 0001", "accent": "green",
          "body": ["同一时刻仅接流集群激活", "MQ 拉取消费 + 定时任务调度",
                   "待命端自动挂起", "杜绝并发竞争消费与重复记账"]},
         {"title": "HTML 零缓存与自愈重载", "en": "Zero-Cache HTML & Self-Healing Reload",
          "tag": "ADR 0004", "accent": "amber",
          "body": ["Web 入口文件禁止一切强缓存", "框架集成 Chunk 加载异常捕获",
                   "切流 / 版本落后时自动优雅重载", "避免老页面调新接口白屏"]},
     ],
     "footnote": "三者共同保证「瞬时拨动」对用户与数据都是无感的：会话不断、账不重复、页面不白屏。"},

    # 18 发版窗口承压 ---------------------------------------------------------
    {"kind": "cards",
     "kicker": "发布过渡 · CUTOVER MECHANICS",
     "title": "发版窗口承压：Release-Window Capacity Acceptance",
     "lede": "不做金丝雀的代价 —— 接流站要在发版窗口内独自承接 100% 生产流量，这是已接受的风险。",
     "cols": 2,
     "cards": [
         {"title": "已接受的风险", "en": "Accepted Risk", "tag": "允许性能降级",
          "accent": "amber",
          "body": ["承接 100% 生产流量的站点", "以精简合署节点承载",
                   "发版窗口内允许性能降级", "属于事前明示、已被接受的风险"]},
         {"title": "门禁与预案", "en": "Gate & Fallback", "tag": "超限即扩容",
          "accent": "green",
          "body": ["P95 恶化上限 <20%（量化门禁）", "全链路演练验证通过（准入门禁）",
                   "超限触发扩容预案", "与「整站全量原子切流」配套生效"]},
     ],
     "footnote": "结论：风险可以接受，但必须有量化门禁（P95 <20%）与演练证据，超限就走扩容预案。"},

    # 19 术语速查 1/2 ---------------------------------------------------------
    {"kind": "table",
     "kicker": "REFERENCE 1/2",
     "title": "术语速查表（1/2）：站点 · 网关与流量路由",
     "compact": True,
     "headers": ["术语", "英文", "一句话定义", "域"],
     "widths": [2.3, 2.7, 6.0, 0.9],
     "tag_col": 3,
     "rows": [
         ["超算区 / 蓝区", "Supercomputing Zone",
          "原有集群（10.142 网段），同机房同内网，承载常态主业务流量，挂载全量数据层", "site"],
         ["南湾区 / 绿区", "Nanwan Zone",
          "新建集群（10.20 网段），同机房同内网、RTT 对等；独立注册中心隔离服务发现", "site"],
         ["逻辑双站 / 蓝绿集群", "Logical Dual Clusters",
          "网络共生、逻辑完全隔离的蓝绿发布集群，用于环境隔离与快速切流，非物理异地双机房", "site"],
         ["L0 统一入口", "L0 Ingress Gateway",
          "前置高可用入口反代，整站全量流量总开关，权重严格 100:0 或 0:100 原子切换", "route"],
         ["L1 站点接入层", "L1 Site Ingress",
          "站内前置接入层，分发本站静态资源并反代 API：本站前端必调本站后端", "route"],
         ["区域亲和路由", "Zone-Affinity Routing",
          "实例启动注入 CLUSTER_ZONE 标签，RPC 严格同区调用，杜绝跨站串门（ADR 0003）", "route"],
         ["整站全量原子切流", "Atomic All-or-Nothing Cutover",
          "不做金丝雀，流量在 100:0 与 0:100 间瞬时拨动；验证依托站点直连内部域名（ADR 0005）", "route"],
     ]},

    # 20 术语速查 2/2 ---------------------------------------------------------
    {"kind": "table",
     "kicker": "REFERENCE 2/2",
     "title": "术语速查表（2/2）：数据库演进 · 发布与过渡机制",
     "compact": True,
     "headers": ["术语", "英文", "一句话定义", "域"],
     "widths": [2.3, 2.7, 6.0, 0.9],
     "tag_col": 3,
     "rows": [
         ["膨胀与收缩", "Expand and Contract",
          "先只新增字段/表以兼顾新旧版本，稳定至少一个周期后再物理下线老字段（ADR 0002）", "db"],
         ["破坏性变更一票否决", "Destructive DDL Ban",
          "发版前禁止字段重命名、存量表直接加非空字段、即时删表删列", "db"],
         ["连接排空", "Connection Draining",
          "切断新请求后允许在途写事务与长请求收敛，活跃连接归零才可关闭或更新应用", "cut"],
         ["跨站会话共享", "Cross-site Shared Session",
          "统一 Redis 集中部署在超算站，共享分布式 Token，切流瞬间免于重新登录", "cut"],
         ["单活任务 / 消费者管控", "Single-Active Task & MQ Consumer",
          "仅接流集群激活 MQ 消费与定时任务调度，待命端挂起，杜绝重复记账（ADR 0001）", "cut"],
         ["HTML 零缓存与自愈重载", "Zero-Cache HTML & Self-Healing Reload",
          "入口 HTML 禁一切强缓存；Chunk 异常捕获后自动优雅重载，避免白屏（ADR 0004）", "cut"],
         ["发版窗口承压", "Release-Window Capacity Acceptance",
          "接流站以精简合署节点扛全量、允许性能降级；P95 恶化 <20% + 全链路演练为门禁", "cut"],
     ]},

    # 21 ADR 索引 -------------------------------------------------------------
    {"kind": "table",
     "kicker": "DECISIONS",
     "title": "ADR 索引：术语背后的决策记录",
     "lede": "术语只说「是什么」，ADR 说「为什么这么定」。评审时遇到分歧，回到对应 ADR。",
     "headers": ["ADR", "主题（据文件名）", "支撑的术语"],
     "widths": [1.1, 4.6, 6.2],
     "rows": [
         ["0001", "single-active-jobs-and-mq｜单活任务与 MQ 消费者",
          "单活任务 / 消费者管控、切流时序 T3"],
         ["0002", "database-expand-and-contract｜数据库膨胀与收缩",
          "膨胀与收缩、破坏性变更一票否决"],
         ["0003", "cross-cluster-service-isolation｜跨集群服务隔离",
          "区域亲和路由、逻辑双站 / 蓝绿集群"],
         ["0004", "frontend-cache-and-api-compatibility｜前端缓存与 API 兼容",
          "HTML 零缓存与自愈重载"],
         ["0005", "atomic-cutover-no-canary｜原子切流、不做金丝雀",
          "整站全量原子切流、发版窗口承压"],
     ],
     "row_colors": ["green", "amber", "accent", "amber", "blue"],
     "footnote": "ADR 原文位于源工程 docs/adr/ 目录；本页主题按文件名与 CONTEXT.md 的引用整理。"},

    # 22 落地检查清单 ---------------------------------------------------------
    {"kind": "checklist",
     "kicker": "CHECKLIST",
     "title": "落地检查清单：发版评审逐项打勾",
     "lede": "每条都对应一个术语口径；任何一条不满足，原子切流的前提就不成立。",
     "groups": [
         {"title": "路由与隔离", "accent": "accent",
          "items": ["L0 权重只有 100:0 / 0:100，无中间态",
                    "上线验证走站点直连内部域名，不依赖 L0 分流",
                    "每个实例启动都注入 CLUSTER_ZONE 标签",
                    "RPC 客户端无跨区调用（区域亲和生效）",
                    "蓝绿各自独立注册中心，互不注册"]},
         {"title": "数据库", "accent": "amber",
          "items": ["本次 DDL 只新增字段 / 表（Expand）",
                    "无字段重命名、无存量表加非空字段",
                    "无即时删表删列；老字段留到 Contract 阶段",
                    "回滚到旧版本代码可无痛读写数据库",
                    "稳定期 ≥ 一个周期后才安排收缩"]},
         {"title": "发布执行", "accent": "green",
          "items": ["切流后等在途事务收敛、活跃连接归零再动工",
                    "MQ 消费与定时任务仅一站激活，待命站挂起",
                    "Token / 会话走统一 Redis，切流不重登",
                    "HTML 入口零缓存 + Chunk 自愈重载已接入",
                    "全链路演练通过，P95 恶化 <20%，扩容预案就绪"]},
     ],
     "footnote": "清单为术语口径的可执行化整理（推导项），用于评审自检；不替代发布手册的正式 SOP。"},

    # 23 结尾 -----------------------------------------------------------------
    {"kind": "closing",
     "title": "谢谢 · 讨论与质询",
     "subtitle": "术语以 CONTEXT.md 为准，实现细节以 ADR 与发布手册为准",
     "stats": [
         {"num": "100:0", "label": "L0 原子切换\n无中间态权重"},
         {"num": "<20%", "label": "发版窗口 P95\n恶化上限门禁"},
         {"num": "≥1 周期", "label": "Expand 稳定期\n后才 Contract"},
     ],
     "meta": SOURCE},
]

# ------------------------------------------------------- 连线锚点（共用） ----
def anchor_points(a, b):
    """按两个节点框的相对位置选择连线锚点，返回归一化坐标 ((x1,y1),(x2,y2))。

    规则：竖直分离 -> 走竖线（源中心落在目标横向范围内时画垂直线）；
          水平分离 -> 走横线；否则退化为中心连线。
    """
    acx, acy = a["x"] + a["w"] / 2.0, a["y"] + a["h"] / 2.0
    bcx, bcy = b["x"] + b["w"] / 2.0, b["y"] + b["h"] / 2.0
    vsep = (b["y"] >= a["y"] + a["h"] - 4) or (a["y"] >= b["y"] + b["h"] - 4)
    hsep = (b["x"] >= a["x"] + a["w"] - 4) or (a["x"] >= b["x"] + b["w"] - 4)
    down, right = bcy > acy, bcx > acx
    if vsep and not hsep:
        sx = min(max(bcx, a["x"] + 10), a["x"] + a["w"] - 10)
        sy = a["y"] + a["h"] if down else a["y"]
        straight = (a["x"] + 6 <= sx <= a["x"] + a["w"] - 6 and
                    b["x"] + 6 <= sx <= b["x"] + b["w"] - 6)
        tx = sx if straight else min(max(acx, b["x"] + 10), b["x"] + b["w"] - 10)
        ty = b["y"] if down else b["y"] + b["h"]
    elif hsep:
        sy = min(max(bcy, a["y"] + 8), a["y"] + a["h"] - 8)
        sx = a["x"] + a["w"] if right else a["x"]
        ty = sy if (b["y"] + 6 <= sy <= b["y"] + b["h"] - 6) else \
            min(max(acy, b["y"] + 8), b["y"] + b["h"] - 8)
        tx = b["x"] if right else b["x"] + b["w"]
    else:
        sx, sy, tx, ty = acx, acy, bcx, bcy
    return (sx, sy), (tx, ty)
