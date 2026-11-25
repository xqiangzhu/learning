# 6. 积分双边记账与镜像对账机制：外部积分平台与核心本地并发双冻结 (Dual-Account Shadow Ledger & Concurrent Freeze)

在接入外部积分平台（如招行福粒 FuLi、招行薪福通 XinFuTong）时，系统采用“**外部渠道冻结 + 核心镜像并发双冻结**”与“**子订单级明细穿透（SKU-level Mapping）**”机制，实现并发防超扣与端到端对账审计闭环。

## 背景与权衡

HMSC 面向企业大客户，涉及跨组织的混合结算。实际积分资产由上游/下游异构福利平台（福粒、薪福通）托管，HMSC 负责体检履约。
在该架构下存在两大技术挑战：
1. **跨系统并发超扣风险**：若仅依赖外部三方接口冻结积分，在多终端并发下单、网络延迟或接口重试场景下，核心本地无法实时感知额度水位，容易发生积分超额扣减或重复抵扣；
2. **账务黑盒与对账困难**：若外部仅以主订单总额粗粒度扣减，一旦发生部分退款、改期或对账差异，无法还原到具体体检加项包（SKU）的资金与积分构成；外部超时失败时，核心亦缺乏完整的审计镜像进行差异比对。

## 架构决策

- **外部渠道 + 核心镜像并发双冻结（Concurrent Dual Freeze）**：
  - 在 `IntegralStrategy.freezeIntegral` 执行时，系统通过 Stream 并发同时触发两路冻结调用：
    1. **外部平台预冻结/扣减**：调用 `FuLiIntegralServiceImpl` 或 `XinFuTongIntegralServiceImpl` 与外部福利系统同步，锁定外部真实积分；
    2. **核心账本镜像冻结（Shadow Ledger）**：同步调用 `CoreIntegralServiceImpl.commonFreezeIntegral`，在 HMSC 核心会员库与积分日志中落标预冻结流水；
  - **防超扣与双边留痕**：核心本地账本提供本地并发水位锁与镜像审计依据，外部渠道提供资产扣减凭据，双边实时对齐，彻底阻断超扣风险。

- **子订单 SKU 级明细穿透（SKU-level Line Item Mapping）**：
  - 调用外部平台创建积分订单（`abstractFreezeIntegral`）时，系统拒绝粗粒度总额扣减；
  - 严格将落标积分抵扣的子订单（`EwpOrderSubBean`）映射为结构化商品项（`sku_items`）：
    ```json
    {
      "partner_sku": "<packetCode>",
      "quantity": 1,
      "unit_price": "<scoreValue>"
    }
    ```
  - 确保外部平台的扣减流水与 HMSC 内部子订单、加项包颗粒度 1:1 精确对应，为后续分项退款与财务核算提供原子级凭据。

- **并行双释放与异常补偿托底（Parallel Release & Exception Log Fallback）**：
  - **逆向并行释放**：订单取消或超时未付时，`releaseIntegral` 采用并行流同时通知外部平台撤单（`cancelIntegralOrder`）与核心镜像释放，并通过 MDC 透传全局 `traceId` 维系分布式链路追踪；
  - **状态核对与异常挂起**：若外部撤单失败，系统二次反查外部订单状态（如福粒状态是否为已撤销 `7`）；若仍未成功撤销，立即向 `ExceptionRecordsBean` 写入异常补偿任务（落表 `INSERT_EXCEPTION_LOG`），防止单边账扩散，保障最终一致性。

## 效果与影响

- **高一致性**：彻底规避了分布式环境下的积分超扣与重放抵扣；
- **明细可溯**：子订单级 SKU 穿透使得每一笔积分变动均能追溯到具体的套餐包与履约项，满足银行级财务对账要求；
- **韧性托底**：核心镜像与异常补偿表为跨网超时、三方宕机提供了完备的事后自愈与人工介入通道。
