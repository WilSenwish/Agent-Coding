# 测试规划模板（必须在编码之前产出）

> 两份规划都是**规划**，不写测试代码。每条用例必须回标 `SPEC-ID`，并注明覆盖的 `IMP-xx`。
> 写不出 SPEC-ID 的用例 → 说明它在测基线外的规则，删掉或回流基线。

---

## 第一部分：test-plan-unit.md（单元测试规划）

### 1. 被测单元清单（只列本次 Code Change Scope 内的）

| # | 被测对象 | 方法/函数 | 关联 SPEC | 关联 IMP |
|---|---|---|---|---|
| U1 | OrderService | `cancel(orderId, reason, operator)` | REQ-SPEC-001 | IMP-03 |
| U2 | RefundCalculator | `calc(order)` | REQ-SPEC-002 | IMP-11 |

> Controller 与 Mapper 不做单元测试（前者归接口集成测试，后者归 DB 层验证）。工具类、枚举转换、领域校验可按需纳入。

### 2. 用例矩阵

每条用例固定字段：`用例ID | 类型 | 输入 | 预期 | 断言点 | SPEC | IMP`

| 用例ID | 类型 | 输入 | 预期 | 关键断言 | SPEC | IMP |
|---|---|---|---|---|---|---|
| U1-C1 | 正向 | status=PAID, role=CS | 成功取消，生成退款单 | `status==CANCELLED`；`refund.amount==paidAmount` | REQ-SPEC-001 | IMP-03 |
| U1-C2 | 异常 | reason 201 字 | 抛 BizException | 异常码 `E_REASON_TOO_LONG`；`status` 未变 | REQ-SPEC-001 | IMP-02 |
| U1-C3 | 边界 | reason 恰好 200 字 | 成功 | 无异常；`status==CANCELLED` | REQ-SPEC-001 | IMP-02 |
| U1-C4 | 幂等 | 重复取消同单 | 返回已取消 | `E_ALREADY_CANCELLED`；退款单仍为 1 条 | INV-001 | IMP-03 |
| U1-C5 | 权限 | role=USER 且非下单人 | 拒绝 | `E_NO_PERMISSION`；`status` 未变 | REQ-SPEC-001 | IMP-01 |
| U1-C6 | 不变量 | 计算中含优惠 | 退款金额=实付 | `INV-001` 成立 | INV-001 | IMP-11 |

必查类型，缺一类要在"豁免理由"写清楚：

- **正向**：主流程 happy path
- **边界**：空 / null / 0 / 上限 / 上限±1 / 超长 / 特殊字符 / 时区 / 金额精度
- **异常**：非法入参、下游失败、超时、并发冲突
- **不变量**：`INV-xxx` 每条至少 1 条用例
- **状态流转**：非法状态迁移被拒

### 3. Mock 边界

| 依赖 | 处理 | 理由 |
|---|---|---|
| `OrderMapper` | mock | 单测不碰 DB |
| `RedisTemplate` | mock | 单测不碰缓存 |
| 退款下游 RPC | mock，可注入成功/失败/超时 | 覆盖异常分支 |
| 时钟 | 注入固定 Clock | 时间相关断言可复现 |

**禁止**：`@SpringBootTest`、`@Autowired` 真实 Bean、连真实 DB/Redis/HTTP。

### 4. 断言质量要求

- 必须断言：**返回值具体内容、异常类型与错误码、关键状态变更**。
- 禁止：只 `assertNotNull` / `assertTrue(true)` / 只校验日志。
- 一条用例一断言主题；多主题拆用例，便于定位。

### 5. 豁免记录

未覆盖的 SPEC / IMP 及理由（E4 会核对）：

| 对象 | 豁免理由 | 风险 |
|---|---|---|

---

## 第二部分：test-plan-api.md（接口集成测试规划）

### 1. 接口清单（仅本次变更接口）

| # | 方法 | 路径 | 变更点 | 关联 SPEC | 关联 IMP |
|---|---|---|---|---|---|
| A1 | POST | `/api/orders/{id}/cancel` | 新增 reason 校验 + 退款 | REQ-SPEC-001 | IMP-01 |

### 2. 用例矩阵

| 用例ID | 场景 | 请求 | 预期 HTTP | 预期响应体关键字段 | 数据侧校验 | SPEC | IMP |
|---|---|---|---|---|---|---|---|
| A1-C1 | 正常取消 | 合法 body + CS token | 200 | `code=0`，`data.status=CANCELLED` | `refund_record` 新增 1 行 | REQ-SPEC-001 | IMP-03 |
| A1-C2 | 参数非法 | reason 超长 | 400 | `code=E_REASON_TOO_LONG` | 无退款记录 | REQ-SPEC-001 | IMP-02 |
| A1-C3 | 未登录 | 无 token | 401 | `code=UNAUTHENTICATED` | 订单不变 | INV-003 | IMP-01 |
| A1-C4 | 越权 | 普通用户取消他人订单 | 403 | `code=E_NO_PERMISSION` | 订单不变 | INV-003 | IMP-01 |
| A1-C5 | 幂等 | 相同幂等键重复提交 | 200 | 第二次返回已取消 | 退款记录仍 1 条 | INV-001 | IMP-03 |
| A1-C6 | 下游失败 | mock 退款超时 | 500/502 | `code=E_REFUND_TIMEOUT` | 订单状态回滚为 PAID | INV-002 | IMP-11 |
| A1-C7 | 缓存 | 取消后查详情 | 200 | `data.status=CANCELLED` | 缓存 key 已失效或更新 | — | IMP-20 |

必查场景：**参数非法 / 未登录 / 越权 / 幂等 / 事务回滚 / 缓存一致性 / 响应 schema 匹配 OpenAPI**。

> 基准说明（二元设计，勿混用）：自动化单测与接口测试的 schema 断言以 **OpenAPI/接口文档**为准；`frontend-contract.md` 是给前端的跨端联调契约说明，不作为测试断言基准。二者内容如出现分歧，以 OpenAPI 为准并回流 P5 同步。

### 3. 环境与依赖

| 项 | 方案 |
|---|---|
| 数据库 | Testcontainers PostgreSQL（一次性容器）或独立测试库 |
| 缓存 | Testcontainers Redis |
| 第三方 | WireMock 场景：成功/失败/超时 |
| 数据隔离 | `@Transactional` 回滚；跨事务场景用显式清理脚本 |
| 认证 | 测试 token 工厂，禁止复用生产 token |

### 4. 数据准备与清理

| 用例 | 前置数据 | 清理方式 | 是否可并行 |
|---|---|---|---|
| A1-C1 | 已支付订单 + 库存 | 事务回滚 | 是 |
| A1-C5 | 幂等键预置 | 显式删除 | 否（共享键） |

### 5. 执行顺序与依赖

- 无状态用例并行；有共享数据的用例串行并标注原因。
- 禁止用例之间传递状态（A 的产物给 B 用），会制造隐性耦合。

### 6. 断言质量要求

- 三层都要断言：**HTTP 状态 + 响应体字段 + 数据侧状态**（DB 行 / Redis key）。
- 响应体除关键字段外，做 schema 校验（字段名、类型、必填），防契约漂移。

---

## 规划评审速查（关卡 B 逐条勾）

- [ ] 每条用例都有 SPEC-ID，且 SPEC 均为 SETTLED
- [ ] 每条 IMP-高 至少被一个用例覆盖，否则有豁免记录
- [ ] 边界与异常分支数量 ≥ 正向
- [ ] 断言是强断言（值/码/状态），无 `assertNotNull` 糊弄
- [ ] 单元层无 `@SpringBootTest`、无真实中间件
- [ ] 集成层只覆盖变更接口，无存量接口冗余用例
- [ ] 未覆盖项均有理由，无"待补"
