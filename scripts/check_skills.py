#!/usr/bin/env python3
"""Lint the dev-flow skill suite for drift between SKILL.md files.

Usage: python check_skills.py [--root <suite dir>]

Checks per df-*/SKILL.md:
  - frontmatter name equals the directory name
  - has a ## 边界 section
  - every templates/… references/… scripts/… pointer resolves
  - task-dispatch skills (df-task, df-solver) carry all three mode values
  - every skill except df-init stays independent: no reference to another skill
    except the shared ones (df-env / df-grill / df-review)
  - carries the host-fallback bullet for AskUserQuestion
  - scripts with the same file name in different skills are byte-identical
    (copies are allowed, drift is not)

Prints one JSON object; exit 1 when any error exists.
"""
import argparse
import json
import os
import re
import sys

MODES = ("主 Agent", "subagent", "后台")
MODE_OWNERS = {"df-task", "df-solver"}
# 除 df-init 外都必须独立；这三个 skill 被允许作为公共能力被引用
SHARED_EXCEPTIONS = {"df-env", "df-grill", "df-review", "df-tdd"}
ORCHESTRATOR = "df-init"
FALLBACK = "宿主没有 AskUserQuestion"


def check_duplicates(root, dirs, issues):
    import hashlib
    seen = {}
    for d in dirs:
        scripts = os.path.join(root, d, "scripts")
        if not os.path.isdir(scripts):
            continue
        for name in sorted(os.listdir(scripts)):
            if not name.endswith(".py"):
                continue
            path = os.path.join(scripts, name)
            with open(path, "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            seen.setdefault(name, []).append((d, digest))
    for name, copies in seen.items():
        if len(copies) < 2:
            continue
        digests = {digest for _, digest in copies}
        if len(digests) > 1:
            where = "、".join(d for d, _ in copies)
            issues.append({"level": "严重", "file": name,
                           "message": f"同一脚本在 {where} 里内容不一致，拷贝件已漂移"})


def check(root):
    issues = []
    dirs = sorted(d for d in os.listdir(root) if d.startswith("df-") and os.path.isdir(os.path.join(root, d)))
    for d in dirs:
        path = os.path.join(root, d, "SKILL.md")
        rel = d + "/SKILL.md"
        if not os.path.exists(path):
            issues.append({"level": "严重", "file": rel, "message": "缺少 SKILL.md"})
            continue
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        lines = text.splitlines()

        name = None
        if lines and lines[0].strip() == "---":
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                if line.strip().startswith("name:"):
                    name = line.split(":", 1)[1].strip()
        if name != d:
            issues.append({"level": "严重", "file": rel, "message": f"frontmatter name 是 {name!r}，与目录名不符"})
        if "## 边界" not in text:
            issues.append({"level": "严重", "file": rel, "message": "缺 ## 边界 小节"})
        if FALLBACK not in text:
            issues.append({"level": "一般", "file": rel, "message": "缺宿主回退说明（无 AskUserQuestion 时退回编号列表）"})
        if "`直接`" in text:
            issues.append({"level": "严重", "file": rel, "message": "出现旧的两值口径 `直接`，应为 主 Agent/subagent/后台"})
        if d in MODE_OWNERS:
            missing = [m for m in MODES if m not in text]
            if missing:
                issues.append({"level": "严重", "file": rel, "message": f"分派类 skill 缺执行方式取值：{'、'.join(missing)}"})

        if d != ORCHESTRATOR and d not in SHARED_EXCEPTIONS:
            for other in dirs:
                if other == d or other in SHARED_EXCEPTIONS or other == ORCHESTRATOR:
                    continue
                for i, line in enumerate(lines, 1):
                    if other in line:
                        issues.append({"level": "严重", "file": rel,
                                       "message": f"独立 skill 不得引用 {other}（第 {i} 行）"})
        for m in re.finditer(r"(?<!\.\./)(?<![\w./])(templates|references|scripts)/([A-Za-z0-9_.\-]+)", text):
            local = os.path.join(root, d, m.group(1), m.group(2))
            shared = os.path.join(root, m.group(1), m.group(2))
            if not (os.path.exists(local) or os.path.exists(shared)):
                issues.append({"level": "严重", "file": rel,
                               "message": f"指向不存在的文件：{m.group(1)}/{m.group(2)}（skill 目录与套件根都没有）"})

        desc = ""
        for line in lines:
            if line.strip().startswith("description:"):
                desc = line.split(":", 1)[1].strip()
                break
        if len(desc) > 200:
            issues.append({"level": "一般", "file": rel, "message": f"description 有 {len(desc)} 字符，建议 <= 200"})

    check_duplicates(root, dirs, issues)
    fatal = [i for i in issues if i["level"] == "严重"]
    return {"ok": not fatal, "skills": len(dirs),
            "stats": {"issues": len(issues), "fatal": len(fatal)},
            "issues": issues}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = ap.parse_args()
    result = check(os.path.abspath(args.root))
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 1 if not result["ok"] else 0


if __name__ == "__main__":
    sys.exit(main())
