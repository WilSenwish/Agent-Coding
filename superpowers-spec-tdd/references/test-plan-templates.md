# 单元测试规划模板（必须在编码之前产出）

> 这是**规划**，不写测试代码。每条用例必须回标 `SPEC-ID`，并注明覆盖的 `IMP-xx`。
> 写不出 SPEC-ID 的用例 → 说明它在测基线外的规则，删掉或回流基线。

---

## test-plan-unit.md（单元测试规划）

### 1. 被测单元清单（只列本次 Code Change Scope 内的）

| # | 被测对象 | 方法/函数 | 关联 SPEC | 关联 IMP |
|---|---|---|---|---|
| U1 | OrderService | `cancel(orderId, reason, operator)` | REQ-SPEC-001 | IMP-03 |
| U2 | RefundCalculator | `calc(order)` | REQ-SPEC-002 | IMP-11 |

> Controller 不做单元测试（走人工接口验证）；Mapper 不做单元测试（走 DB 层验证）。工具类、枚举转换、领域校验可按需纳入。

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

## 规划评审速查（关卡 B 逐条勾）

- [ ] 每条用例都有 SPEC-ID，且 SPEC 均为 SETTLED
- [ ] 每条 IMP-高 至少被一个用例覆盖，否则有豁免记录
- [ ] 边界与异常分支数量 ≥ 正向
- [ ] 断言是强断言（值/码/状态），无 `assertNotNull` 糊弄
- [ ] 单元层无 `@SpringBootTest`、无真实中间件
- [ ] 未覆盖项均有理由，无"待补"
