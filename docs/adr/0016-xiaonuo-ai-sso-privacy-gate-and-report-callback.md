# 16. 小诺健康 AI 多 Agent 免登、隐私最小化门禁与报告双向回查契约 (XiaoNuo Health AI Multi-Agent SSO, Privacy-Minimized PII Gate & Bidirectional Report Callback)

体检平台与外部第三方「小诺健康 AI 平台」之间确立“**国密 SM4+SM3 免登多 Agent 路由**”、“**`pushCustomerInfoFlag` 四要素隐私最小化推送门禁**”以及“**RSA 短效令牌双向回查 EWP/SWP 体检报告 PDF**”集成契约，并明确其与保险在线客服免登（AES-GCM）的边界。

## 背景与权衡

随着检后服务从单一“看报告”延伸到“AI 体检报告解读 + AI 心理咨询 + 多场景健康陪伴”，AI 能力由外部专业平台「小诺健康」独立演进，体检平台（HMSC）需要在不泄露敏感 PII、不将核心报告公网裸奔的前提下，实现无感跨系统跳转与数据协同：
1. **多 Agent 复用同一免登通道**：小诺健康同时承载检后体检报告 AI 解读、心理咨询等多种 Agent，若按每个场景单独建对接协议会导致接入碎片化；
2. **跨企业租户的隐私合规差异**：不同企业大客户对将员工姓名、手机号、证件号同步至外部 AI 平台的合规要求不一，不能一刀切全量推送 PII，也不能推送残缺四要素导致外部建档脏数据；
3. **报告原件的安全跨平台调阅**：小诺 AI 解读需要读取用户真实体检报告 PDF，但体检报告属于高度敏感医疗数据，严禁暴露永久公网下载链接或绕过权限校验。

## 架构决策

- **双入口统一国密免登与多 Agent 路由（SM4 加密 + SM3 签名）**：
  - **固定体检解读入口（`getXiaoNuoLoginUrl`）**：同时服务企业端（EWP）与散客端（SWP），固定路由至 `pageType=ai`、`pageTab=physical`，支持携带 `appointSerialCode` 精确定位单次体检报告；
  - **通用多 Agent 路由入口（`getXiaoNuoTargetUrl`）**：动态接收 `pageType` 与 `pageTab`（当 `pageType=ai` 时强制校验 `pageTab` 非空），统一承接体检 AI 报告解读、心理咨询等延伸健康 Agent 跳转；
  - 跳转报文统一由 `SM4` 加密 `data` 负载，并按 `appId + data + nonce + timestamp + signKey` 计算 `SM3` 签名防篡改。

- **隐私最小化推送门禁（`pushCustomerInfoFlag` 四要素全有才推）**：
  - 每次免登必传项目级对接开关 `pushCustomerInfoFlag`（`Y/N`）；
  - 默认始终透传脱敏身份标识 `thirdUserId`（`customerCode`）与企业工号 `memberNo`（`workCode`）；
  - **严格原子推送约束**：仅当 `pushCustomerInfoFlag == Y` 且姓名、手机号、证件类型、证件号**四要素全部非空**时，才打包推送 PII；任一字段缺失即整体跳过 PII 推送，防止外部平台产生残缺身份档案。

- **双向报告回查与 RSA 短效令牌封装（`queryAllReportList`）**：
  - 用户进入小诺健康后，由小诺健康反向调用 HMSC 的 `queryAllReportList` 获取该用户 EWP 与 SWP 全量体检报告清单（支持按 `appointSerialCode` 过滤）；
  - HMSC 实时签发 `bizType=xiaonuologin` 的短效 EWP Token，经 **RSA 公钥加密**后拼接于每份报告 PDF URL 参数中返回，同时按需补齐真实体检人客户号 `holderCustomerCode`，确保小诺 AI 仅能在令牌有效期内安全拉取对应持有人的报告原件。

- **与保险在线客服免登的清晰边界**：
  - 实时人工在线客服走独立通道 `getCustomerServiceSystemUrl`，按 `bizType` 区分 **`BGJD`（报告解读）** 与 **`PTZX`（普通咨询）**，采用 `AES-GCM` 加密跳转招商信诺保险在线客服系统，与小诺健康 AI 平台及 HMC 托管的 C24/C59 异步医生解读工单（见 [ADR-0010](./0010-report-interpretation-pipeline-and-hr-monitoring.md)）互不混用。

## 效果与影响

- **扩展零改造成本**：新增小诺健康心理咨询、慢病管理等 AI Agent 仅需配置 `pageType/pageTab`，无需重复开发免登与加签链路；
- **隐私与合规可控**：`pushCustomerInfoFlag` 与四要素原子校验兼顾了严合规大客户的 PII 隔离诉求与普通项目的无缝体验；
- **医疗文件零裸奔**：RSA 加密短效令牌机制保证了第三方 AI 平台按需调阅报告 PDF 的时效性与可审计性。
