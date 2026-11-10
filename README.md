# Agent-Coding Skills 维护仓库

本仓库**只做一件事**：存放可复用的 AI 编程 Skill。其他项目仓库通过**软链接**方式引用本仓库内的 skill 目录，不需要拷贝、不需要 submodule、不需要安装脚本。

## 设计原则

- **一处维护，多项目生效**：skill 只在本仓库里维护，更新一次，所有软链接项目自动同步。
- **纯 Markdown + 可选脚本**：skill 本体只有 `SKILL.md`（指令）+ `references/`（模板）+ `scripts/`（机械校验）。不引入可执行包管理、不编译、不依赖运行时。
- **目录即 Skill**：本仓库根目录下每个一级子目录就是一个 skill，目录名必须与 `SKILL.md` frontmatter 里的 `name` 字段完全一致。

## 当前 Skill 列表

| Skill | 说明 | 适用场景 |
|---|---|---|
| [superpowers-spec-tdd](./superpowers-spec-tdd/) | Superpowers 流程加固版：结构化需求基线 + 波及面扫描 + 基线对齐审计 + 测试规划前置于编码 + 偏差回流 | 需求基线、需求漂移、波及面分析、测试先行、TDD 落地、前端联调契约 |

每个 skill 目录结构：

```
<skill-name>/
├── SKILL.md                  # 必须，frontmatter + 正文指令
├── references/               # 可选，长文档/模板/示例（正文只做一层引用）
└── scripts/                  # 可选，确定性校验脚本
```

## 安装方式（软链接）

### Trae

```bash
# 项目级（推荐，随仓库走，团队成员拉代码就能用）
ln -s /path/to/Agent-Coding/superpowers-spec-tdd  <你的项目>/.trae/skills/superpowers-spec-tdd

# 全局级（所有项目共享，但不随仓库走）
ln -s /path/to/Agent-Coding/superpowers-spec-tdd  ~/.trae-cn/skills/superpowers-spec-tdd
```

### Cursor

```bash
# Cursor 的 project rules 目录
ln -s /path/to/Agent-Coding/superpowers-spec-tdd/SKILL.md  <你的项目>/.cursor/rules/superpowers-spec-tdd.mdc
# 注意：Cursor 只认单文件，软链接时会把 references/ 和 scripts/ 丢掉，
# 建议 Trae 项目级软链接为主，Cursor 场景按需拷贝
```

### Codex / Worbuddy / 其他

```bash
# 通用方式：找到对应工具的 skills/rules 目录，软链接目录
ln -s /path/to/Agent-Coding/superpowers-spec-tdd  <工具的 skill 目录>/superpowers-spec-tdd
```

### 一键脚本（推荐）

在你的项目里加一个 `scripts/link-skills.sh`：

```bash
#!/usr/bin/env bash
# 指向本仓库的绝对路径
SKILLS_REPO="/path/to/Agent-Coding"
TARGET_DIR=".trae/skills"
SKILLS=("superpowers-spec-tdd")

mkdir -p "$TARGET_DIR"
for skill in "${SKILLS[@]}"; do
  src="$SKILLS_REPO/$skill"
  dst="$TARGET_DIR/$skill"
  if [ -L "$dst" ]; then
    echo "已存在软链接：$dst"
  elif [ -e "$dst" ]; then
    echo "⚠️  $dst 已存在且不是软链接，跳过（手动处理）"
  else
    ln -s "$src" "$dst"
    echo "✅ 软链接：$dst → $src"
  fi
done
```

## 更新 Skill

直接在本仓库里改，其他项目的软链接自动生效（改了即同步，不需要重新链接）。

如果改了 skill 的目录名或 `name` 字段，**所有引用的项目都要重建软链接**（软链接是硬编码路径的，目录名变了会断）。

## 维护规则

- **新增 skill**：在本仓库根目录下新建一级目录，目录名 = `SKILL.md` 的 `name` 字段 = kebab-case，2–64 字符。
- **skill 目录**：`SKILL.md` 正文不超过 500 行；长内容放 `references/`，正文只做一层引用；脚本放 `scripts/`，必须可独立执行、退出码语义清晰。
- **不引入**：README/CHANGELOG 等人读文件（读者读 SKILL.md 就行）、第三方依赖、编译产物。
- **frontmatter**：只保留 `name` + `description`，无多余字段；`description` 单行、无 `: `、无 `<` `>`、包含 what + when 触发词。
