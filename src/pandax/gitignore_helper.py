"""维护项目 .gitignore,确保 PandaX 自动产物不被 git 跟踪。

第一性原理(为什么这个模块存在):
  - pandax lock 会写入 `desktop.ini`(Windows 文件夹图标配置)
  - pandax init 会创建 `.pandax/` 目录(配置/审计/快照)
  - 这些文件**不应**被 git 跟踪:
    - `.pandax/` 是运行时状态(每台机器可能不同,审计日志是个人数据)
    - `desktop.ini` 是 Windows-only 文件,macOS/Linux 协作无意义
    - TortoiseGit / VSCode 等工具见到 desktop.ini 会显示污染状态
  - 用户经常忘记加 .gitignore → `git status` 噪音 → 偶尔误 add → 污染仓库

对抗式审查:
  - 不能覆盖用户的 .gitignore:用"追加缺失条目"策略,保留所有现有规则
  - 不能在非 git 目录乱创建 .gitignore:先探测 `.git/`
  - 不能重复添加条目:逐行检测,已存在则跳过
  - 顺序敏感:.pandax/ 必须先于 desktop.ini(虽然 gitignore 顺序不严格,但习惯)
  - 隐藏文件/系统文件安全:`desktop.ini` 在 Windows 上是 +h +s,但我们读/写用普通文本 API
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable


# 需要确保在 .gitignore 里的条目
REQUIRED_GITIGNORE_ENTRIES = [
    "# PandaX 运行时产物(自动管理,不要手动提交)",
    ".pandax/",
    "desktop.ini",
]

GIT_DIR_MARKERS = (".git",)  # 探测 git 仓库的标志


def is_git_repo(root: Path) -> bool:
    """检查目录是否在 git 仓库中(.git/ 存在)。"""
    return (root / ".git").exists()


def ensure_gitignore(root: Path, entries: Iterable[str] = REQUIRED_GITIGNORE_ENTRIES) -> tuple[bool, str]:
    """确保 .gitignore 包含所有必需条目;返回 (changed, message)。

    策略:
      1. 只在 git 仓库中操作(避免污染非 git 目录)
      2. 读取现有 .gitignore(若无则创建空)
      3. 逐条检查,只追加缺失的
      4. 用换行符分隔(Unix 风格 \n,git 友好)
      5. 不重排现有条目,新条目追加到末尾

    Returns:
      (changed, message):
        - changed: True = 文件被修改,False = 已正确无需改动
        - message: 人类可读的状态摘要
    """
    root = Path(root).resolve()

    # 非 git 目录直接跳过
    if not is_git_repo(root):
        return False, f"[SKIP] {root} 不是 git 仓库,跳过 .gitignore 维护"

    gitignore = root / ".gitignore"

    # 读取现有内容(若无则空)
    existing_lines: list[str] = []
    if gitignore.exists():
        try:
            text = gitignore.read_text(encoding="utf-8")
            existing_lines = text.splitlines()
        except (OSError, UnicodeDecodeError):
            existing_lines = []

    # 过滤出需要添加的条目
    existing_normalized = {line.strip() for line in existing_lines}
    to_add: list[str] = []
    for entry in entries:
        # 跳过注释(以 # 开头)和空行,只看实际规则
        # 但 entry 列表里第一项是注释,需要单独处理
        if entry.startswith("#"):
            # 注释如果已存在,不重复加
            if entry.strip() in existing_normalized:
                continue
            to_add.append(entry)
            continue
        if entry.strip() not in existing_normalized:
            to_add.append(entry)

    if not to_add:
        return False, "[OK] .gitignore 已正确包含 PandaX 条目,无需改动"

    # 确保文件以换行符结尾(避免拼接问题)
    if existing_lines and existing_lines[-1] != "":
        existing_lines.append("")

    # 拼接新条目(块头加注释说明)
    block = ["", "# PandaX 锁定的标识文件(自动管理,不要 commit)"] if not any(
        "PandaX" in line for line in existing_lines
    ) else [""]
    block.extend(to_add)

    new_content = "\n".join(existing_lines + block) + "\n"

    try:
        gitignore.write_text(new_content, encoding="utf-8")
    except OSError as e:
        return False, f"[ERR] 写 .gitignore 失败: {type(e).__name__}: {e}"

    added_names = [e for e in to_add if not e.startswith("#")]
    return True, f"[OK] .gitignore 已更新,新增: {', '.join(added_names)}"


def check_gitignore(root: Path) -> tuple[bool, list[str]]:
    """检查 .gitignore 是否包含所有必需条目(只读,不动文件)。

    Returns:
      (ok, missing):
        - ok: True = 全部存在,False = 缺失至少一项
        - missing: 缺失的条目列表
    """
    root = Path(root).resolve()
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return False, list(REQUIRED_GITIGNORE_ENTRIES)

    try:
        text = gitignore.read_text(encoding="utf-8")
        existing = {line.strip() for line in text.splitlines()}
    except (OSError, UnicodeDecodeError):
        return False, list(REQUIRED_GITIGNORE_ENTRIES)

    missing = [e for e in REQUIRED_GITIGNORE_ENTRIES
               if not e.startswith("#") and e.strip() not in existing]
    return (len(missing) == 0), missing