# 体检系统（HMSC）核心领域全景流程图

> 本文档与 [domain-entities.md](file:///D:/coder/代码/体检/docs/domain-entities.md)、[CONTEXT-MAP.md](file:///D:/coder/代码/体检/CONTEXT-MAP.md) 及 [hmsc-service/CONTEXT.md](file:///D:/coder/代码/体检/hmsc-service/CONTEXT.md) 保持完全一致。
>
> **核心建模约定**：
> 1. **单链归属**：`Benefit（体检权益） ➔ Order（主订单，含 0 元统付单） ➔ Appointment（预约单）`。
> 2. **顶层配置层级**：`Project（1，核心端为主权威源、MIS 补充） ➔ TeamOrder（N，年度/批次周期） ➔ Group（数据层二级组别，前台不露出） ➔ ProductPackage（P 员工包 / G 家属包）`。
> 3. **双入口汇流**：同时承接「一体化选检加车结算锁单」与「已支付待预约主订单独立选店/重约」两条路径。

---

## 一、体检业务端到端全景主流程图

```mermaid
flowchart LR
    subgraph S1["阶段1：顶层配置与权益发放"]
        P["Project 企业项目\n(核心端主配置 / MIS补充)"] --> TO["TeamOrder 团单\n(1:N 年度周期/理赔标识)"]
        TO --> GRP["Group 组别\n(数据层部门/批次分组，前台不露出)"]
        GRP --> PP["ProductPackage 产品包\n(P员工 / G家属 + 增值子产品)"]
        E1["HR批量导入 / 免密SSO\n卡密兑换 / 自费优惠购"] --> B["Benefit 体检权益\n(有效期/次数门禁)"]
        PP -.-> B
    end

    subgraph S2["阶段2：鉴权与准入门禁"]
        B --> L["白名单/免密登录\n自动绑定 User/Staff/Holder"]
        L --> G1{"一级合规门禁\n隐私与健康信息授权"}
        G1 -- "已同意" --> G2{"团单开启商保直赔?"}
        G2 -- "是" --> CL["ClaimApplication\n身份证OCR + 手写签名\n合成PDF -> SFTP归档211核心"]
        G2 -- "否" --> SEL_ENTRY["进入体检选购入口"]
        CL --> SEL_ENTRY
    end

    subgraph S3["阶段3：智能选检与双向选购"]
        SEL_ENTRY -. "可选辅助" .-> AI["AI套餐推荐\n(问卷 / 历史报告异步打分)\n& 套餐对比 (标准医学字典)"]
        AI -. "自动勾选/参考" .-> PICK["双向选购与硬校验\n选套餐加项 <-> 选分院排期\n适检/互斥/预算帽/交集匹配"]
        SEL_ENTRY --> PICK
    end

    subgraph S4["阶段4：结算与主订单确立"]
        PICK --> CART["CartItem 加车\n-> CombinationOrder 合并结算"]
        CART --> PAY["积分两阶段冻结(镜像账本)\n+ 现金支付 / 0元统付确认\n+ 15分钟排期临时占容"]
        PAY --> ORD["Order 主订单 (单持有人)\n+ SubOrder 明细落标"]
        REBOOK["已支付待预约 Order\n(优惠转单 / 取消重约回流)"] --> ORD
    end

    subgraph S5["阶段5：预约履约与异常变更"]
        ORD --> G3{"二级合规门禁\n企业劳资健康承诺书"}
        G3 -- "已签署(年度绑定)" --> APT["Appointment 预约单\n(主套餐+加项合并原子交付)"]
        APT --> SUP_ON["线上直连供应商 API\n实时锁单 -> 成功(02)/失败(07)"]
        APT --> SUP_OFF["线下公立医院 / 特批协调\n申请中 -> 人工协调 -> 确认"]
        SUP_ON & SUP_OFF -. "变更/异常" .-> CHG["同店改期 / 取消重约(过期熔断)\n停业降级协调 / 超期释放 / 退款"]
    end

    subgraph S6["阶段6：到检核销、报告与闭环"]
        SUP_ON & SUP_OFF --> CHK["双轨到检同步 (已到检 04)\n确立供应商采购结算里程碑"]
        CHK --> RPT["Report PDF 报告\n大模型OCR解析 -> 归档HMES"]
        RPT --> VAS["小诺AI免登(解读/心理) / C24·C59手动&自动解读\n在线客服(BGJD) / 家庭共用 / HR看板"]
    end

    subgraph S7["并行路径：院外报销与积分变现"]
        B -. "与预约互斥(01)\n或异常复检(02)" .-> REIM_M["MedicalReimbursement\n体检代报销(双抬头/原件寄送)\n全额核准 / 05原单改卡重推"]
        L -. "员工本人健康消费\n三类积分源1:1冻结" .-> REIM_P["PointsReimbursement\n积分报销(仅个人发票)\n打款回调转实扣 / 05保冻重推"]
    end
```

---

## 二、子图 1：上游配置、4 路权益发放与准入门禁流

覆盖 `Project` / `TeamOrder` / `ProductPackage` 配置、4 条权益来源、ToB 免密动态赋权、一级隐私门禁与商保直赔前置门禁（ADR-0011、ADR-0013、ADR-0014）。

```mermaid
flowchart TD
    subgraph CFG["上游配置 (核心端为主权威源，MIS为补充)"]
        PRJ["Project 企业项目\n长期规则 / 门户 / 屏蔽日 / 停业策略 / 加项上限 / AI开关"]
        PRJ -->|"1 : N"| TO["TeamOrder 团单\n年度周期 / 团险保单同步 / 理赔标识 / 承诺书周期"]
        TO -->|"1 : N"| GRP["Group 组别 (数据层)\n按部门/职级/批次收敛权益范围"]
        GRP --> PP["ProductPackage 产品包\n员工包(P) / 家属包(G) / 分院白名单 / C24·C59子产品"]
        PP --> MP["MedicalPackage 体检套餐\n00标准 / 02升级 / 03加价 / 01加项"]
    end

    subgraph SRC["4 路体检权益生成途径"]
        S1["1. HR 批量导入\nImportBatch -> StaffMember"]
        S2["2. ToB 免密 SSO 动态导入\n/jump/:projectCode + Apollo岗位规则"]
        S3["3. 健康商城卡密兑换\nCardVoucher (checkGardPassword)\n核销即永久锁死不可退"]
        S4["4. 自费优惠套餐购买\n支付成功直接生成权益与待预约 Order"]
    end

    S1 & S2 & S3 & S4 --> BEN["Benefit 体检权益\n状态: EFFECTIVE (有效待预约)"]
    BEN --> AUTH["白名单四要素 / 免密鉴权\n自动建档绑定 User + StaffMember + Holder"]

    AUTH --> GATE1{"一级合规门禁\n隐私政策与个人健康信息授权"}
    GATE1 -- "拒绝" --> BLOCK1["阻断访问核心功能"]
    GATE1 -- "同意 -> 写入 ConsentRecord" --> CLAIM_CHK{"团单/保单是否开启\n商保直赔标识 (claimsType)?"}

    CLAIM_CHK -- "否 (普通福利/自费)" --> PASS["准入通过 -> 进入选检首页"]
    CLAIM_CHK -- "是 (EWP团险 / SWP个险)" --> OCR["强制理赔前置资料门禁\n身份证正反面 OCR + 实时手写电子签名"]
    OCR -- "未完成" --> BLOCK2["阻断后续预约流程"]
    OCR -- "完成" --> PDF["mergeClaimsData 动态盖章\n合成《体检理赔申请授权书 PDF》"]
    PDF --> SFTP["ClaimsDataEvent 异步专线 SFTP\n归档至 211 保险核心结案"]
    PDF --> PASS
```

---

## 三、子图 2：智能选检、双向选购与两阶段积分结算流

覆盖 **AI 套餐推荐（问卷/报告双入口）**、**套餐对比**、双向交集匹配、购物车合并结算、积分两阶段冻结与双边镜像账本（ADR-0001、ADR-0003、ADR-0004、ADR-0005、ADR-0006、ADR-0009）。

```mermaid
flowchart TD
    START["准入通过 (持有有效 Benefit)"] --> OPT{"是否使用智能选检辅助?"}

    subgraph SMART["智能选检 (可选决策辅助子环节)"]
        OPT -- "AI 套餐推荐" --> REC_IN{"推荐入口"}
        REC_IN -- "健康问卷测评" --> Q1["填写/复用历史测评问卷"]
        REC_IN -- "历史体检报告" --> Q2["提交/引用历史报告\nsubmitReport"]
        Q1 & Q2 --> REC_JOB["创建 RecommendationRecord\n状态: 01-推荐中 (异步大数据模型)"]
        REC_JOB --> REC_RES{"推荐结果"}
        REC_RES -- "02-推荐完成" --> AUTO["返回主套餐/加项分值 + 补充检查项\n+ 报告AI解读 -> 回填选检页默认勾选"]
        REC_RES -- "03-推荐失败" --> MANUAL["降级为自主选购"]

        OPT -- "套餐对比" --> CMP["无状态套餐对比服务 (comparePacket)\n基于 MedicalItem 标准医学字典\n实时输出候选套餐共有项/差异项/价格"]
        CMP --> PICK
    end

    OPT -- "直接选购" --> PICK
    AUTO & MANUAL --> PICK

    subgraph SELECT["双向选购与硬规则校验"]
        PICK["双向选购路径\n路径A: 先选套餐加项 -> 后选分院排期\n路径B: 先选分院排期 -> 后选套餐加项"]
        PICK --> CHK_RULE["核心业务不变量校验:\n1. 适检人口门禁 (性别/婚否)\n2. 主干单选互斥 (00/02/03 选1)\n3. 加项医学互斥 & 预算帽\n4. 套餐门店交集匹配 & 机构私有编码映射\n5. 项目屏蔽日 & 分院停业展示策略"]
    end

    CHK_RULE --> MODE{"结算与建单路径"}

    MODE -- "一体化路径 (含多持有人/家属共济)" --> CART["加入 CartItem (草稿不占容)\n支持员工积分共济支付家属包(G)"]
    CART --> COMB["提交结算 -> 瞬态 CombinationOrder\n按持有人拆分为独立 Order (1:1 Holder)"]
    COMB --> ZERO{"应付现金与积分是否为 0\n(纯企业统付)?"}

    ZERO -- "是 (0 元统付)" --> ORD_PAID["确立 Order (PAID_WAIT_APPOINT)\nSubOrder 明细落标 -> 自动进入预约锁单"]
    ZERO -- "否 (需扣积分/付现金)" --> HOLD["1. 排期临时占容 (15分钟超时释放)\n2. 外部积分预冻结 + ShadowLedgerRecord 双边镜像\n(优先抵扣主干升级/加价，后抵加项，SKU级穿透)"]
    HOLD --> PAY_RES{"收银台支付结果"}
    PAY_RES -- "支付成功回调" --> CONFIRM_PT["积分预冻结转实扣 + 清理 CartItem\nCombinationOrder 解体 -> 确立 Order"]
    PAY_RES -- "超时/取消未付" --> RELEASE_PT["释放 15 分钟占容 + 积分原路解冻\nOrder 取消"]

    MODE -- "两段式回流 (优惠套餐转单 / 取消重约)" --> EXIST_ORD["已有已支付待预约 Order\n独立选分院排期后直接发起预约"]
    CONFIRM_PT & ORD_PAID & EXIST_ORD --> TO_APT["进入阶段5：二级合规门禁与预约履约"]
```

---

## 四、子图 3：预约履约与异常变更流

覆盖二级劳资承诺书门禁、合并原子履约、线上直连 vs 线下协调、原分院同店改期、当日不对称改退、权益过期熔断、分院停业降级、超期未到检自动释放及退款级序（ADR-0002、ADR-0005、ADR-0007、ADR-0008、ADR-0012、ADR-0014）。

```mermaid
flowchart TD
    IN["待预约 Order (含主套餐+全部加项 SubOrder)"] --> G2{"二级合规门禁\n项目是否要求企业劳资健康承诺书?"}
    G2 -- "是且当期团单未签" --> SIGN["在线签署 ConsentRecord\nShaRsaUtil 哈希存证 + 定制邮件PDF留档"]
    SIGN --> BUNDLE
    G2 -- "否 / 当期团单已签" --> BUNDLE["合并原子履约封装\n主套餐 + 全部加项打包为单一 Appointment"]

    BUNDLE --> ROUTE{"供应商履约类型与排期模式"}
    ROUTE -- "线上直连供应商 (17+ 民营连锁 API)" --> API["实时调用机构独立适配器 API 锁单"]
    API -- "锁单成功" --> CONFIRMED["Appointment: CONFIRMED (预约成功 02)\nOrder: APPOINTED / Benefit: LOCKED"]
    API -- "超时/售罄 (即时同步失败策略)" --> FAIL07["Appointment: 预约失败 (07)\n不异步死循环重试，提示用户重选"]

    ROUTE -- "线下公立医院 / 特批协调排期 / 团检报名(0030)" --> PENDING["Appointment: PENDING (申请中)\n团检报名入口隔离过滤专属线下门店\n按核心排期落标 groupCheck(Y/N) -> 导出聚合 Excel 名单"]
    PENDING --> OFFLINE["客服人工对接医院协调加号/确认排期"]
    OFFLINE -- "医院确认" --> CONFIRMED

    CONFIRMED --> EVENT{"履约前变更或异常事件"}

    EVENT -- "1. 同店改期" --> RESCHED["原分院同店改期 (禁跨店)\n保持原 appointmentCode 不变\n体检日当天允许改至后续日期\n(线下改期动态刷新 groupCheck 标识)"]
    EVENT -- "2. 主动取消预约" --> DAYOF{"是否为体检日当天?"}
    DAYOF -- "是 (当日不对称规则)" --> DENY_C["默认禁止当天主动取消\n仅引导同店改期"]
    DAYOF -- "否" --> DO_CANCEL["取消 Appointment -> 释放机构排期\nOrder 恢复待预约 / Benefit 释放锁定"]
    DO_CANCEL --> EXP_GUARD{"权益是否已过期?\n(benefitEndTime < Today)"}
    EXP_GUARD -- "未过期" --> REBOOK["允许重新选分院发起新预约"]
    EXP_GUARD -- "已过期 (熔断门禁)" --> EXP_BLOCK["严禁再次选店预约\n锁死企业福利预算敞口"]

    EVENT -- "3. 分院停业/下线" --> DOWNGRADE["分院停业降级策略\n不静默退单 -> 降级为线下协调模式\n客服外呼协助改约至同品牌临近分院"]

    EVENT -- "4. 超期未到检 (No-show)" --> OVERDUE["定时任务按工作日/节假日推算\nAppointment: OVERDUE_RELEASED\n自动释放排期并恢复 Order 待预约"]

    EVENT -- "5. 申请退款 (自费/混合单)" --> REFUND["前置校验/级联取消关联 Appointment\n发起资金原路退款"]
    REFUND --> CB_PT["资金退款成功异步回调\n驱动外部积分平台退还积分\n(失败重试，超限转人工)"]
    CB_PT --> REFUNDED["Order: REFUNDED"]
```

---

## 五、子图 4：双轨到检核销、报告解读（手动/自动/小诺AI免登）与对账闭环流

覆盖双轨状态同步、已到检（04）供应商采购结算里程碑、大模型 OCR 统一解析归档 HMES、自主外院历史报告隔离、C24/C59 手动前置开放门禁与四条件自动申请、小诺健康 AI 多 Agent 免登（报告解读/心理咨询 + 隐私门禁）、保险在线客服（`BGJD`）与 HR 异常监控看板（ADR-0008、ADR-0010、ADR-0012、ADR-0016）。

```mermaid
flowchart TD
    APT["Appointment: CONFIRMED (预约成功)"] --> TRACK{"到检与报告回传双轨通道"}

    TRACK -- "线上民营连锁" --> POLL["后台定时任务主动轮询拉取\n(到检名单 + 原版 PDF 报告\n原生私有 JSON 拉取已弃用)"]
    TRACK -- "线下公立医院" --> MIS["MIS 后台运营批量导入 Excel\n或单笔核销并上传报告扫描件"]

    POLL & MIS --> CHKIN["Appointment: CHECKED_IN (已到检 04)\nBenefit: CONSUMED (权益核销)"]

    CHKIN --> SETTLE["供应商采购结算里程碑\n以已到检(04)确立采购成本发生\n驱动对账核销 (不等待报告/解读)"]
    CHKIN --> EVAL["分院口碑评价 (自愿提交)\n仅作前台选店参考，不联动供应商扣款"]

    CHKIN --> PDF_IN["体检中心出具原版 PDF 报告\nAppointment: REPORTED (05) / Order: FINISHED"]
    PDF_IN --> OCR["统一大模型 OCR 结构化解析管道\n抽取临床检测值与 AbnormalFinding"]
    OCR --> HMES["归档至健康档案系统 (HMES)\n员工账号支持家庭报告共用查看"]

    PAST["用户自主上传的外院历史报告"] -. "物理隔离" .-> LOCAL["仅保留移动端个人查阅\n不入 HMES、不污染官方趋势比对"]

    HMES --> XN["小诺健康 AI 多Agent免登\n(体检AI解读 / 心理咨询等)\n隐私门禁 pushCustomerInfoFlag -> 回查加密PDF"]
    HMES --> CS["保险在线客服免登\n(BGJD 报告解读 / PTZX 普通咨询)"]

    PDF_IN --> AUTO_CHK{"四条件自动申请门禁\n电子授权书+类型+门店自动授权+C24/C59余次?"}
    AUTO_CHK -- "全部满足" --> DOC_PIPE["创建/更新 HMC 托管 ReportInterpretation 工单\n(新建扣次/补传不重扣，归属真实持有人 hmcId)\n异步推送三方专科医生 -> 回写结构化结论"]

    APT -. "手动前置门禁 anomlndexInterpreType\n(01-已到检/出报告 | 02-预约日当天及之后)" .-> MAN_UP["合并机构报告与用户自传当次报告(上限30份)\n统一归档 HMES 供医生阅片"]
    MAN_UP --> DOC_PIPE

    HMES --> HR_DASH["B端企业异常指标监控看板\n面向 HR 呈现团队异常分布与解读概况"]
```

---

## 六、子图 5：`Benefit` / `Order` / `Appointment` 三态联动状态机

明确单链模型下三大核心聚合根的状态演进与跨聚合事件联动。

```mermaid
stateDiagram-v2
    state "Benefit (体检权益)" as B_GRP {
        [*] --> B_EFF : 导入/免密/卡密兑换/自费购买
        B_EFF : EFFECTIVE (有效待预约)
        B_LOCK : LOCKED (预约锁定中)
        B_CONS : CONSUMED (已核销闭环)
        B_EXP : EXPIRED (已过期失效)
        B_REV : REVOKED (离职减员/退单作废)

        B_EFF --> B_LOCK : 确认主订单并发起预约
        B_LOCK --> B_EFF : 预约取消/超期释放 (未过期)
        B_LOCK --> B_EXP : 预约取消/超期释放 (已过期熔断)
        B_LOCK --> B_CONS : 分院已到检(04) / 已出报告(05)
        B_EFF --> B_EXP : 超过 benefitEndTime
        B_EFF --> B_REV : HR减员冻结 / 全额退款核销
    }

    state "Order (主订单 - 单持有人)" as O_GRP {
        [*] --> O_WPAY : 自费/混合下单 (15分钟占容)
        [*] --> O_PAID : 0元纯统付确认 / 优惠套餐转单
        O_WPAY : WAIT_BUYER_PAY (待支付)
        O_PAID : PAID_WAIT_APPOINT (已支付/待预约)
        O_APT : APPOINTED (已预约/履约中)
        O_FIN : FINISHED (已出报告闭环)
        O_REF : REFUNDED (已退款)

        O_WPAY --> O_PAID : 支付成功回调 (积分转实扣)
        O_WPAY --> [*] : 超时未付自动取消 (解冻积分)
        O_PAID --> O_APT : 发起预约 (线上锁单/线下申请)
        O_APT --> O_PAID : 预约取消 / 锁单失败(07) / 超期释放
        O_APT --> O_FIN : 到检并出具报告
        O_PAID --> O_REF : 发起退款 (回调驱动退积分)
        O_APT --> O_REF : 级联先取消预约 -> 退款
    }

    state "Appointment (预约单 - 合并原子履约)" as A_GRP {
        [*] --> A_PEND : 线下公立医院 / 特批协调
        [*] --> A_CONF : 线上直连 API 实时锁单成功
        [*] --> A_FAIL : 线上直连锁单失败 (07)
        A_PEND : PENDING (申请中/待确认)
        A_CONF : CONFIRMED (预约成功 02)
        A_CHK : CHECKED_IN (已到检 04)
        A_RPT : REPORTED (已出报告 05)
        A_CAN : CANCELLED (已取消)
        A_OVR : OVERDUE_RELEASED (超期未到检释放)
        A_FAIL : FAILED (预约失败 07)

        A_PEND --> A_CONF : 客服协调医院确认排期
        A_PEND --> A_CAN : 取消申请
        A_CONF --> A_CONF : 原分院同店改期 (单号不变)
        A_CONF --> A_PEND : 分院停业降级线下协调
        A_CONF --> A_CAN : 主动取消 (体检日当天默认禁止)
        A_CONF --> A_OVR : 超期未到检定时自动释放
        A_CONF --> A_CHK : 双轨同步已到检 (触发采购结算)
        A_CHK --> A_RPT : PDF报告回传 + 大模型OCR归档
    }
```

---

## 七、子图 6：体检代报销与积分报销全景流程

覆盖 `MedicalReimbursement`（体检报销 `01` 与预约互斥、复检报销 `02` 独立共存、支持员工及家属、双抬头发票与 `08-待寄送发票原件`）、`PointsReimbursement`（仅限员工本人、仅个人发票、三类积分源两阶段核销）、全额核准不部分核减以及 `05-付款失败` 原单改卡免复审直推（ADR-0015）。

```mermaid
flowchart TD
    subgraph MED["路径 A：体检代报销 (MedicalReimbursement，支持员工本人与家属)"]
        M_TYPE{"报销类型"}
        M_TYPE -- "01 体检报销" --> M_EX{"权益互斥门禁\n同一权益是否已有预约/有效报销?"}
        M_EX -- "是" --> M_BLK["硬阻断：您已使用体检权益，无法再报销"]
        M_EX -- "否" --> M_SUB["提交个人/公司双抬头发票与体检凭证\n状态: 01-审核中"]
        M_TYPE -- "02 复检报销\n(首次体检异常后)" --> M_REC["校验独立复检权益 (reimburseRecheckCode)\n可与首次体检共存"] --> M_SUB

        M_SUB --> M_ACT{"审核与用户操作"}
        M_ACT -- "用户撤销" --> M_CAN["04-已取消 (终态)"]
        M_ACT -- "需原件核验" --> M_MAIL["08-待寄送发票原件 -> 核验通过"]
        M_ACT -- "审核驳回 (All-or-Nothing)" --> M_REJ["06-审核未通过 (终态，修正后重提)"]
        M_ACT -- "全额审核通过" --> M_WAIT["02-待付款 -> 推送核心财务打款"]
        M_MAIL --> M_WAIT

        M_WAIT --> M_PAY{"核心财务打款回调"}
        M_PAY -- "成功" --> M_DONE["03-已付款 (终态)"]
        M_PAY -- "失败" --> M_FAIL["05-付款失败\n原单号不变，修改银行卡跳过复审直推"]
        M_FAIL --> M_WAIT
    end

    subgraph PTS["路径 B：积分报销 (PointsReimbursement，仅限员工本人个人发票)"]
        P_SUB["提交个人健康消费发票\n(单项体检/疫苗/牙科/眼科/健身瑜伽，无原件寄送)"] --> P_FRZ["按 1:1 预冻结积分\n(核心 / 薪福通 / 福粒三类积分源)\n状态: 01-审核中"]
        P_FRZ --> P_ACT{"审核与用户操作"}
        P_ACT -- "用户撤销 / 全额驳回" --> P_REL["04-已取消 / 06-审核未通过\n驱动积分原路解冻返还 (终态)"]
        P_ACT -- "全额审核通过\n(不支持部分核减)" --> P_WAIT["02-待付款 -> 推送核心财务打款"]

        P_WAIT --> P_PAY{"核心财务打款回调"}
        P_PAY -- "成功" --> P_DONE["03-已付款\n驱动冻结积分转实扣 (终态)"]
        P_PAY -- "失败" --> P_FAIL["05-付款失败\n保持积分冻结不退回，原单改卡跳过复审直推"]
        P_FAIL --> P_WAIT
    end
```
