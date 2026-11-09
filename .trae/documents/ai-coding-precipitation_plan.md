# AI 编程工作流沉淀 Plan（v2）

## 反转思路：先有验证过的工作流骨架，再填原理

**v1 被拒的根因**：把小林面试笔记 14 篇当骨架，从文章里"重新推导"提示词和模板 → 学术化、产物碎片化、与用户日常用的 Superpowers/Plan Mode 没接上。

**v2 的骨架**（已验证、已有可复制 prompt）：
1. **Matt Pocock Skills v1.2.3** 的 25 个 skill + 6 组常用搭配 + 可直接复制的提示词
2. **GitHub Spec Kit** 的 spec.md / plan.md / tasks.md 三文档体系 + Constitution.md 项目原则
3. **AGENTS.md 授权边界**（来自 Matt Pocock 文档末尾的那段）

**小林面试笔记 14 篇** → 作为每个阶段的「原理支撑 + 反例 + 什么时候不适用」的注释层，不独立产文件。

---

## 二、三大信息源的交叉映射

| Matt Pocock Skill | 小林面试文章 | Spec Kit 对应物 | 说明 |
|---|---|---|---|
| `grill-with-docs` | T2 需求描述 + T3 上下文 + T4 代码定位 | /speckit-clarify /speckit-specify | 追问→澄清→规格，三段式 |
| `to-spec` | T2 需求描述 + T5 Vibe vs Spec | spec.md | 聊天结论→正式规格 |
| `to-tickets` | T6 任务拆分 | tasks.md | 规格→可执行任务 |
| `tdd` | T7 代码质量 + T10 测试覆盖 | /speckit-implement 的实现阶段 | 红→绿→重构 + 规则→场景推导 |
| `code-review` | T8 代码审查 + T7 质量检查 | /speckit-converge | 两条线：代码质量 + 需求对齐 |
| `diagnosing-bugs` | T9 调试排查 | — | 稳定复现→缩小范围→修复→回归 |
| `handoff` | T11 上下文管理 + T13 跨会话交接 | — | 会话摘要 + 工作区核对 + 交接文档 |
| `domain-modeling` | T12 过期描述 + T4 定位 | — | 共同语言 + 边界场景 |
| `wayfinder` | T6 大项目拆分 | — | 决策地图 vs 实现任务 |
| `research` | T4 定位里的外部资料查找 | — | 一手资料 + 来源 |
| `setup-matt-pocock-skills` | — | constitution.md | 项目原则 |
| **AGENTS.md 授权边界** | T14 权限边界 | — | 三层：任务授权 / 工具能力 / 执行隔离 |

---

## 三、要产出的文件（压缩到 5 个）

全部放在 `/Users/chenjunbing/Develop/Project/Personal/Agent-Coding/` 根目录，文件名清晰、可直接用。

### 文件 1：`AI-CODING-WORKFLOW.md` — 工作流总指南（核心）
按 **7 个阶段** 组织，每阶段包含：
- 🦴 **骨架**：Matt Pocock 对应 skill + 可直接复制的提示词
- 📖 **原理**：小林面试文章对应编号的简要摘录（一句话说明为什么这样做）
- ⚠️ **反例**：面试官翻车现场里的典型错误
- 🔗 **Spec Kit 对应**：用哪个 `/speckit-*` 命令
- 📎 **关联模板**：指向下面的模板文件

7 个阶段：
1. **Grill 追问澄清** → `grill-with-docs`
2. **Spec 规格整理** → `to-spec` → spec.md
3. **Tickets 任务拆分** → `to-tickets` → tasks.md
4. **Codebase 设计** → `codebase-design`
5. **TDD 实现** → `tdd`
6. **Review 审查** → `code-review` + 授权边界 AGENTS.md
7. **Debug / Handoff** → `diagnosing-bugs` + `handoff` + context.md + HANDOFF.md

额外章节：
- **6 组搭配速查表**（直接搬 Matt Pocock 文档里的那张表）
- **25 个 Skill 完整索引**（名称 + 一句话作用 + 主动/按需调用）
- **AGENTS.md 授权边界模板**（来自 Matt Pocock 文档末尾，Java 项目版）
- **三大信息源交叉映射表**（就是上面那张表）

### 文件 2：`SPEC.md` — 规格模板（Java/SpringBoot 项目适配版）
来自 Spec Kit 的 spec.md 概念 + 小林 T2 的五段式 + Matt Pocock `to-spec` 的内容要点。
结构：目标 → 范围（这次做/不做）→ 行为规则（输入输出边界）→ 技术约束 → 验收标准 → 测试方式。

### 文件 3：`TASKS.md` — 任务清单模板
来自 Spec Kit 的 tasks.md + 小林 T6 的四要素（目标/前置/范围/依据）+ Matt Pocock `to-tickets` 的 Blocked by 关系。
结构：总体约定 → T1 分析 → T2 接口 → T3 实现 → T4 联调 → T5 回归。每项四要素齐全。

### 文件 4：`HANDOFF.md` — 交接模板
来自小林 T13 + Matt Pocock `handoff`。
结构：目标约定 → 代码现场（含未提交/新文件）→ 进度 → 验证记录（对应版本）→ 运行状态 → 下一步。

### 文件 5：`AI-CODING-INDEX.md` — 总索引（一张表）
交叉索引：场景 → 推荐 Skill → 提示词 → 模板 → 小林原理来源。

---

## 四、不做的事（v1 里哪些砍掉）

- ❌ prompts/ 目录拆 7 份独立 prompt → 全部合并到 WORKFLOW.md 的 7 个阶段里
- ❌ checklists/ 目录 3 份 → Checklist 内容合并到对应阶段的"验证方式"段落
- ❌ knowledge/ 目录 4 份 → 小林的原理/反例直接作为 WORKFLOW.md 的注释层，不独立存
- ❌ debug.md / review.md / context.md 独立模板 → 合并进 WORKFLOW.md 的 Debug/Handoff 章节里，不单独产

---

## 五、实现步骤

1. 写 `AI-CODING-WORKFLOW.md`（工作量最大，约 7 阶段 × 150 行 = 1000 行）
   - 每个阶段先写骨架（Matt Pocock 提示词原样搬）
   - 再插小林文章的原理摘要 + 反例
   - 最后加 Spec Kit 对应 + 关联模板指针
2. 写 `SPEC.md`（约 80 行）
   - 参考 Spec Kit spec.md 概念 + 小林 T2 五段式 + Matt Pocock to-spec 要点
   - 用 SpringBoot/MyBatis 项目的订单校验场景做示例值
3. 写 `TASKS.md`（约 100 行）
   - 参考 Spec Kit tasks.md + 小林 T6 四要素 + Matt Pocock to-tickets 的 Blocked by
4. 写 `HANDOFF.md`（约 60 行）
   - 小林 T13 结构 + Matt Pocock handoff 要点
5. 写 `AI-CODING-INDEX.md`（约 50 行）
   - 场景 → Skill → 提示词位置 → 模板 → 小林编号 的交叉索引表

---

## 六、风险与处理

| 风险 | 处理 |
|---|---|
| 小林文章用 JS/TS 示例，用户用 Java/SpringBoot | 模板里的占位符和示例值改成 Java/SpringBoot（如 `src/order/OrderService.java`），WORKFLOW.md 里的提示词保留 Matt Pocock 原文风格（因为提示词是通用的） |
| Matt Pocock Skill 在 TRAE 里不直接叫这名字 | WORKFLOW.md 里每个阶段都标注"对应 TRAE 里的 XX Skill"（如 `grill-with-docs` ≈ TRAE spec-mode 的 clarify 阶段），但骨架提示词保留原样，因为用户也可以手动写 |
| 内容可能与 Superpowers Skill 重叠 | 在交叉映射表里标注哪些是重叠（只做补充不替代），哪些是全新（独立产出） |
| 5 个文件仍然较多 | 如果用户觉得多，可以把 SPEC.md / TASKS.md / HANDOFF.md 三个模板合并成一个 `TEMPLATES.md`，只是可读性稍差 |

---

## 七、验证

- WORKFLOW.md 7 个阶段的每个提示词都能直接复制使用（不引用外部文件）
- 3 个模板都有 SpringBoot 项目的示例值（不是空壳）
- 交叉映射表能回答"我现在要做 X，该用哪个 Skill + 哪段提示词 + 哪个模板"
