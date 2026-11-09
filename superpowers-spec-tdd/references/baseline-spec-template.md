# baseline-spec.md 模板（结构化需求基线规约）

> 给 Agent 的填充规则：严格按下列章节顺序输出，不新增自由散文章节。每条规则必须可派生断言；不可断言的句子一律降级到 `OPEN`。

## 0. 头部

```markdown
# 需求基线规约：<需求名>
- 版本：V1
- 状态：DRAFT | BASELINE LOCKED
- 锁定时间：
- 上游来源：<需求文档链接 / 会议记录 / 票据号>
- Code Change Scope：<见第 5 节>
```

## 1. 业务目标与范围（只写能验证的）

| 项 | 内容 |
|---|---|
| 业务目标 | 一句话，可被某条 SPEC 验证 |
| 本次范围 | 列出交付能力 |
| 明确不做 | 对应 `OUT_OF_SCOPE` 清单 |

## 1.5. 技术约束（不能打破的技术边界）

> 这些约束是波及面扫描和实现方案的重要输入，显式列出避免 Agent 越界。

| 项 | 内容 |
|---|---|
| 框架版本 | SpringBoot 2.1.3.RELEASE，不升级 |
| 数据层 | MyBatis + PageHelper，不改框架 |
| 依赖限制 | 不修改 pom.xml 依赖版本，不新增第三方库 |
| 数据库 | 不修改 schema、不新增表、不加字段 |
| 中间件 | 复用现有 Redis / MQ / RPC 客户端，不新增 |
| 其他 | 复用现有 ErrorCode 枚举、GlobalExceptionHandler、ApiResponse 封装 |

## 2. SETTLED 规约（核心）

**每条使用固定条目格式，ID 连续编号。** 谓词范式优先：

```markdown
### REQ-SPEC-001 <短标题>
- 分区：SETTLED
- 来源：<需求文档第 X 节 / 与产品确认于 X 月 X 日>
- 波及项：IMP-03（OrderService）、IMP-07（order_status 枚举）
- 前置条件：
  - `P(order.status == PAID)`
  - `P(operator.hasRole("CS") || operator.isOwner(order))`
- 动作：`cancelOrder(orderId, reason)`
- 后置断言（成功）：
  - `P(order.status == CANCELLED)`
  - `P(refundRecord exists && refundRecord.amount == order.paidAmount)`
- 后置断言（异常/边界）：
  - `IF reason.length > 200 THEN return err(E_REASON_TOO_LONG)`，且 `P(order.status unchanged)`
  - `IF order.status == CANCELLED THEN return err(E_ALREADY_CANCELLED)`（幂等）
- 约束不变量：`INV-001`
```

流程/分支/数据转换类用伪代码范式（**无实现细节**：不写类名、SQL、Redis 命令、框架注解）：

```markdown
### REQ-SPEC-005 优惠券发放
- 分区：SETTLED
- 波及项：IMP-11（CouponService）、IMP-12（coupon 表）
- 行为：
  ```
  IF user.level in [VIP1, VIP2]        → 发 VIP 券 ×1
  ELIF user.level == NONE AND user.registerDays < 7 → 发 NEWUSER 券 ×1
  ELSE                                  → 不发券
  ```
- 后置断言：`P(count(coupon where batchId=A and userId=u) <= 1)`
- 约束不变量：`INV-005`
```

谓词书写约定：

| 记号 | 含义 |
|---|---|
| `P(x)` | 布尔谓词，必须可判定 |
| `state` / `order.status` | 领域对象状态 |
| `in(...)` / `out(...)` | 入参 / 出参 |
| `ok` / `err(CODE)` | 分支结果，CODE 必须在错误码表中存在 |
| `INV-xxx` | 全程不变量，任何分支不得打破 |

## 2.5. 验收标准表（人工可操作的验证清单）

> 每条 REQ-SPEC 对应至少一条 AC。前置条件明确、操作具体、预期结果可独立判断通过/失败。

| # | 前置条件 | 操作 | 预期结果 | 对应 SPEC |
|---|---|---|---|---|
| AC1 | 订单状态 PAID，操作员有 CS 权限 | `POST /api/orders/{id}/cancel` + 合法 reason | 200，`data.status=CANCELLED`，退款单新增 1 条 | REQ-SPEC-001 |
| AC2 | reason 201 字 | 同上 | 400，`code=E_REASON_TOO_LONG`，订单状态不变 | REQ-SPEC-001 |
| AC3 | reason 恰好 200 字 | 同上 | 200，成功取消 | REQ-SPEC-001 |
| AC4 | 订单已 CANCELLED | 重复取消 | 200 或 400，`code=E_ALREADY_CANCELLED`，退款单仍 1 条 | INV-001 |

> 验收标准表是关卡 B 和 E4 的核对清单，比纯谓词断言更直观、可手动操作验证。

## 3. INV 不变量清单

最容易漏、最容易漂移的一类。逐条列出，并标注"违反时的表现"：

| ID | 不变量 | 违反表现 | 关联 SPEC |
|---|---|---|---|
| INV-001 | 订单金额在取消流程中不得被修改 | 退款金额与实付不符 | REQ-SPEC-001 |
| INV-002 | 库存不得为负 | 超卖 | REQ-SPEC-002 |
| INV-003 | 未登录或无权限的请求不得改变订单状态与资金数据 | 越权取消 / 越权退款 | REQ-SPEC-001 |

必查四类不变量：**事务边界、幂等性、权限边界、数据一致性**（跨表/跨缓存）。

> 若某条 REQ-SPEC 经审计被降级为 OPEN，保留该条目并在其块内补一行 `- 分区：OPEN`；`check_spec_coverage.py` 据此免除覆盖要求。同理写 `- 分区：OUT_OF_SCOPE` 表示本次不做。

## 4. 错误码表

| CODE | 触发条件 | HTTP 状态 | 关联 SPEC |
|---|---|---|---|
| E_REASON_TOO_LONG | 取消原因为空或超 200 字 | 400 | REQ-SPEC-001 |

规约中出现的每个 `err(CODE)` 都必须在此表登记，否则审计判"不可测/不一致"。

## 5. Code Change Scope（增量测试边界）

```markdown
| 类型 | 目标 | 预计动作 | 关联 SPEC |
|---|---|---|---|
| Controller | OrderController#cancel | 修改入参校验 | REQ-SPEC-001 |
| Service | OrderService#cancel | 新增状态校验+退款调用 | REQ-SPEC-001 |
| Mapper | OrderMapper#updateStatus | 新增条件更新 | REQ-SPEC-001 |
| 枚举 | OrderStatus | 新增 CANCELLED 分支 | REQ-SPEC-001 |
| Redis | order:cancel:lock:{orderId} | 新增锁 key | INV-002 |
| 表 | refund_record | 新增记录 | REQ-SPEC-001 |
```

**规则**：范围外代码一律视为不该改。E4 阶段做越界检查（git diff 文件清单 ∩ 本表 = 实际改动）。

## 6. OPEN 待探索

| ID | 缺口描述 | 为什么未定 | 候选方向 | 阻塞项 |
|---|---|---|---|---|
| OPEN-01 | 未支付订单能否取消 | 产品未回答；存量代码允许但无校验 | A 允许无退款取消 / B 禁止 | 需产品决策 |

`OPEN` 项**不进规约正文、不进测试、不进代码**，只在 `exploration-options.md` 里给方案与代价。

## 7. OUT_OF_SCOPE

| 项 | 原因 | 后续去处 |
|---|---|---|
| 部分退款 | 本期只做全额退款 | 下迭代 |

## 8. 版本与变更记录

| 版本 | 时间 | 变更 | 变更来源 | 影响 SPEC |
|---|---|---|---|---|
| V1 | 2026-11-09 | 初版锁定 | 关卡 A 确认 | — |
| V2 | 2026-11-12 | 新增 REQ-SPEC-009 | 回流 B1 | 影响 P1/P2 清单 |

**规则**：版本号递增即视为"基线变更"，必须重走审计与关卡 A，然后重生成阶段2产物。

## 反例（审计会直接判不合格）

| 反例写法 | 问题 | 正确写法 |
|---|---|---|
| "取消要快" | 不可断言 | `P(p99(latency) < 500ms)` 或降为 OPEN |
| "尽量保证幂等" | 无判定条件 | `P(重复请求仅生成 1 条记录)` |
| "权限合理即可" | 无主体 | `P(operator.hasRole("CS"))` |
| "参考现有逻辑" | 无边界 | 显式列出存量分支与保留/修改决定 |
| 一词多义（"订单"指主单还是子单） | 歧义 | 在术语表中定义，全文统一 |
