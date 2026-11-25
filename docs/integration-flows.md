# 体检系统（HMSC）下游核心接口与系统集成时序图

> 本文档为体检领域全景的**系统集成层**配套文档，与纯业务语义的 [domain-flows.md](file:///D:/coder/代码/体检/docs/domain-flows.md)、[domain-entities.md](file:///D:/coder/代码/体检/docs/domain-entities.md)、[CONTEXT-MAP.md](file:///D:/coder/代码/体检/CONTEXT-MAP.md) 及 [hmsc-service/CONTEXT.md](file:///D:/coder/代码/体检/hmsc-service/CONTEXT.md) 保持严格分层与术语一致。
>
> **分层约定**：业务流程图不暴露具体 URL、Feign 客户端、MQ 队列或 SFTP 路径；所有跨系统接口契约、同步/异步通道、重试与降级策略均收敛于本文档。

---

## 一、下游系统集成全景拓扑

HMSC 边端微服务群（`hmsc-edge-enterprise` / `hmsc-edge-provider` / `hmsc-edge-cmb` / `hmsc-edge-support` / `hmsc-edge-ehr`）与调度中心（`hmsc-innovate-jobs` XXL-Job）通过 **核心中台网关（`member-core-health`）**、**RabbitMQ**、**专线 SFTP** 及 **国密/加密免登网关** 协同 8 大下游系统：

```mermaid
flowchart LR
    subgraph HMSC["HMSC 体检边端服务群 & 调度中心"]
        ENT["hmsc-edge-enterprise\n企业体检核心边端"]
        PRV["hmsc-edge-provider\n服务商/AI/咨询边端"]
        CMB["hmsc-edge-cmb\n招行/EPAY支付边端"]
        SUP["hmsc-edge-support\n外部回调接收边端"]
        JOB["hmsc-innovate-jobs\nXXL-Job 定时轮询与补偿"]
    end

    subgraph GW["核心代理层"]
        CORE["member-core-health\n(/corehealth 统一内部网关)"]
        SIGN["member-core-sign\n(/sign 电子签名服务)"]
    end

    subgraph DOWN["8 大下游核心系统"]
        HMC["1. HMC 核心系统\n项目/团单/权益/订单/预约/财务报销"]
        PTS["2. 外部积分福利平台 & 支付网关\n核心积分 / 福粒 / 薪福通 / EPAY"]
        SUPP["3. 17+ 线上直连体检供应商\n美年/爱康/瑞慈/嘉会等独立API"]
        TBDS["4. 大数据推荐服务 TBDS\n问卷/报告AI推荐 & 套餐对比"]
        INS211["5. 211 保险核心\n商保直赔理赔资料归档"]
        HMES["6. 健康档案系统 HMES & OCR\n大模型OCR解析与档案归档"]
        VAS["7. 报告解读服务\nDify普惠AI & C24/C59三方医生"]
        XN["8. 小诺健康 AI & 保险在线客服\n国密多Agent免登 / AES-GCM客服"]
    end

    ENT -- "Feign HTTP" --> CORE
    ENT -- "RabbitMQ Direct\n(订单/预约/改期/取消/报销)" --> HMC
    ENT -- "Feign HTTP\n(ICmbFeignClient)" --> CMB
    ENT -- "Feign HTTP\n(IElectricSignFeignClient)" --> SIGN
    ENT -- "专线 SFTP\n(ClaimsDataListener)" --> INS211
    ENT -- "SM4+SM3免登 / AES-GCM" --> XN
    XN -. "RSA令牌回查 PDF" .-> ENT
    PRV -- "Feign HTTP / SSE\n(IDifyFeignClient)" --> VAS
    JOB -- "HTTP 触发 / 补偿轮询" --> ENT
    JOB -- "分页推送 PDF" --> HMES

    CORE -- "配置/权益/容量/退款/报销" --> HMC
    CORE -- "扣减/取消/查单" --> PTS
    CORE -- "/inside/interface/{type}/*" --> SUPP
    CORE -- "/inside/tbds/*" --> TBDS
    CORE -- "/inside/hmes/*" --> HMES
    CORE -- "interpretEwpReportApply" --> VAS

    CMB -- "收银台/退款 & 异步回调" --> PTS
    TBDS -. "异步推荐结果回调" .-> SUP
    SUPP -. "部分机构取消回调(如爱康)" .-> ENT
    PTS -. "支付/退款异步回调" .-> ENT
    HMC -. "报销打款状态回调" .-> ENT
```

---

## 二、时序图 1：HMC 核心系统同步链路（配置/权益/占容 + MQ 异步同步）

覆盖项目/权益/门店排期实时查询、15 分钟排期占容与释放、以及主订单/预约单/改期/取消经由 RabbitMQ 异步同步至 HMC 核心（含“体检 + 增值服务”组合特殊单延迟同步与退款状态回推）。

```mermaid
sequenceDiagram
    autonumber
    actor User as 持有人 (PC/H5)
    participant ENT as hmsc-edge-enterprise
    participant CORE as member-core-health (IPhysicalExamFeignClient)
    participant MQ as RabbitMQ (ewp.hmc.hmcsc.*)
    participant HMC as HMC 核心系统
    participant JOB as hmsc-innovate-jobs

    rect rgb(245, 248, 255)
        Note over User,HMC: 阶段 A：选检前实时查询与硬校验（同步 Feign，带 Hystrix 降级）
        User->>ENT: 进入项目/查询权益与可约套餐
        ENT->>CORE: queryProjectConfiguration / queryStaffMemberEffBenefits
        CORE->>HMC: 读取项目配置与实时有效权益
        HMC-->>ENT: 返回项目规则、团单有效期与产品包
        User->>ENT: 双向选检（选套餐/门店/排期）
        ENT->>CORE: queryPacketListNew / queryStoreListNew / queryNewScheduleList
        ENT->>CORE: checkPackageMutual / queryDisableDateList / validateCashNew
        CORE-->>ENT: 返回交集门店、排期余量、屏蔽日与金额校验结果
    end

    rect rgb(245, 255, 248)
        Note over User,HMC: 阶段 B：下单占容与订单/预约同步（事务提交后异步 MQ）
        User->>ENT: 确认下单 / 提交预约
        ENT->>CORE: lockAppointNum (锁定分院当天排期容量 15 分钟)
        CORE-->>ENT: 占容成功
        ENT->>ENT: 本地事务落库 Order / SubOrder / Appointment，发布 OrderEvent / AppointmentEvent

        alt 普通体检单（事务 AFTER_COMMIT 触发 AppointmentListener）
            ENT->>MQ: PushMqDataServiceImpl 发送 Direct 消息 (ordersync / appointsync / modifydatesync / ordercancelsync)
            Note right of ENT: 首次发送异常自动即时重试 1 次；无论成败均写入 mq_log 留痕
            MQ->>HMC: 异步消费落盘主订单/预约单/改期/取消状态
        else 含增值服务子单的组合特殊单（haveAdditionalService == true）
            ENT->>ENT: dealAddPushOrder 暂不推 MQ，仅落 mq_log(type=05)
            JOB->>ENT: AddOrderSyncCompensationHandler 定时补偿同步
            ENT->>CORE: syncOrderService / syncServiceStep
            CORE->>HMC: 实时同步增值服务订单与预约步骤
        end
    end

    rect rgb(255, 248, 245)
        Note over ENT,JOB: 阶段 C：回滚释放与退款状态同步
        opt 下单/预约事务回滚（AFTER_ROLLBACK）
            ENT->>CORE: AppointmentListener 触发 lockAppointNum 释放占容
        end
        opt 订单发生退款
            ENT->>CORE: ewpPushRefundStatus(orderCode, refundStatus, epayRefundOrderCode)
            CORE->>HMC: 更新核心订单退款状态
            Note right of JOB: 推送失败由 PushEwpRufundStatusHandler 定时补偿重试
        end
    end
```

---

## 三、时序图 2：外部积分福利平台 & 支付网关两阶段结算与回调退积分链路

覆盖 **核心积分（`CoreIntegralServiceImpl`）**、**福粒平台（`FuLiIntegralServiceImpl`）**、**薪福通（`XinFuTongIntegralServiceImpl`）** 的双边镜像账本、SKU 级穿透扣减、超时查单、15 分钟未付自动释放，以及 **资金退款成功异步回调驱动退积分** 的事务级序（ADR-0004、ADR-0005、ADR-0006）。

```mermaid
sequenceDiagram
    autonumber
    actor User as 持有人
    participant ENT as hmsc-edge-enterprise
    participant CORE as member-core-health (IPhysicalExam / IXinFuTong)
    participant EXT as 外部积分平台 (福粒 / 薪福通)
    participant CMB as hmsc-edge-cmb & EPAY
    participant JOB as hmsc-innovate-jobs

    rect rgb(245, 248, 255)
        Note over User,EXT: 阶段 A：积分余额查询
        User->>ENT: 进入结算页查看可用积分
        ENT->>CORE: queryIntegral(核心) / getIntegralDetail(福粒/薪福通)
        CORE->>EXT: 查询员工可用福利积分余额
        EXT-->>ENT: 返回可用积分（严格 1:1 人民币等值）
    end

    rect rgb(245, 255, 248)
        Note over User,CMB: 阶段 B：下单两阶段预冻结（外部实扣/冻结 + 核心双边镜像账本）
        User->>ENT: 提交合并结算（CombinationOrder 拆单为独立 Order）
        ENT->>ENT: 按优先级分摊写入 SubOrder（先主干升级/加价，后加项）
        par 并发双边冻结（福粒/薪福通模式）
            ENT->>CORE: buildIntegralOrder（携带 sku_items: partner_sku/quantity/unit_price）
            CORE->>EXT: 外部积分平台下单扣减/冻结积分
            alt 薪福通返回 errorData == timeOut
                ENT->>CORE: queryOrderResult（自动查单重试确认终态）
            end
            EXT-->>ENT: 返回 thirdOrderCode
        and 并发核心镜像冻结
            ENT->>CORE: operationIntegral(type=01 预冻结)
            CORE-->>ENT: 镜像账本冻结成功
        end

        alt 存在应付现金（混合支付）
            ENT->>CMB: ICmbFeignClient.buildPayUrl
            CMB-->>User: 跳转招行/EPAY收银台支付
            CMB->>ENT: 异步回调 /epay/interface/epayPayNotifyNew
            ENT->>ENT: 校验验签 -> 积分预冻结转实扣 -> 清理 CartItem -> 推 OrderEvent
        else 15 分钟超时未支付
            JOB->>ENT: CancelEwpOrderNewHandler 扫描超时待付单
            ENT->>CORE: 释放 15 分钟占容 + 并发释放外部与核心积分
        end
    end

    rect rgb(255, 246, 246)
        Note over User,JOB: 阶段 C：混合退款（严格遵循“资金退款成功回调驱动退积分”）
        User->>ENT: 申请退款（先级联取消关联 Appointment）
        ENT->>CMB: ICmbFeignClient.cmbApplyRefund
        CMB->>ENT: 资金原路退回成功后异步回调 /epay/interface/epayRefundNotifyNew
        ENT->>ENT: 落标退款成功，触发并发退积分（releaseIntegral）
        par 并发退回外部与核心镜像积分
            ENT->>CORE: cancelIntegralOrder(oid / orderId, refundAmount)
            CORE->>EXT: 撤销外部积分订单退还积分
            alt 撤销异常或超时
                ENT->>CORE: getIntegralOrder(福粒) / queryCancelResult(薪福通) 反查终态
                opt 确认未撤销成功
                    ENT->>ENT: 写入 exception_records 待补偿表（不静默丢单）
                end
            end
        and 释放核心镜像积分
            ENT->>CORE: operationIntegral(type=03 释放/退还)
        end
        JOB->>ENT: CancelFuLiOrderHandler / CancelOrderIntegralFailHandler 定时补偿重试（超限告警转人工）
    end
```

---

## 四、时序图 3：17+ 线上直连体检供应商全生命周期链路

覆盖通过 `IAppointmentFeignClient`（`/inside/interface/{type}/*`）对接 17+ 民营体检连锁（爱康、美年、瑞慈、慈铭、嘉会、中科等）的排期查询、实时锁单（即时同步失败策略 `07`）、同店改期/取消、部分机构主动回调，以及 XXL-Job 定时轮询到检（`04` 采购结算里程碑）与原版 PDF 报告下载（ADR-0007、ADR-0008、ADR-0012）。

```mermaid
sequenceDiagram
    autonumber
    actor User as 持有人
    participant ENT as hmsc-edge-enterprise
    participant CORE as member-core-health (IAppointmentFeignClient)
    participant SUPP as 线上直连供应商 API (/{type}/* 17+ 独立适配器)
    participant JOB as hmsc-innovate-jobs

    rect rgb(245, 248, 255)
        Note over User,SUPP: 阶段 A：排期查询与实时锁单（合并原子履约 + 即时同步失败策略）
        User->>ENT: 选择分院与就检日期/时间段
        ENT->>CORE: /{type}/queryScheduleList & /{type}/queryStoreSchedulePeriod
        CORE->>SUPP: 实时拉取分院号源与时间段余量
        SUPP-->>ENT: 返回可约日期与时段
        User->>ENT: 提交预约（主套餐 + 全部加项合并打包）
        ENT->>CORE: /{type}/transformPacketCodeOffline（硬校验机构私有套餐编码映射）
        ENT->>CORE: /{type}/customerAppointment
        CORE->>SUPP: 独立适配器转换差异化报文并发起实时锁单
        alt 锁单成功
            SUPP-->>ENT: 返回外部预约单号
            ENT->>ENT: Appointment -> CONFIRMED(02) / Order -> APPOINTED / Benefit -> LOCKED
            opt 本地事务提交失败回滚（AFTER_ROLLBACK）
                ENT->>CORE: AppointmentListener 自动调用 /{type}/cancelAppointment 补偿（失败发告警邮件）
            end
        else 接口超时或排期售罄
            SUPP-->>ENT: 返回失败/超时
            ENT->>ENT: 即时落标 Appointment -> FAILED(07)，提示用户重选（严禁异步死循环重试）
        end
    end

    rect rgb(255, 250, 240)
        Note over User,SUPP: 阶段 B：同店改期、取消与异常回调
        alt 原分院同店改期（保持原 appointmentCode 不变）
            User->>ENT: 发起同店改期（体检日当天允许改至后续日期）
            ENT->>CORE: /{type}/modifyAppointmentDateV2 (或 modifyAppointmentDate)
            CORE->>SUPP: 同步修改外部预约日期
        else 主动取消预约（体检日当天默认禁止）
            User->>ENT: 发起取消预约
            ENT->>CORE: /{type}/cancelAppointment
            CORE->>SUPP: 释放外部机构排期
        else 机构侧主动取消回调（如爱康）
            SUPP->>ENT: POST /aikang/interface/aiKangNotify
            ENT->>ENT: 同步更新本地预约单取消状态并释放权益锁定
        else 超期未到检（No-show）
            JOB->>ENT: CancelOverdueAppointmentHandler 按工作日/节假日推算
            ENT->>CORE: /{type}/cancelAppointment -> 落标 OVERDUE_RELEASED 恢复待预约
        end
    end

    rect rgb(245, 255, 248)
        Note over ENT,JOB: 阶段 C：双轨定时轮询到检状态（04）与原版 PDF 报告下载（05）
        loop 定时轮询到检（UpdateToCheckStateHandler / SwpUpdateToCheckStateHandler）
            JOB->>ENT: 触发批量轮询已预约单
            ENT->>CORE: /{type}/queryPhysicalExamStatus / /{type}/queryAppointmentVid
            CORE->>SUPP: 拉取机构到检状态与 VID 名单
            SUPP-->>ENT: 返回已到检(04)
            ENT->>ENT: 落标 CHECKED_IN(04) & Benefit CONSUMED（确立供应商采购对账结算里程碑）
        end

        loop 定时轮询 PDF 报告（UpdateAppointReportStateHandler / SwpUpdateReportStateHandler）
            JOB->>ENT: 触发批量轮询已到检单
            ENT->>CORE: /{type}/checkAppointmentReportCreated -> /{type}/downloadAppointmentReport
            CORE->>SUPP: 下载原版 PDF 体检报告（原生 JSON 拉取已弃用）
            SUPP-->>ENT: 返回 PDF 文件流落地存储
            ENT->>ENT: 落标 REPORTED(05) / Order FINISHED（触发 HMES 归档与 C24/C59 解读事件）
        end
    end
```

---

## 五、时序图 4：大数据推荐服务 TBDS（智能选检异步推荐 & 套餐对比）

覆盖问卷推荐、历史体检报告异步推荐（`RecommendationRecord`：`01-推荐中` ➔ `02-推荐完成` / `03-推荐失败`）以及基于标准医学字典的无状态套餐对比（`AiQuestionnaireController`、`ITbdsFeignClient`、`TbdsController`）。

```mermaid
sequenceDiagram
    autonumber
    actor User as 持有人
    participant ENT as hmsc-edge-enterprise (AiQuestionnaireController)
    participant CORE as member-core-health (ITbdsFeignClient)
    participant TBDS as 大数据推荐服务 TBDS
    participant SUP as hmsc-edge-support (TbdsController)

    rect rgb(245, 248, 255)
        Note over User,TBDS: 场景 A：健康问卷测评推荐（同步/历史复用）
        User->>ENT: 请求推荐问卷 /ewp/interface/queryAIQuestionnaire
        ENT->>CORE: /inside/tbds/queryAIQuestionnaire(性别/年龄)
        CORE->>TBDS: 获取适龄健康风险问卷
        TBDS-->>User: 返回问卷题目
        User->>ENT: 提交答卷 /queryAIQuestionnaireResult（或复用 /queryHistoryAIQuestionnaireResult）
        ENT->>CORE: /inside/tbds/queryAIQuestionnaireResult
        CORE->>TBDS: 算法打分匹配主套餐与加项包
        TBDS-->>User: 返回 AiRecommendPackageResultDTO（自动勾选推荐项）
    end

    rect rgb(245, 255, 248)
        Note over User,SUP: 场景 B：历史体检报告异步推荐（双阶段提交 + 异步回调）
        User->>ENT: 上传/引用历史报告 /recommendPacket/submitReport
        ENT->>CORE: /inside/tbds/parseReportGetBaseInfo（校验报告姓名/证件号）
        ENT->>ENT: 创建 RecommendationRecord（状态 01-推荐中）
        ENT->>CORE: /inside/tbds/aiRecommendPackageByReport(候选套餐+报告路径)
        CORE->>TBDS: 异步提交大模型报告解析与推荐任务
        TBDS-->>ENT: 即时 ACK 受理成功
        Note over TBDS: 大数据模型异步解析异常指标并计算套餐推荐分值
        TBDS->>SUP: POST /tbds/interface/updateReportRecommendedPacketResult
        SUP->>ENT: 回写 RecommendationRecord 状态（02-推荐完成 / 03-推荐失败）与分值
        loop 前端短轮询查询结果
            User->>ENT: /recommendPacket/queryRecommendResultByReport
            ENT-->>User: 返回推荐主套餐/加项分值/补充检查项与报告解读（若 03-失败则降级自主选购）
        end
    end

    rect rgb(255, 250, 240)
        Note over User,TBDS: 场景 C：无状态套餐对比服务
        User->>ENT: 选择多个候选套餐 /comparePacket 或 /V2/comparePacket
        ENT->>CORE: /inside/tbds/comparePacket
        CORE->>TBDS: 基于 MedicalItem 标准医学字典比对
        TBDS-->>User: 实时返回共有项、差异项与价格对比矩阵
    end
```

---

## 六、时序图 5：211 保险核心商保直赔与电子签名 SFTP 归档链路

覆盖开启商保直赔标识（EWP 团险 / SWP 散客）的前置资料门禁、电子签名校验与 PDF 动态盖章合成（`IElectricSignFeignClient`、`ClaimsDataServiceImpl`），以及事件驱动专线 SFTP 归档至 211 保险核心结案（`ClaimsDataEvent` / `SwpClaimsDataEvent`、`ClaimsDataListener`、ADR-0013）。

```mermaid
sequenceDiagram
    autonumber
    actor User as 持有人 (保单直赔用户)
    participant ENT as hmsc-edge-enterprise (ClaimsDataServiceImpl)
    participant SIGN as member-core-sign (IElectricSignFeignClient)
    participant NAS as 本地/NAS 文件存储
    participant SFTP as 211 保险核心 SFTP (hmsc.ftp.server.host)

    User->>ENT: 1. 上传身份证正反面影像（OCR 识别校验）
    ENT->>NAS: 暂存影像至 ewp/electricSign/temp/{yyyyMMdd}/{cardCode}/

    User->>ENT: 2. 提交实时手写电子签名轨迹（validateElectricSign）
    ENT->>SIGN: POST /member/sign/{sourceCode}/signCheck（签名轨迹合法性校验，生成 flowId）
    SIGN-->>ENT: 校验通过（code=1000）
    ENT->>SIGN: POST /member/sign/{sourceCode}/signWriting（合成电子签名图）
    SIGN-->>ENT: 合成成功

    User->>ENT: 3. 确认提交理赔授权（mergeClaimsData）
    ENT->>SIGN: POST /member/sign/{sourceCode}/getSignFile（拉取签章后 PDF）
    SIGN-->>ENT: 返回《体检理赔申请授权书 PDF》
    ENT->>NAS: 持久化保存身份证影像、签名图与理赔 PDF

    ENT->>ENT: 发布领域事件 ClaimsDataEvent / SwpClaimsDataEvent
    par 事件 1：本地理赔资料落库（PUSH_CLAIMS_DATA_TO_MEMBER）
        ENT->>ENT: ClaimsDataListener.publishClaimsData 更新理赔表影像与 PDF 相对路径
    and 事件 2：专线 SFTP 归档 211 核心（PUSH_CLAIMS_DATA_TO_HMC）
        ENT->>NAS: 清理临时 PDF 与签名模板文件
        ENT->>SFTP: SftpUtil.uploadLocalFile 上传至 {ftpPath}/ewp/electricSign/{yyyyMMdd}/{flowId}.pdf
        alt SFTP 上传成功
            SFTP-->>ENT: 归档成功（驱动 211 核心后台自动化理赔结案）
        else SFTP 上传失败
            ENT->>ENT: 记录失败日志告警，待人工/重试补传
        end
    end
    ENT-->>User: 理赔前置门禁放行，进入标准选检预约流程
```

---

## 七、时序图 6：报告 OCR 归档 HMES、C24/C59 手动与自动解读、小诺健康 AI 免登及在线客服链路

覆盖原版 PDF 报告经大模型 OCR 统一解析归档 HMES、C24/C59 手动前置开放门禁与四条件自动申请报告解读（`ReportInterpretationEvent`）、外部小诺健康 AI 国密免登与 RSA 短效令牌双向回查报告（`queryAllReportList`），以及保险在线客服 AES-GCM 免登（ADR-0010、ADR-0016）。

```mermaid
sequenceDiagram
    autonumber
    actor User as 持有人 / HR
    participant JOB as hmsc-innovate-jobs
    participant ENT as hmsc-edge-enterprise
    participant CORE as member-core-health (IHmes / IPhysicalExam)
    participant OCR_HMES as 大模型 OCR & 健康档案 HMES
    participant DOC as HMC 托管 C24/C59 三方医生解读
    participant XN as 小诺健康 AI / 保险在线客服

    rect rgb(245, 248, 255)
        Note over JOB,OCR_HMES: 阶段 A：大模型 OCR 结构化解析与 HMES 官方档案归档
        JOB->>OCR_HMES: NotifyCheckReportHandler 分页推送近 3 天已出 PDF 报告至 OCR（最多重试 maxPushNum=2 次）
        OCR_HMES-->>OCR_HMES: 统一大模型 OCR 抽取临床指标与 AbnormalFinding

        ENT->>ENT: 报告落标 REPORTED(05) 事务提交（AFTER_COMMIT）触发 AppointmentListener.pushReportToHmes
        ENT->>CORE: /inside/hmes/pushReportToHmes（PhysicalExamInfoToHmesParam）
        CORE->>OCR_HMES: 归档官方体检报告至 HMES（自主上传外院历史报告物理隔离不推送）
        Note right of JOB: PushReportToHmesHandler 按日期区间定时兜底补推未同步报告
    end

    rect rgb(255, 248, 245)
        Note over User,DOC: 阶段 B：C24 / C59 专业医生异步解读（手动申请 + 四条件自动申请）
        alt 路径 1：出报告自动申请（电子授权书 + 授权类型 + 门店自动授权 + 可用 C24/C59 次数）
            ENT->>ENT: 线上轮询或 MIS 上传报告落库后发布 ReportInterpretationEvent(PUSH_REPORT_INTERPRETATION_TO_HMC)
            ENT->>ENT: AppointmentListener -> OrderWrapper.automaticInterpretEwpReportApply 自动选可用子产品
        else 路径 2：用户手动申请 / 已有工单补传材料（interpretReportId）
            User->>ENT: POST /ewp/interface/interpretEwpReportApply（前置校验 anomlndexInterpreType 01/02）
            ENT->>CORE: uploadHmesFile（合并机构报告与用户自传当次报告，上限 30 份，统一归档 HMES）
        end
        ENT->>ENT: 映射真实持有人核心客户号 hmcId；新建工单校验并扣 remaindCount（修改补传不重扣）
        ENT->>CORE: /inside/interface/interpretEwpReportApply
        CORE->>DOC: HMC 创建/更新解读工单（interpretReportId）并推送专科医生核阅
        Note right of JOB: 自动提交失败由 InterpretEwpReportApply XXL-Job 定时兜底补推
        DOC-->>CORE: 医生核阅完成异步回写结构化解读结论（永久挂载）
        User->>ENT: /ewp/interface/queryEwpInterpretReportList & queryEwpInterpretReportInfo
        ENT->>CORE: 查询解读记录与结论 -> 返回持有人
        JOB->>User: SendInterpretTheReportHrHandler 汇总异常分布推送 B 端 HR 监控看板
    end

    rect rgb(245, 255, 248)
        Note over User,XN: 阶段 C：小诺健康 AI 国密多 Agent 免登 & 报告双向回查（及在线客服免登）
        User->>ENT: 请求免登（getXiaoNuoLoginUrl 固定 ai/physical | getXiaoNuoTargetUrl 动态 pageType/pageTab）
        ENT->>ENT: 校验 pushCustomerInfoFlag：仅 Y 且四要素全非空才推 PII，否则仅传 thirdUserId + memberNo
        ENT-->>User: 返回 SM4 加密 + SM3 签名免登跳转 URL（跳转小诺体检解读 / 心理咨询等 Agent）
        User->>XN: 免登进入小诺健康 AI 页面
        XN->>ENT: 反向调用 queryAllReportList(customerCode, appointSerialCode)
        ENT->>ENT: 签发短效 xiaonuologin Token 并 RSA 加密拼入 PDF URL，补齐 holderCustomerCode
        ENT-->>XN: 返回 EWP + SWP 加密体检报告列表（供小诺大模型安全拉取 PDF 解读）
        opt 实时人工在线客服（BGJD 报告解读 / PTZX 普通咨询）
            User->>ENT: POST /ewp/interface/getCustomerServiceSystemUrl
            ENT-->>User: 返回 AES-GCM 加密跳转 URL -> 进入招商信诺保险在线客服
        end
    end
```

---

## 八、时序图 7：体检代报销与积分报销核心财务推送、回调及原单改卡重推链路

覆盖 `MedicalReimbursement`（`MengniuController` / `IMengniuServiceImpl` / `ReimburseTxServiceImpl`）与 `PointsReimbursement`（`KpmgServiceImpl`）的权益互斥校验、三类积分源冻结、MIS 全额审核推送核心财务、异步打款回调与 `05-付款失败` 原单改卡免复审直推（ADR-0015）。

```mermaid
sequenceDiagram
    autonumber
    actor User as 持有人 / 员工
    participant MIS as MIS 审核后台
    participant ENT as hmsc-edge-enterprise
    participant CORE as member-core-health (积分/财务网关)
    participant MQ as RabbitMQ (PushMqDataServiceImpl)
    participant HMC as HMC 核心财务系统

    rect rgb(245, 248, 255)
        Note over User,HMC: 路径 A：体检代报销（01-体检报销 / 02-复检报销）
        User->>ENT: POST /ewp/interface/addUserReimburseNew（个人/公司双抬头发票）
        ENT->>ENT: ReimburseBenefitCheckPrepare 校验：01 与线上预约互斥；02 校验独立复检权益
        ENT-->>User: 落库 MEMBER_EWP_USER_REIMBURSE（01-审核中）
        MIS->>ENT: 审核（08-待寄送原件 -> 全额通过 02-待付款 | 整体驳回 06-审核未通过）
        ENT->>HMC: synReimburseToHmc / MQ 推送 EwpSynReimburseBo 至核心财务打款
        HMC->>ENT: 异步回调 updateReimburseStatus（03-已付款 | 05-付款失败）
        ENT->>ENT: ReimburseTxServiceImpl 事务更新报销单、复检权益与权益变更流水并发送短信通知
        opt 05-付款失败：原单改卡免复审直推
            User->>ENT: POST /ewp/interface/againSubmitReimburse（原 reimburseCode 修改银行卡）
            ENT->>ENT: 跳过人工复审直接置为 02-待付款
            ENT->>MQ: pushReimburse(reimburseCode) 重新推送核心财务打款
        end
    end

    rect rgb(245, 255, 248)
        Note over User,HMC: 路径 B：积分报销（仅员工本人个人发票，全额核准 + 积分两阶段）
        User->>ENT: 提交积分报销 addIntegralReimburse（仅个人抬头发票，无原件寄送）
        ENT->>CORE: integralOperation(status=01 预冻结，支持核心/薪福通/福粒积分源)
        ENT-->>User: 落库 MEMBER_EWP_KPMG_REIMBURSE（01-审核中）
        alt 用户撤销（cancelIntegralReimburse）或 MIS 驳回（updateIntegralByMis -> 06）
            ENT->>CORE: integralOperation(status=03 原路返还冻结积分)
        else MIS 全额审核通过（不支持部分核减）
            ENT->>HMC: synIntegralReimburseToHmc 推送 EwpSynIntegralReimburseBo（02-待付款）
            HMC->>ENT: 异步回调 updateIntegralReimburseStatus（03-已付款 | 05-付款失败）
            alt 回调 03-已付款
                ENT->>CORE: integralOperation(status=02 冻结转实扣，按 applicationAmount 全额扣减)
                Note right of ENT: 若积分操作失败则自动回滚报销单状态至 02-待付款并记异常列表
            else 回调 05-付款失败（或 03 异常逆转 05 先退再冻）
                ENT->>ENT: 保持积分冻结态不退回，释放推送锁
                User->>ENT: updateIntegralReimburse（原 reimburseCode 修改银行卡，跳过复审重推财务）
            end
        end
    end
```

---

## 九、下游核心接口契约总表（Interface Contract Matrix）

| 下游系统 | 调用方 / 接收方 | 协议与客户端 / 入口 | 核心接口 / Topic / 路径 | 通信模式 | 失败重试与降级策略 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. HMC 核心系统** | `hmsc-edge-enterprise` ➔ `member-core-health` | Feign HTTP (`IPhysicalExamFeignClient`) | `queryProjectConfiguration`、`queryStaffMemberEffBenefits`、`queryPackageListNew`、`queryStoreListNew`、`queryNewScheduleList`、`validateCashNew`、`lockAppointNum`、`ewpPushRefundStatus` | 同步 | `PhysicalExamHystrix` 降级兜底；事务回滚监听自动释放占容；退款推送失败由 `PushEwpRufundStatusHandler` 定时补偿 |
| **1. HMC 核心系统** | `hmsc-edge-enterprise` ➔ HMC | RabbitMQ Direct (`PushMqDataServiceImpl` / `MqProperties`) | `ordersync`、`appointsync`、`modifydatesync`、`ordercancelsync` | 异步（事务 `AFTER_COMMIT`） | 首次发送失败即时重试 1 次并落 `mq_log`；含增值服务特殊单走 `mq_log(type=05)` + `AddOrderSyncCompensationHandler` 补偿 |
| **2. 外部积分福利平台** | `hmsc-edge-enterprise` ➔ `member-core-health` | Feign HTTP (`IPhysicalExamFeignClient` / `IXinFuTongFeignClient`) | 核心：`queryIntegral` / `operationIntegral`<br/>福粒：`getIntegralDetail` / `buildIntegralOrder` / `cancelIntegralOrder` / `getIntegralOrder`<br/>薪福通：`getIntegralDetail` / `buildIntegralOrder` / `queryOrderResult` / `cancelIntegralOrder` / `queryCancelResult` | 同步（双边并发） | 薪福通下单超时自动调 `queryOrderResult` 重试查单；退积分失败先反查终态，确认未撤则落 `exception_records`，由 `CancelFuLiOrderHandler` / `CancelOrderIntegralFailHandler` 定时补偿，超限转人工 |
| **2. 支付网关 (CMB/EPAY)** | `hmsc-edge-enterprise` ⇄ `hmsc-edge-cmb` / EPAY | Feign HTTP (`ICmbFeignClient`) + HTTP 回调 (`NotifyNewController`) | 出站：`buildPayUrl`、`cmbApplyRefund`、`queryCmbRefundInfo`<br/>入站：`/epay/interface/epayPayNotifyNew`、`/epay/interface/epayRefundNotifyNew` | 同步建单 + 异步回调 | 支付回调验签幂等；退款回调驱动退积分（异常返回 `FAIL` 触发支付平台重试）；超时未付由 `CancelEwpOrderNewHandler` 15 分钟释放 |
| **3. 17+ 线上直连供应商** | `hmsc-edge-enterprise` ➔ `member-core-health` | Feign HTTP (`IAppointmentFeignClient`, `/inside/interface/{type}/*`) | 实时：`queryScheduleList`、`queryStoreSchedulePeriod`、`transformPacketCodeOffline`、`customerAppointment`、`modifyAppointmentDateV2`、`cancelAppointment`<br/>轮询：`queryPhysicalExamStatus`、`queryAppointmentVid`、`checkAppointmentReportCreated`、`downloadAppointmentReport`<br/>入站回调：`/aikang/interface/aiKangNotify` | 同步锁单 + XXL-Job 定时轮询 | **即时同步失败策略**：锁单超时/售罄直接落标 `07`，不异步重试；本地事务回滚自动调 `cancelAppointment` 补偿（失败发邮件告警）；到检/报告由 `UpdateToCheckStateHandler` / `UpdateAppointReportStateHandler` 周期轮询；原生 JSON 拉取已弃用 |
| **4. 大数据推荐 TBDS** | `hmsc-edge-enterprise` ➔ `member-core-health`；TBDS ➔ `hmsc-edge-support` | Feign HTTP (`ITbdsFeignClient`, `/inside/tbds/*`) + HTTP 回调 (`TbdsController`) | 出站：`queryAIQuestionnaire`、`queryAIQuestionnaireResult`、`parseReportGetBaseInfo`、`aiRecommendPackageByReport`、`comparePacket`<br/>入站：`/tbds/interface/updateReportRecommendedPacketResult` | 同步（问卷/对比）+ 异步回调（报告推荐） | `TbdsHystrix` 降级；报告推荐任务失败落标 `03-推荐失败`，前端平滑降级为自主选购，不阻断主履约链路 |
| **5. 电子签名 & 211 保险核心** | `hmsc-edge-enterprise` ➔ `member-core-sign` & 211 SFTP | Feign HTTP (`IElectricSignFeignClient`) + 专线 SFTP (`ClaimsDataListener`) | 签名：`/member/sign/{sourceCode}/signCheck`、`signWriting`、`getSignFile`<br/>归档：`SftpUtil.uploadLocalFile` ➔ `{ftpPath}/ewp/electricSign/{yyyyMMdd}/{flowId}.pdf` | 同步签章 + 事件驱动异步 SFTP | 签章失败硬阻断理赔前置门禁；PDF 合成后双事件解耦本地落库与 SFTP 归档，SFTP 异常记录日志告警补传 |
| **6. 健康档案 HMES & 大模型 OCR** | `hmsc-edge-enterprise` / `hmsc-innovate-jobs` ➔ `member-core-health` | Feign HTTP (`IHmesFeignClient`, `/inside/hmes/*`) + XXL-Job | `pushReportToHmes`、`queryReportJsonList`、`queryMedicalSubjectList`；`NotifyCheckReportHandler` 分页推 OCR | 事件异步 + XXL-Job 补偿 | OCR 推送最大重试 `maxPushNum=2`；`PushReportToHmesHandler` 支持按时间区间手动/定时补推；自主外院报告物理隔离不入 HMES |
| **7. 报告解读（Dify AI & C24/C59 医生）** | `hmsc-edge-provider` ➔ Dify；`hmsc-edge-enterprise` ➔ `member-core-health` | Feign HTTP/SSE (`IDifyFeignClient`) + Feign HTTP (`IPhysicalExamFeignClient`) | Dify：`/v1/workflows/run`、`/v1/chat-messages` (SSE)<br/>医生解读：`interpretEwpReportApply`、`uploadHmesFile`、`queryEwpInterpretReportInfo`、`queryEwpInterpretReportList` | 同步/流式（AI）+ 异步工单（医生） | AI 解读独立于人工服务；C24/C59 支持手动前置门禁与四条件 `ReportInterpretationEvent` 自动触发，自动提交失败由 `InterpretEwpReportApply` XXL-Job 兜底补推 |
| **8. 小诺健康 AI & 保险在线客服** | `hmsc-edge-enterprise` ⇄ 小诺健康 AI / 保险在线客服 | 国密 SM4+SM3 免登 + HTTP 回调；AES-GCM 加密跳转 | 出站：`getXiaoNuoLoginUrl`（固定 `ai/physical`）、`getXiaoNuoTargetUrl`（多 Agent `pageType/pageTab`）、`getCustomerServiceSystemUrl`（`BGJD/PTZX`）<br/>入站回查：`queryAllReportList`（RSA 加密 `xiaonuologin` Token） | 免登跳转 + 反向加密拉取 | `pushCustomerInfoFlag` 四要素原子隐私门禁（缺一不推 PII）；短效 RSA 令牌控权防报告裸奔 |
| **1. HMC 核心财务（报销打款）** | `hmsc-edge-enterprise` ⇄ HMC 核心财务 | HTTP / RabbitMQ (`PushMqDataServiceImpl`) + 异步回调 | 推送：`synReimburseToHmc`、`synIntegralReimburseToHmc`、`pushReimburse`<br/>回调：`updateReimburseStatus`、`updateIntegralReimburseStatus`、`updateIntegralByMis` | 异步推送 + 回调驱动 | 全额核准不部分核减；积分报销回调 `03` 转实扣失败自动回滚至 `02`；`05-付款失败` 维持冻结态，原单改卡免复审直推 |
