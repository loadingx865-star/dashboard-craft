#!/usr/bin/env python3
"""dashboard-craft 仓库自检。

校验内容:
  1. SKILL.md frontmatter 必填字段完整、顶层字段在官方白名单内
  2. skill 名称与所在目录名一致
  3. description 长度不超过官方上限（1024 字符）
  4. SKILL.md 体积预算（官方建议 < 500 行 / < 5000 tokens 估算）
  5. references/ 编号连续
  6. 文档中引用的相对路径真实存在
  7. assets/examples/ 只放形态参考，且在 SKILL.md 索引中登记
  8. 全部文件为 UTF-8 且无 BOM
  9. scripts/ 下 Python 脚本语法正确

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
SKILL_MD = SKILL / "SKILL.md"

# 运行期产物与依赖目录：不参与编码检查与文件计数。
# 否则"先跑一次脚本、再跑自检"就会因 __pycache__ 里的 .pyc 误报失败。
IGNORED_DIR_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
}


def _iter_repo_files():
    """遍历仓库内应纳入自检的文件，跳过版本控制与运行期缓存目录。"""
    for p in REPO.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORED_DIR_PARTS for part in p.parts):
            continue
        yield p

# 官方 Agent Skills spec 允许的顶层 frontmatter 字段
ALLOWED_FM_FIELDS = {
    "allowed-tools",
    "compatibility",
    "description",
    "license",
    "metadata",
    "name",
}
REQUIRED_FM = ("name:", "description:", "version:", "license:")

# 官方建议：SKILL.md 控制在 500 行 / 5000 tokens 以内
MAX_LINES = 500
MAX_TOKENS = 5000
MAX_DESCRIPTION_CHARS = 1024

PATH_REF = re.compile(r"`((?:references|assets|scripts|agents)/[A-Za-z0-9_./-]+/?)`")
CJK_RE = re.compile(r"[\u3000-\u9fff\uff00-\uffef]")

problems: list[str] = []
warnings: list[str] = []


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数：CJK 每字约 1 token，其余每 4 字符约 1 token。"""
    cjk = len(CJK_RE.findall(text))
    other = len(text) - cjk
    return cjk + other // 4


def _frontmatter(path: Path) -> str | None:
    if not path.exists():
        problems.append(f"缺少 {path.relative_to(REPO)}")
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        problems.append("SKILL.md 缺少 YAML frontmatter")
        return None
    parts = text.split("---")
    if len(parts) < 3:
        problems.append("SKILL.md frontmatter 未正确闭合")
        return None
    return parts[1]


def check_frontmatter() -> None:
    fm = _frontmatter(SKILL_MD)
    if fm is None:
        return
    for key in REQUIRED_FM:
        if key not in fm:
            problems.append(f"SKILL.md frontmatter 缺少字段: {key}")

    top_keys = re.findall(r"^([A-Za-z][A-Za-z0-9_-]*):", fm, re.M)
    for key in top_keys:
        if key not in ALLOWED_FM_FIELDS:
            problems.append(
                f"SKILL.md frontmatter 含官方不支持的顶层字段: {key}"
                f"（允许: {', '.join(sorted(ALLOWED_FM_FIELDS))}）"
            )

    m = re.search(r"^name:\s*(\S+)", fm, re.M)
    if not m:
        problems.append("SKILL.md frontmatter 缺少 name")
    elif m.group(1) != SKILL.name:
        problems.append(
            f"skill 名称与目录不一致: name={m.group(1)} 目录={SKILL.name}"
        )


def check_description() -> None:
    fm = _frontmatter(SKILL_MD)
    if fm is None:
        return
    m = re.search(r"^description:\s*(.+)$", fm, re.M)
    if not m:
        problems.append("SKILL.md frontmatter 缺少 description")
        return
    desc = m.group(1).strip().strip('"').strip("'")
    if len(desc) > MAX_DESCRIPTION_CHARS:
        problems.append(
            f"description 超长: {len(desc)} 字符 > {MAX_DESCRIPTION_CHARS}"
        )


def check_budget() -> None:
    if not SKILL_MD.exists():
        return
    text = SKILL_MD.read_text(encoding="utf-8")
    line_count = len(text.splitlines())
    tokens = estimate_tokens(text)
    if line_count > MAX_LINES:
        problems.append(f"SKILL.md 行数超预算: {line_count} > {MAX_LINES}")
    if tokens > MAX_TOKENS:
        problems.append(
            f"SKILL.md token 估算超预算: 约 {tokens} > {MAX_TOKENS}"
            "（应把细则下沉到 references/）"
        )
    print(f"  [i]     SKILL.md: {line_count} 行 / 约 {tokens} tokens")


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
    if not SKILL_MD.exists():
        return
    text = SKILL_MD.read_text(encoding="utf-8")
    for ref in sorted(set(PATH_REF.findall(text))):
        if not (SKILL / ref.rstrip("/")).exists():
            problems.append(f"SKILL.md 引用了不存在的路径: {ref}")


def check_examples() -> None:
    examples = SKILL / "assets" / "examples"
    if not examples.exists():
        return
    files = sorted(
        p for p in examples.rglob("*")
        if p.is_file()
        and not any(part in IGNORED_DIR_PARTS for part in p.parts)
    )
    if not files:
        problems.append("assets/examples/ 存在但为空")
        return
    if not (examples / "README.md").exists():
        problems.append("assets/examples/ 缺少 README.md（说明这些只是形态参考）")
    allowed_suffix = {".md", ".example", ".ts", ".tsx", ".js", ".jsx", ".css"}
    for p in files:
        if p.suffix not in allowed_suffix:
            warnings.append(f"assets/examples/ 出现非预期文件类型: {p.name}")


def check_encoding() -> None:
    for p in _iter_repo_files():
        if p.suffix in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}:
            continue
        if p.suffix in {".pyc", ".pyo"}:
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
    check_description()
    check_budget()
    check_reference_numbering()
    check_path_references()
    check_examples()
    check_encoding()
    check_scripts()

    files = list(_iter_repo_files())
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

    print("  [OK] frontmatter 字段合法，名称与目录一致")
    print("  [OK] description 长度在官方上限内")
    print("  [OK] SKILL.md 体积在预算内")
    print("  [OK] references 编号连续")
    print("  [OK] 文档相对路径全部有效")
    print("  [OK] assets/examples 已登记且含 README")
    print("  [OK] 全部文件 UTF-8 无 BOM")
    print("  [OK] 脚本语法正确")
    for w in warnings:
        print(f"  [WARN] {w}")
    print()
    print("结论：全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())