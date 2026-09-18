#!/usr/bin/env python3
"""dashboard-craft 仓库自检。

校验内容:
  1. SKILL.md frontmatter 必填字段完整
  2. skill 名称与所在目录名一致
  3. references/ 编号连续
  4. 文档中引用的相对路径真实存在
  5. 全部文件为 UTF-8 且无 BOM
  6. scripts/ 下 Python 脚本语法正确

用法:
    python tools/check_skill.py
退出码: 0 通过, 1 发现问题。
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dashboard-craft"
REQUIRED_FM = ("name:", "description:", "version:", "license:")
PATH_REF = re.compile(r"`((?:references|assets|scripts|agents)/[A-Za-z0-9_./-]+/?)`")

problems: list[str] = []


def check_frontmatter() -> None:
    skill_md = SKILL / "SKILL.md"
    if not skill_md.exists():
        problems.append(f"缺少 {skill_md.relative_to(REPO)}")
        return
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        problems.append("SKILL.md 缺少 YAML frontmatter")
        return
    parts = text.split("---")
    if len(parts) < 3:
        problems.append("SKILL.md frontmatter 未正确闭合")
        return
    fm = parts[1]
    for key in REQUIRED_FM:
        if key not in fm:
            problems.append(f"SKILL.md frontmatter 缺少字段: {key}")

    m = re.search(r"^name:\s*(\S+)", fm, re.M)
    if not m:
        problems.append("SKILL.md frontmatter 缺少 name")
    elif m.group(1) != SKILL.name:
        problems.append(
            f"skill 名称与目录不一致: name={m.group(1)} 目录={SKILL.name}"
        )


def check_reference_numbering() -> None:
    refs = sorted((SKILL / "references").glob("*.md"))
    if not refs:
        problems.append("references/ 下没有文件")
        return
    nums = []
    for p in refs:
        m = re.match(r"^(\d{2})-", p.name)
        if not m:
            problems.append(f"references 文件名未按 NN- 前缀编号: {p.name}")
            continue
        nums.append(int(m.group(1)))
    if nums and nums != list(range(1, len(nums) + 1)):
        problems.append(f"references 编号不连续: {nums}")


def check_path_references() -> None:
    skill_md = SKILL / "SKILL.md"
    if not skill_md.exists():
        return
    text = skill_md.read_text(encoding="utf-8")
    for ref in sorted(set(PATH_REF.findall(text))):
        if not (SKILL / ref.rstrip("/")).exists():
            problems.append(f"SKILL.md 引用了不存在的路径: {ref}")


def check_encoding() -> None:
    for p in REPO.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.suffix in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}:
            continue
        raw = p.read_bytes()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"文件不是 UTF-8 编码: {p.relative_to(REPO)}")
            continue
        if raw[:3] == b"\xef\xbb\xbf":
            problems.append(f"文件含 BOM: {p.relative_to(REPO)}")


def check_scripts() -> None:
    scripts_dir = SKILL / "scripts"
    if not scripts_dir.exists():
        problems.append("缺少 scripts/ 目录")
        return
    found = False
    for p in scripts_dir.glob("*.py"):
        found = True
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as e:
            problems.append(f"脚本语法错误: {p.name}: {e}")
    if not found:
        problems.append("scripts/ 下没有 Python 脚本")


def main() -> int:
    check_frontmatter()
    check_reference_numbering()
    check_path_references()
    check_encoding()
    check_scripts()

    files = [p for p in REPO.rglob("*") if p.is_file() and ".git" not in p.parts]
    print("=" * 60)
    print("dashboard-craft 仓库自检")
    print("=" * 60)
    print(f"仓库根目录: {REPO}")
    print(f"文件总数  : {len(files)}")
    print()

    if problems:
        for p in problems:
            print(f"  [FAIL] {p}")
        print()
        print(f"结论：不通过（{len(problems)} 个问题）")
        return 1

    print("  [OK] frontmatter 完整，名称与目录一致")
    print("  [OK] references 编号连续")
    print("  [OK] 文档相对路径全部有效")
    print("  [OK] 全部文件 UTF-8 无 BOM")
    print("  [OK] 脚本语法正确")
    print()
    print("结论：全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
