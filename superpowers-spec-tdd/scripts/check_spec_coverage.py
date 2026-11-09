#!/usr/bin/env python3
"""SPEC-ID 覆盖机械校验。

用途：在 Execute-plan 的 E4 阶段核对「规约里的每条 SETTLED 规则是否真的被 plan / 测试 / 代码引用」，
避免人工肉眼漏检。纯本地工具，不接 CI。

用法：
    python3 check_spec_coverage.py <root> --baseline baseline-spec.md \
        --scan plan.md src/test src/main [--require-impact] [--quiet]

退出码：
    0  所有锁定 ID 均被引用（且未出现悬空引用）
    1  存在未覆盖的锁定 ID，或存在引用了基线中不存在的悬空 ID
    2  参数/文件错误
"""

import argparse
import os
import re
import sys

SPEC_RE = re.compile(r"\b(REQ-SPEC-\d+|INV-\d+|IMP-\d+)\b")
IMP_RE = re.compile(r"\bIMP-\d+\b")
# 条目块起点只认「标题行」或「表格首列定义行」，
# 避免正文顺带提及、版本记录、审计表把引用误判为定义行。
HEADING_ID_RE = re.compile(r"^ {0,3}#{1,6}\s+(REQ-SPEC-\d+|INV-\d+)\b")
TABLE_ID_RE = re.compile(r"^\s*\|\s*(REQ-SPEC-\d+|INV-\d+)\s*\|")
# 条目内降级标记（与 baseline-spec-template.md 约定一致）：- 分区：OPEN / 分区：OUT_OF_SCOPE
OPEN_STATUS_RE = re.compile(r"(?:分区|状态|status)\s*\**\s*[:：]\s*(OPEN|OUT_OF_SCOPE)\b")

TEXT_EXTS = {
    ".md", ".txt", ".java", ".kt", ".py", ".go", ".ts", ".js", ".tsx", ".jsx",
    ".rs", ".sql", ".json", ".feature",
}

# 配置文件一律排除：不读取 yml/yaml/properties 等配置内容，
# 只在代码/测试/规划文档里匹配 SPEC-ID。
CONFIG_EXTS = {".yml", ".yaml", ".properties", ".ini", ".toml", ".env", ".conf"}
CONFIG_NAME_RE = re.compile(
    r"(^|\.)((application|bootstrap)[\w.-]*|docker-compose.*|pom|build|settings|gradle\.properties)$",
    re.IGNORECASE,
)

SKIP_DIRS = {
    ".git", "node_modules", "target", "build", "dist", ".idea", ".gradle",
    "__pycache__", ".venv", "venv", ".mvn",
}


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError as exc:
        print(f"[warn] 无法读取 {path}: {exc}", file=sys.stderr)
        return ""


def parse_baseline(path):
    """返回 (locked_ids, open_ids, spec_blocks)。

    spec_blocks: id -> 该条目块文本，用于 IMP 绑定检查。
    块起点只认标题行（### REQ-SPEC-001）或表格首列定义行（| INV-001 | ... |），
    正文/版本记录中的顺带引用不会开启新块，避免切块边界错乱。
    """
    text = read_text(path)
    if not text:
        return set(), set(), {}

    lines = text.splitlines()
    ids_in_order = []
    blocks = {}
    current = None
    buf = []

    def flush():
        if current is not None:
            blocks[current] = "\n".join(buf)

    for line in lines:
        matched = HEADING_ID_RE.match(line) or TABLE_ID_RE.match(line)
        if matched:
            rid = matched.group(1)
            if rid not in blocks and rid not in ids_in_order:
                flush()
                current = rid
                ids_in_order.append(rid)
                buf = [line]
                continue
        if current is not None:
            buf.append(line)
    flush()

    locked, open_ids = set(), set()
    for rid in ids_in_order:
        block = blocks.get(rid, "")
        if OPEN_STATUS_RE.search(block):
            open_ids.add(rid)
        else:
            locked.add(rid)
    return locked, open_ids, blocks


def is_config_file(name):
    """按扩展名和常见配置文件名（application*.yml / pom.xml 等）判定是否为配置文件。"""
    ext = os.path.splitext(name)[1].lower()
    if ext in CONFIG_EXTS:
        return True
    return bool(CONFIG_NAME_RE.search(name))


def iter_files(paths, baseline_abs):
    for p in paths:
        if os.path.isfile(p):
            if (
                os.path.abspath(p) != baseline_abs
                and os.path.splitext(p)[1].lower() in TEXT_EXTS
                and not is_config_file(os.path.basename(p))
            ):
                yield p
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for name in files:
                    ext = os.path.splitext(name)[1].lower()
                    if ext not in TEXT_EXTS:
                        continue
                    if is_config_file(name):
                        continue
                    fp = os.path.join(root, name)
                    if os.path.abspath(fp) == baseline_abs:
                        continue
                    yield fp
        else:
            print(f"[warn] 路径不存在，已跳过：{p}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="SPEC-ID 覆盖校验")
    ap.add_argument("root", help="项目根目录")
    ap.add_argument("--baseline", required=True, help="基线文件（相对 root 或绝对路径）")
    ap.add_argument("--scan", nargs="+", required=True, help="待扫描的文件或目录")
    ap.add_argument("--require-impact", action="store_true", help="检查每条 REQ-SPEC 是否绑定 IMP")
    ap.add_argument("--quiet", action="store_true", help="只输出结论")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print(f"[error] root 不是目录：{args.root}", file=sys.stderr)
        return 2

    baseline = args.baseline
    if not os.path.isabs(baseline):
        baseline = os.path.join(args.root, baseline)
    if not os.path.isfile(baseline):
        print(f"[error] 基线文件不存在：{baseline}", file=sys.stderr)
        return 2

    locked, open_ids, blocks = parse_baseline(baseline)
    if not locked and not open_ids:
        print("[error] 基线中未解析到任何 REQ-SPEC-xxx / INV-xxx", file=sys.stderr)
        return 2

    scan_targets = [t if os.path.isabs(t) else os.path.join(args.root, t) for t in args.scan]
    base_abs = os.path.abspath(baseline)

    refs = {}
    for fp in iter_files(scan_targets, base_abs):
        text = read_text(fp)
        for rid in SPEC_RE.findall(text):
            refs.setdefault(rid, set()).add(os.path.relpath(fp, args.root))

    missing = sorted(rid for rid in locked if rid not in refs)

    known = locked | open_ids
    dangling = sorted(
        rid for rid in refs
        if rid.startswith(("REQ-SPEC-", "INV-")) and rid not in known
    )

    impact_issues = []
    if args.require_impact:
        for rid, block in blocks.items():
            if rid.startswith("REQ-SPEC") and rid in locked and not IMP_RE.search(block):
                impact_issues.append(rid)

    if not args.quiet:
        print(f"基线：{os.path.relpath(baseline, args.root)}")
        print(f"锁定条目 {len(locked)} 条，待探索/不做 {len(open_ids)} 条，"
              f"扫描到 {len(refs)} 个 ID 引用\n")
        print("== 锁定条目引用情况 ==")
        for rid in sorted(locked):
            where = ", ".join(sorted(refs.get(rid, []))) or "（无）"
            print(f"  {'OK  ' if rid in refs else 'MISS'}  {rid}  -> {where}")
        if open_ids:
            print("\n== 待探索/不做（不要求覆盖）==")
            for rid in sorted(open_ids):
                print(f"  --   {rid}")
        if dangling:
            print("\n== 悬空引用（基线中不存在，疑似脑补或笔误）==")
            for rid in dangling:
                print(f"  ??   {rid}  -> {', '.join(sorted(refs[rid]))}")
        if impact_issues:
            print("\n== 未绑定 IMP 的 SETTLED 规则 ==")
            for rid in impact_issues:
                print(f"  !!   {rid}")

    problems = []
    if missing:
        problems.append(f"未覆盖锁定条目 {len(missing)} 条：{', '.join(missing)}")
    if dangling:
        problems.append(f"悬空引用 {len(dangling)} 条：{', '.join(dangling)}")
    if impact_issues:
        problems.append(f"未绑定 IMP 的规则 {len(impact_issues)} 条：{', '.join(impact_issues)}")

    print()
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print("[PASS] 所有锁定条目均被引用，无悬空引用")
    return 0


if __name__ == "__main__":
    sys.exit(main())
