# 编码规约（项目级）

> **版本**：v1.4（2026-11-10；自原始 v1.3 迁出规范条目，砍历史/背景/落地方式）
> **适用**：本仓库全部新增/改动代码。存量代码按"记录、不在本规范内做强制整改"处理。
> **依赖**：SpringBoot 2.1.3.RELEASE / MyBatis 多模块（api / service / dao / entity / util）

---

## 1. 分层：Controller → Service → Mapper（强制）

```
Controller  →  Service  →  Mapper
（协议层）      （业务+事务）  （SQL 映射）
```

| 层 | 应做 | 禁止 |
|---|---|---|
| Controller | Swagger 注解；入参/出参为 `XxxModel` / `XxxParam` / `XxxVo`；`@AuthCode` 权限；`@CurrentUser` 取当前用户 | **注入或调用 Mapper（强制）**；写业务判断；写 SQL；开事务 |
| Service | 业务编排；事务边界；跨表一致性；组装 Vo | 返回 `ApiResponse`；依赖 `HttpServletRequest`/`Session`；直接抛 Http 状态码 |
| Mapper | 单表/联表 SQL；`period_id`/`org_id`/`state` 条件过滤 | 业务判断；拼装权限；循环查库（N+1，见 §5 N1） |

## 2. Model / Param / Vo 继承约定

| 类型 | 职责 | 继承 | 创建时机 |
|---|---|---|---|
| `XxxModel` | 表结构映射（`@Data`，字段与列一一对应） | 适当时 `extends BaseModel`（见下） | 每个业务实体必备 |
| `XxxParam` | 请求入参（可加校验/前端专用字段） | **必须 `extends XxxModel`** | 入参需校验注解或前端专用字段时 |
| `XxxVo` | 响应出参（可加派生/脱敏/子集合字段） | **必须 `extends XxxModel`** | 响应需派生/脱敏/拼子集合时 |

### Model 继承 BaseModel 规则

- **应继承**：主业务表含 `state` + 创建/修改审计列 → `extends BaseModel`，子类只声明业务列，不重复声明基类字段
- **可继承**：表无 `state` 但有审计列 → 仍可 `extends BaseModel` 复用审计字段；Mapper 不得读写表中不存在的基类列
- **可不继承**：纯关联/中间表、或存量已走 `PageModel`/`Serializable` 的写法；审计字段在子类内自声明

### Model 禁止项

- 禁止在 `XxxModel` 上增加表中不存在的业务/查询属性（如查询开关 `allPeriod`、`IN` 条件集合 `periodIds`）——此类字段放 `Param` 或独立 Query 对象
- `Param` 与 `Vo` **互不继承**：不出现 `Vo extends Param`、`Param extends Vo`；二者只能各自 `extends XxxModel` 并列存在
- 不重复声明 Model 已有的同名列；确需改变语义时另行命名

### Service 方法签名

入参/出参可为 `Model` / `Param` / `Vo` / 集合，按是否需要区分读写语义决定；**不要求新增方法必须用 Param/Vo**。

## 2.1 Mapper 方法参数（强制）

- 新增 Mapper 方法参数**尽量 ≤ 3 个**（含 `@Param` 基础类型）
- 超过 3 个 → 改为单个对象入参（`XxxParam` / `XxxQuery`），XML 用对象属性取值；**禁止堆 `@Param`**
- 单表 CRUD 优先复用 `BaseMapper` + `XxxModel` 条件对象

## 2.2 类注释与作者（新增类强制）

新增 `*Model` / `*Mapper` / `*Param` / `*Vo` / `*Service(Impl)` / 枚举须补类级 JavaDoc：

```java
/**
 * 学段实体
 * PeriodModel 对应数据库表 period
 *
 * @author Junbing.Chen
 * @date YYYY-MM-DD
 */
```

- `*Model`：写明"对应数据库表 xxx"，字段旁注释列名（`/** 学段名称 name */`）
- `*Mapper`：接口级注释 + 非常规方法 `@param`/`@return`
- 新增类作者统一 `@author Junbing.Chen`

## 2.3 Mapper 共用 Where vs Param 条件分离（强制）

`selectList` / 共用 `<where>` **只写 Model 表字段**。`periodIds`/`parentIds` 等 Param 专有条件：
- **优先**：另开查询方法（如 `selectListByParam(XxxParam)`），XML 入参统一为 Param
- **或**：该语句链路入参全部改为 Param

禁止在 Model 共用 `<where>` 里写 Param 字段，也禁止用 `instanceof` 在 XML 里兜底。

## 2.4 改动类清理无用 import（强制）

本批次新增或改动的 Java 文件，提交前必须清理无用 import（含误入 `static import`、显式 `java.lang.*`）：
- 类型/成员名在文件内除 import 行外零引用 → 删除该 import
- 禁止为通过编译保留"可能以后用"的 import
- 功能改完、规约整改、字段迁移后同一轮做完

## 3. Swagger 文档

- Controller 类：`@Api(tags = "...")`；方法：`@ApiOperation(value = "...")`
- Param 字段：`@ApiModelProperty`；或在接口上 `@ApiImplicitParam(s)`——**同一个 Controller 内须保持一致**
- 隐式参数（分页、`periodId`、`orgId` 等）必须显式声明
- 返回值结构变更须在 `@ApiOperation` 或字段 `@ApiModelProperty` 上说明

## 4. 事务（Service 层）

- **判定口径**：**单表单语句**可不加事务；**跨表、同表多语句、先查后写依赖**必须加 `@Transactional(rollbackFor = Exception.class)`
- 事务注解加在 **ServiceImpl 的 public 方法**上；同类内部调用不走代理，注解无效
- **事务内禁止**：远程调用、MQ 发送、大批量循环逐条 insert、长时间计算
- 跨服务编排由**最外层入口**持有事务，内层 `@Transactional` 用默认 `REQUIRED` 加入，不得各自 `REQUIRES_NEW`

## 5. 性能与并发设计红线（N1~N6）

所有新增/改动以高并发系统标准设计，不以"数据量小"豁免。设计须按下述最坏情况推演：**10 学段 / 500 机构 / 5 万教师 / 字典 16 类×每类 50 项 / 评选活动参与人 1 万**。

| 编号 | 红线 | 具体要求 |
|---|---|---|
| **N1** | 禁止 N+1 | 循环体内不得查库或调远程服务；列表派生字段必须**一次批量取回后内存拼装** |
| **N2** | 新增查询必须命中索引 | 新增的 `WHERE`/`JOIN`/`ORDER BY` 列须有可用索引；存量表索引变更须提供 `EXPLAIN` 改造前后对比 |
| **N3** | 禁止无界查询 | 下拉/候选/模糊搜索须带 `LIMIT`；`IN` 集合超 1000 须分片；禁止无条件 `selectList` 后内存分页 |
| **N4** | 热路径必须走缓存 | 字典/学段/机构树属低频变更高频读取主数据，须走 Redis + **主动失效**，不能只依赖过期时间 |
| **N5** | 禁止请求链路内重计算 | 优先一次聚合查询替代多次单条；单次同步计算超 200ms 须评估异步化 |
| **N6** | 写操作幂等 + 事务粒度受控 | 禁止事务内包裹远程调用或长循环；批量写用批量语句；新增写接口须说明幂等性 |

## 6. 性能基线采集方法（零侵入三层）

### 前提（不满足则基线无效）

1. 数据量级接近生产（生产只读副本或导入脱敏生产数据的预发）
2. 避开定时任务窗口（采集时段错开 quartz Runner）
3. 改造前后同环境/参数/并发/时长

### 层 1：接口 RT（curl / ab / wrk）

```bash
# 单次定位
curl -s -o /dev/null \
  -w "http=%{http_code} total=%{time_total}s ttfb=%{time_starttransfer}s\n" \
  -H "<鉴权头>: <token>" \
  "http://<host>:<port>/<path>?<param>=1"

# 并发分位
ab -n 500 -c 20 -H "<鉴权头>: <token>" "http://<host>:<port>/<path>?<param>=1"
wrk -t4 -c50 -d60s --latency -s /tmp/auth.lua "http://<host>:<port>/<path>?<param>=1"
```

### 层 2：SQL 条数（零代码，复用 MyBatis DEBUG 日志）

1. 采集环境临时调 `logging.level.com.mhqc.dao=DEBUG`（不改代码、不提交）
2. 单发一次请求（并发 1），`grep -c "==>  Preparing:" app.log` 即为 SQL 条数
3. 同一 SQL 模板重复 N 次 = N+1 证据

### 层 3：DB 侧扫描行数（DBA 执行）

```sql
SELECT DIGEST_TEXT, COUNT_STAR AS exec_cnt,
       SUM_ROWS_EXAMINED AS rows_examined,
       SUM_ROWS_SENT AS rows_sent,
       ROUND(SUM_TIMER_WAIT / 1e9, 1) AS total_ms,
       ROUND(AVG_TIMER_WAIT / 1e6, 2) AS avg_ms
FROM performance_schema.events_statements_summary_by_digest
WHERE SCHEMA_NAME = '<业务库名>'
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 20;
```

### 产出物模板

目录 `docs/<分支>/perf-baseline/`，文件名 `YYYY-MM-DD-<env>-before.md` / `-after.md`：

| 接口 | 并发 | P50(ms) | P95(ms) | P99(ms) | QPS | SQL 条数 | 扫描行数 | 环境/规模 | 备注 |
|---|---|---|---|---|---|---|---|---|---|

文件头须写明：环境、采集时间、采集人、数据规模、是否开启缓存、JVM 参数。

## 7. 重复代码重构原则（Rule of Three）

| 次数 | 处置 |
|---|---|
| **第一次** | 直接新写，**不提前抽象**——没有证据证明这段代码会被复用 |
| **第二次** | 可复制，也可重构（提取为私有方法/静态工具方法）——成本可接受；**禁止过度抽象**（泛型化、反射、SPI…） |
| **第三次** | **必须重构**——提取为可复用的公共组件（Service 方法 / Util / 独立类），消除重复；抽象层级与复用场景匹配，避免为了"干净"而引入不必要的复杂度 |

> **禁止**：第一次出现就抽 Utils、就做模板方法、就设计扩展点——YAGNI（You Aren't Gonna Need It）。

---

## 变更记录

- **v1.4.1（2026-11-10）**：补 §7 重复代码重构原则（Rule of Three：第一次新写 / 第二次可复制可重构 / 第三次必须重构）
- **v1.4（2026-11-10）**：自原始 v1.3 迁出，砍掉历史背景/现状实测/工时估算/C44 案例，保留纯规则；新增 §6 性能基线采集简化版
- **v1.3（2026-11-02）**：§2.3 Model 共用 Where 与 Param 条件分离
- **v1.2（2026-11-02）**：§2.4 改动类清理无用 import
- **v1.1（2026-11-02）**：补强制条——BaseModel 继承、Mapper 参数 ≤3、类注释、Param/Vo 字段注释
