# frontend-contract.md 模板（前后端联调契约）

> 用途：P5 产出。给前端的**接口变更/新增告知**，同时是前端 AI 辅助开发的强制门禁。
> 只列本次变更涉及的接口，不重复 Swagger 已有内容。
> 复制下面模板填充，按需增删接口条目；版本与 `baseline-spec.md` 同步。

````markdown
# 前后端联调契约 — <需求名>

- 版本：V1（与 baseline-spec.md 同步）
- 生成时间：
- 锁定状态：BASELINE LOCKED（与关卡 A/B 同步）
- 契约源：baseline-spec.md + impact-scan.md

## 一、接口总览

| 变更类型 | 方法 | 路径 | 变更说明 | 关联 SPEC | 关联 IMP |
|---|---|---|---|---|---|
| 新增 | POST | /api/v1/orders/{id}/cancel | 新增取消接口，含 reason 校验 + 退款 | REQ-SPEC-001 | IMP-01 |
| 修改 | GET | /api/v1/orders/{id} | 返回体新增 `refundInfo` 字段 | REQ-SPEC-003 | IMP-04 |
| 删除 | — | — | 无（不删存量接口） | — | — |

## 二、接口详细契约（一个接口一节）

### POST /api/v1/orders/{id}/cancel — 新增

- **路由**：POST /api/v1/orders/{orderId}/cancel
- **请求头**：Authorization: Bearer <token>，Content-Type: application/json
- **路径参数**：

  | 字段 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | orderId | String | 是 | 订单号 |

- **请求体**：

  | 字段 | 类型 | 必填 | 默认值 | 约束 | 说明 |
  |---|---|---|---|---|---|
  | reason | String | 否 | null | 0-200 字 | 取消原因 |

- **成功响应（200）**：

  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "orderId": "ORD20261109001",
      "status": "CANCELLED",
      "refundAmount": 299.00
    }
  }
  ```

- **错误响应**：

  | HTTP | code | 说明 | 关联 SPEC |
  |---|---|---|---|
  | 400 | E_REASON_TOO_LONG | reason 超 200 字 | REQ-SPEC-001 |
  | 400 | E_ALREADY_CANCELLED | 幂等，订单已取消 | INV-001 |
  | 403 | E_NO_PERMISSION | 非订单所有者且非客服 | REQ-SPEC-001 |
  | 404 | E_ORDER_NOT_FOUND | 订单不存在 | — |

- **兼容性说明**：全新接口，无存量调用方。

### GET /api/v1/orders/{id} — 修改

- **变更说明**：返回体新增 `refundInfo` 字段，存量字段不变。
- **请求体**：无
- **成功响应（200）**：

  ```json
  {
    "code": 0,
    "data": {
      "orderId": "...",
      "status": "PAID",
      "refundAmount": 299.00,
      "refundInfo": {
        "status": "PENDING",
        "amount": 299.00,
        "applyTime": "2026-11-09T15:30:00+08:00"
      }
    }
  }
  ```

- **兼容性说明**：响应体新增字段，存量前端按已有字段解析不受影响（JSON 反序列化忽略未知字段）。**但**若前端做了严格 schema 校验（如 OpenAPI 校验器设为 additionalProperties=forbid），需要同步更新 schema。
- **关联 SPEC**：REQ-SPEC-003

## 三、字段级变更清单（只列变更点）

| 接口 | 字段 | 变更类型 | 变更前 | 变更后 | 关联 SPEC |
|---|---|---|---|---|---|
| GET /orders/{id} | data.refundInfo | 新增 | 不存在 | Object { status, amount, applyTime } | REQ-SPEC-003 |

## 四、状态机变更（如有）

| 实体 | 原状态迁移 | 新增/修改迁移 | 关联 SPEC |
|---|---|---|---|
| Order | PAID → COMPLETED | PAID → CANCELLED（新增） | REQ-SPEC-001 |

## 五、幂等与并发说明

- POST /orders/{id}/cancel：支持幂等键 `X-Idempotency-Key`，重复提交返回已取消状态（E_ALREADY_CANCELLED），退款记录仍 1 条
- 前端需在重试时传相同幂等键

## 六、前端 AI 辅助开发门禁（必读）

> 本节是给前端开发 / 前端 AI Agent 的强制约束。不遵守者联调必炸。

### 6.1 前端 AI Agent 的工作流顺序（必须锁死）

```
① 读取 frontend-contract.md（本文件）
② 对照 baseline-spec.md（如可访问）
③ 输出「契约缺口清单」——列出契约中缺失或模糊的点
④ 停在缺口清单，等待后端 Agent / 人工确认
⑤ 确认后，才开始写前端代码
```

**禁止跳过④**。直接写代码而不先输出缺口清单 = 违反门禁。

### 6.2 必须复核的缺口类型（缺一类必须反馈）

| 缺口类型 | 说明 | 示例 |
|---|---|---|
| 入参缺失 | 必填字段在请求体示例里没出现 | reason 是可选的但前端不知道要不要传 |
| 响应体 schema 不完整 | 响应只列部分字段，漏了可空字段 | `refundInfo` 没列 null 场景 |
| 枚举值不全 | 状态只列 CANCELLED，漏 PENDING/FAILED | 前端需要做分支 |
| 错误码场景遗漏 | 只列 400/403/404，没说 5xx 怎么处理 | 前端不知道降级策略 |
| 幂等键约定 | 没说 header 名和生成规则 | 前端重试不知道怎么传 |
| 字段类型不符预期 | amount 契约是 Number，前端按 String 处理 | 金额精度问题 |
| 时间格式 | 没说 ISO8601 还是 yyyy-MM-dd HH:mm:ss | 前端格式化错误 |
| 空值语义 | 非取消订单时 refundInfo 返回 null 还是不返回 key | 前端解构会炸 |
| 跨接口关联 | 只说了单个接口，但前端要同时改多个页面 | 需告知页面级变更范围 |

### 6.3 缺口反馈格式（给后端 Agent）

```markdown
【前端契约缺口反馈】frontend-contract.md @ V1

## 接口：POST /orders/{id}/cancel
1. **[空值语义]** 订单未取消时 refundAmount 返回 null 还是不返回？
2. **[时间格式]** error 响应是否需要带 serverTime？契约没说

## 接口：GET /orders/{id}
1. **[枚举值不全]** refundInfo.status 可能的值有哪些？只列了 PENDING

## 跨接口关联
1. 列表接口 GET /orders 是否也需要加 refundInfo？列表页和详情页都展示退款状态

---
以上确认后前端才能开始编码。
```

### 6.4 后端 Agent 收到缺口反馈后的处理

1. 逐条确认是否合理
2. 合理 → 更新 frontend-contract.md（版本 +1）+ 更新 baseline-spec.md（如涉及规则变更）
3. 不合理 → 说明理由（如「列表接口本次不改」= OUT_OF_SCOPE）
4. 更新后重新经过关卡 B

### 6.5 门禁判定

| 前端 AI 行为 | 判定 |
|---|---|
| 读完契约 → 直接写代码 | ❌ 违反门禁，退回 |
| 读完 → 输出缺口清单 → 等确认 → 写代码 | ✅ 合规 |
| 缺口清单有未确认项就写了代码 | ❌ 违反门禁，退回 |
| 手动开发（不用 AI） | ✅ 同样要过一遍缺口清单 |

## 七、变更记录

| 版本 | 时间 | 变更 | 触发来源 |
|---|---|---|---|
| V1 | 2026-11-09 | 初版，随关卡 B 锁定 | baseline-spec.md V1 |
````
