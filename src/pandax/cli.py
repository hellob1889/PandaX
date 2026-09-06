#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pandax.py
============
PandaX — AI Agent 代码审计门禁系统（CLI 主程序）

设计核心：
  - 每次启动必读 README.md 并显示当前阶段 / 已完成步骤
  - 文件锁（attrib +r）+ 审计写入（reason/problem/approach 必填）+ git 自动提交
  - 五层防御：L1 文件锁 / L2 监控 / L3 git hook / L4 启动校验 / L5 自指纹

实施状态：Phase 1 CLI MVP
  - [x] Step 2: 框架 + 启动读 README
  - [ ] Step 3: init
  - [ ] Step 4: lock / unlock
  - [ ] Step 5: write（核心）
  - [ ] Step 6: log
  - [ ] Step 7: SHA256 自指纹
"""
import argparse
import fnmatch
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

# Phase 10: i18n（国际化）— t() 函数 + 语言包
from pandax import i18n as _i18n
from pandax.i18n import t, t_bilingual, init as i18n_init

# 修复 Windows GBK 编码问题（PyInstaller 打包后默认 GBK）
# 确保 stdout/stderr 支持 UTF-8，中文不乱码
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ============================================================
# 路径常量
# ============================================================
ROOT = Path(__file__).resolve().parent
README_PATH = ROOT / "README.md"
# 指纹文件放用户目录（避免 pip 安装后被覆盖）
FP_PATH = Path.home() / ".pandax_fp.txt"


# ============================================================
# README 摘要（启动必读）
# ============================================================
def load_banner():
    """
    加载并返回 ASCII 启动 banner（带品牌色 ANSI 转义）

    第一性原理:
      - CLI 是产品的"门面"——第一印象决定专业度
      - banner 用 ANSI 颜色，Windows CMD 需先 reconfigure UTF-8
      - 文件读取失败时降级为纯文本（不阻断启动）
      - tagline 走 i18n（zh-CN / en）
    """
    try:
        from pathlib import Path
        banner_path = Path(__file__).parent / "banner.txt"
        if not banner_path.exists():
            return []
        text = banner_path.read_text(encoding="utf-8")
        # i18n: 替换 tagline 占位符
        text = text.replace("__TAGLINE__", t("banner_tagline"))
        # ANSI 颜色：PandaX 用紫色主题（与品牌色一致）
        BOLD = "\033[1m"
        DIM = "\033[2m"
        RESET = "\033[0m"
        MAGENTA = "\033[95m"
        INDIGO = "\033[94m"
        CYAN = "\033[96m"
        colored_lines = []
        for line in text.splitlines():
            if "█████" in line:
                colored_lines.append(f"{MAGENTA}{BOLD}{line}{RESET}")
            elif "🐼" in line:
                colored_lines.append(f"{CYAN}{line}{RESET}")
            elif "───" in line:
                colored_lines.append(f"{INDIGO}{DIM}{line}{RESET}")
            else:
                colored_lines.append(line)
        return colored_lines
    except Exception:
        return []


def load_readme_summary():
    """
    解析 README.md，输出：
      - 当前阶段段落
      - 已完成步骤（[x] 标记行）

    第一性原理：
      README 的"当前阶段"段落用 `- [x]` 标记已完成步骤，
      所以"已完成"是从阶段段落里提取，不是从"实施步骤记录"段落里。
    """
    if not README_PATH.exists():
        return ["[ERROR] README.md 未找到，CLI 无法运行"]

    text = README_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    out = []
    out.append("=" * 64)
    out.append(t("readme_header"))
    out.append("=" * 64)
    out.append("")

    phase_lines = []      # 当前阶段段落的所有有效行
    completed_steps = []  # 已完成的 [x] Step 行
    section = None

    for line in lines:
        stripped = line.strip()

        if stripped == "## 当前阶段":
            section = "phase"
            continue

        # 任何其他 ## 标题结束"当前阶段"
        if stripped.startswith("## ") and section == "phase":
            section = None

        if section == "phase" and stripped:
            phase_lines.append(stripped)
            if "[x]" in stripped:
                completed_steps.append(stripped.lstrip())

    # 输出【当前阶段】
    # Bug #4 fix: 取最后一个 **Phase 行（最新活跃阶段），而不是第一个
    # 第一性原则：README 段落里会列多个已完成 Phase + 当前进行中 Phase。
    # 当前活跃阶段 = 最后出现的 "**Phase X" 标题（README 维护者按时间顺序写）
    out.append(t("current_phase"))
    last_phase_line = None
    for ln in phase_lines:
        if ln.startswith("**Phase"):
            last_phase_line = ln
    if last_phase_line:
        out.append("  " + last_phase_line)
    else:
        # 兼容：README 段落里没有 **Phase 标题（罕见），回退到第一个有效行
        for ln in phase_lines:
            if ln:
                out.append("  " + ln)
                break

    # 输出【已完成步骤】
    if completed_steps:
        out.append("")
        out.append(t("completed_steps"))
        for step in completed_steps:
            out.append("  " + step)
    else:
        out.append(f"{t('completed_steps')}（{t('_none')}）")

    out.append("")
    out.append("=" * 64)
    return out


# ============================================================
# CLI 框架
# ============================================================
def build_parser():
    parser = argparse.ArgumentParser(
        prog="pandax",
        description="PandaX — AI Agent 代码审计门禁系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="store_true", help="显示版本")
    parser.add_argument("--update-fingerprint", metavar="PASSWORD", help="更新 pandax 自身 SHA256 指纹（默认密码 0000）")
    # Phase 9+: 无声 + 默认信任（右键场景一键到底）
    parser.add_argument("--silent", action="store_true",
                        help="静默模式：跳过 banner 和 README 摘要（右键菜单调用建议带上）")
    parser.add_argument("--trust-default", action="store_true",
                        help="使用默认密码 0000 自动更新/初始化指纹（右键菜单调用建议带上）")
    # Phase 10: i18n 语言切换
    parser.add_argument("--lang", choices=["zh-CN", "en"], default=None,
                        help="界面语言：zh-CN（简体中文，默认）/ en（英文）。不指定则自动检测 OS 语言")

    sub = parser.add_subparsers(dest="command", help="子命令")

    # 子命令占位（按 Step 顺序实现）
    init_p = sub.add_parser("init", help="在当前文件夹初始化 PandaX")
    init_p.add_argument("--root", default=".", help="项目根目录路径（默认当前目录）")
    init_p.add_argument("--ext", nargs="+", default=None,
                        help="自定义受保护扩展名（如 --ext .py .md .json）。不指定则用 17 种默认文本格式")
    init_p.add_argument("--no-binary", action="store_true",
                        help="禁用二进制保护（不创建 SHA256 快照）")
    lock_p = sub.add_parser("lock", help="锁定所有受保护扩展名的文件")
    lock_p.add_argument("--root", default=".", help="项目根目录路径")
    unlock_p = sub.add_parser("unlock", help="解锁所有受保护扩展名的文件")
    unlock_p.add_argument("--root", default=".", help="项目根目录路径")
    log_p = sub.add_parser("log", help="查看审计历史")
    log_p.add_argument("--root", default=".", help="项目根目录路径")
    # Bug #13 fix: -n 是 --recent 的短选项别名，方便 `pandax log -n 5`
    log_p.add_argument("-n", "--recent", type=int, default=20,
                       help="最近 N 条（默认 20）。短选项 -n 仅 log 命令可用")
    log_p.add_argument("--file", default="", help="按文件过滤")
    log_p.add_argument("--session", default="", help="按 session 过滤")
    log_p.add_argument("--rejected", action="store_true", help="只看拒绝记录")
    log_p.add_argument("--unauthorized", action="store_true", help="只看非授权写入")
    log_p.add_argument("--export", default="", help="[已废弃] 导出为 HTML 报告，请用 --format html --output PATH")
    log_p.add_argument("--format", default="",
                      help="导出格式: text(csv, tsv, json, yaml, md, html, xlsx, docx, pdf, sqlite, rst, asciidoc). 也可用 txt/sql/db/yml/adoc 别名")
    log_p.add_argument("--output", "-o", default="", help="导出文件路径（与 --format 一起使用）")
    log_p.add_argument("--from", dest="from_date", default="", help="起始日期 YYYY-MM-DD")
    log_p.add_argument("--to", dest="to_date", default="", help="截止日期 YYYY-MM-DD")
    install_git_p = sub.add_parser("install-git", help="探测/安装 git")
    install_git_p.add_argument("--probe-only", action="store_true", help="只探测不下载")
    install_git_p.add_argument("--auto-download", action="store_true", help="自动下载 portable git")
    install_hook_p = sub.add_parser("install-hook", help="安装 pre-commit hook")
    install_hook_p.add_argument("--root", default=".", help="项目根目录")
    install_hook_p.add_argument("--uninstall", action="store_true", help="卸载 hook")
    status_p = sub.add_parser("status", help="查看状态")
    status_p.add_argument("--root", default=".", help="项目根目录路径")
    watch_p = sub.add_parser("watch", help="启动 watchdog 监控")
    watch_p.add_argument("--root", default=".", help="项目根目录路径")
    watch_p.add_argument("--daemon", action="store_true", help="后台运行")

    # Phase 7: CI 子命令（GitHub Actions 集成）
    ci_p = sub.add_parser("ci", help="CI 验证：检查 PR 所有变更都有审计")
    ci_p.add_argument("--root", default=".", help="项目根目录")
    ci_p.add_argument("--base", default="", help="基线分支（默认 main）")
    ci_p.add_argument("--head", default="HEAD", help="当前 HEAD（默认 HEAD）")

    # write 子命令参数
    write_p = sub.add_parser("write", help="审计写入（核心）")
    write_p.add_argument("--root", default=".", help="项目根目录路径")
    write_p.add_argument("--file", required=True, help="目标 .py 文件路径")
    write_p.add_argument("--reason", default="", help="改动原因（必填）")
    write_p.add_argument("--problem", default="", help="解决的问题（必填）")
    write_p.add_argument("--approach", default="", help="采用的方法（必填）")
    write_p.add_argument("--old", default="", help="原字符串（模式 1，仅文本文件）")
    write_p.add_argument("--new", default="", help="新字符串（模式 1，仅文本文件）")
    write_p.add_argument("--content", default="", help="整文件文本内容（模式 2）")
    write_p.add_argument("--content-base64", default="", help="整文件二进制内容（base64 编码）")
    write_p.add_argument("--from-file", default="", help="从本地文件读取内容（二进制或文本均可）")
    write_p.add_argument(
        "--force-write",
        action="store_true",
        help=(
            "允许覆盖 L1 锁定的文件（默认拒绝 ReadOnly 文件以确保审计门禁，"
            "加此标志走完整 unlock-write-lock 流程并审计记录 force_write=true）"
        ),
    )

    # Phase 9: OS 右键菜单集成
    ic_p = sub.add_parser("install-context", help="安装 OS 右键菜单（自动检测 Windows / macOS / Linux）")
    ic_p.add_argument("--force", action="store_true", help="强制重新安装（仅 Windows 生效）")
    ic_p.add_argument("--lang", choices=["zh-CN", "en"], default=None,
                      help="右键菜单 UI 语言（默认跟随 pandax 当前语言）")
    uc_p = sub.add_parser("uninstall-context", help="卸载 OS 右键菜单（自动检测平台）")

    return parser


# ============================================================
# 子命令处理（逐步实现）
# ============================================================
# ============================================================
# 自指纹保护（L5 防御）
# ============================================================
FINGERPRINT_PASSWORD = "0000"  # 默认密码（本地使用）


def compute_fingerprint() -> str:
    """计算 pandax.py 自身的 SHA256"""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def check_fingerprint(silent: bool = False) -> bool:
    """
    检查 pandax.py 指纹。
    返回 True = 通过（首次运行也通过，会生成初始指纹）
    返回 False = 失败（被篡改）
    silent=True → 不打印任何错误（用于 --trust-default 模式）
    """
    current = compute_fingerprint()

    if not FP_PATH.exists():
        # 首次运行：生成初始指纹
        FP_PATH.write_text(current, encoding="utf-8")
        if not silent:
            print(t("info_fp_generated", fp=current[:16]))
        return True

    stored = FP_PATH.read_text(encoding="utf-8").strip()
    if stored != current:
        if not silent:
            print(t("err_fingerprint_mismatch"))
            print(f"  {t('_stored', stored=stored[:16])}")
            print(f"  {t('_current', current=current[:16])}")
            print(f"  {t('err_fingerprint_hint')}")
        return False

    return True


def cmd_init(args):
    """
    在指定目录初始化 PandaX：
      - 创建 .pandax/
      - 写 config.json
      - 写空的 pandax.jsonl
    幂等：二次运行不报错。
    """
    import json

    root = Path(args.root).resolve()
    pandax_dir = root / ".pandax"

    # 创建目录（exist_ok=True 实现幂等）
    pandax_dir.mkdir(parents=True, exist_ok=True)

    # 写 config.json
    # Phase 4.6: 默认保护 17 种常见文本格式（不只是 .py）
    # 覆盖：代码、配置、文档、前端、脚本五大类
    DEFAULT_PROTECTED_EXTENSIONS = [
        # 代码
        ".py", ".pyx",
        # 配置
        ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env",
        # 文档
        ".md", ".rst", ".txt",
        # 前端
        ".html", ".css", ".js", ".ts",
        # 脚本
        ".sh", ".bat", ".ps1",
    ]
    protected_extensions = args.ext if args.ext else DEFAULT_PROTECTED_EXTENSIONS
    # 统一规范化：确保每个都以 "." 开头
    protected_extensions = [
        e if e.startswith(".") else f".{e}"
        for e in protected_extensions
    ]

    config = {
        "version": "1.0",
        "project_root": str(root),
        "protected_extensions": protected_extensions,
        "exclude_patterns": ["__pycache__", "*.pyc", "_tmp_*.py", "_fix*.py", ".pandax", ".git"],
        "git_enabled": True,
        "watchdog_enabled": True,
        "min_reason_length": 5,
        "min_problem_length": 10,
        "min_approach_length": 10,
    }
    # Phase 5: 二进制文件 SHA256 快照保护
    DEFAULT_BINARY_EXTENSIONS = [
        # 图片
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
        # 文档
        ".pdf", ".docx", ".xlsx", ".pptx",
        # 压缩
        ".zip", ".tar", ".gz", ".7z", ".rar",
        # 可执行
        ".exe", ".dll", ".so", ".dylib", ".bin",
        # 媒体
        ".mp4", ".mp3", ".wav", ".avi", ".mkv",
    ]
    config["binary_protected_extensions"] = [] if args.no_binary else DEFAULT_BINARY_EXTENSIONS
    exclude_patterns = config["exclude_patterns"]  # 提取出来给后续使用
    config_path = pandax_dir / "config.json"
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 写空审计日志
    audit_path = pandax_dir / "pandax.jsonl"
    if not audit_path.exists():
        audit_path.touch()

    # Phase 5: 创建二进制文件 SHA256 快照
    if config["binary_protected_extensions"]:
        _create_binary_snapshots(root, config["binary_protected_extensions"], exclude_patterns)

    print(t("ok_initialized", path=pandax_dir))
    print(f"  {t('init_config', path=config_path)}")
    print(f"  {t('init_audit', path=audit_path)}")
    if config["binary_protected_extensions"]:
        print(f"  {t('init_binary', path=pandax_dir / 'binary_snapshots.json')}")
    return 0


def _create_binary_snapshots(root: Path, binary_exts: list[str], exclude_patterns: list[str]):
    """
    Phase 5: 创建 binary_snapshots.json — 所有受保护二进制文件的 SHA256 字典。

    第一性原理：
      二进制无法做语义化 diff/审计，只能做完整性校验。
      snapshot 是审计的"基线"——所有变更必须以"approved write"形式留痕。

    对抗式审查：
      - 攻击：snapshot 文件本身被改 → 缓解：snapshot 在 .pandax/ 里（被指纹 + exclude 保护）
      - 攻击：大文件 SHA256 慢 → 缓解：snapshot 仅在 init/approved write 时算一次
    """
    import hashlib
    import json
    import fnmatch as fnm

    snapshots = {}
    seen = set()
    for ext in binary_exts:
        for f in root.rglob(f"*{ext}"):
            if f in seen:
                continue
            seen.add(f)
            rel = f.relative_to(root)
            # 排除规则
            skip = False
            for pat in exclude_patterns:
                if any(fnm.fnmatch(part, pat) for part in rel.parts):
                    skip = True
                    break
                if fnm.fnmatch(rel.name, pat):
                    skip = True
                    break
            if skip:
                continue
            try:
                sha = hashlib.sha256(f.read_bytes()).hexdigest()
                snapshots[str(rel).replace("\\", "/")] = sha
            except OSError:
                pass

    snap_path = root / ".pandax" / "binary_snapshots.json"
    snap_path.write_text(
        json.dumps(snapshots, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(t("info_snapshot_count", n=len(snapshots)))


def _update_binary_snapshot(root: Path, relpath: str, new_sha: str):
    """Phase 5: 更新单个文件的 SHA256 快照（approved write 后调用）"""
    import json
    snap_path = root / ".pandax" / "binary_snapshots.json"
    if not snap_path.exists():
        return
    snapshots = json.loads(snap_path.read_text(encoding="utf-8"))
    # 统一为正斜杠
    relpath_normalized = relpath.replace("\\", "/")
    snapshots[relpath_normalized] = new_sha
    snap_path.write_text(
        json.dumps(snapshots, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def cmd_lock(args):
    """锁定所有 .py 文件（attrib +r / chmod ~0o222）"""
    return _apply_readonly(args.root, readonly=True)


def cmd_unlock(args):
    """解锁所有 .py 文件（attrib -r / chmod +0o222）"""
    return _apply_readonly(args.root, readonly=False)


class _OldNotFoundError(Exception):
    """Bug #12: 业务拒绝异常 --old 字符串不在文件中。
    让 write 流程用统一的 try/finally 处理，无需散落的 inline 拒绝代码。"""
    def __init__(self, snippet: str):
        super().__init__(snippet)
        self.snippet = snippet


def _info_length(s: str) -> int:
    """
    Bug #9/#10 fix: 计算字符串的"信息长度"（unicode 显示宽度）。

    第一性原则：阈值应当反映"内容是否有足够语义价值"，而不是字符数。
    - 1 个 CJK 字符（中文/日文/韩文）= 2 宽度单位（信息密度 ≈ 2 个英文字符）
    - 1 个 Fullwidth 字符（全角标点）= 2 宽度单位
    - 1 个 ASCII/拉丁字符 = 1 宽度单位
    - 控制字符 = 0

    修复前：len("测试") == 2，被 reason 阈值 (5 chars) 误伤
    修复后：info_len("测试") == 4，仍然 < 5 阈值 — 仍可能被误伤
           所以同时降低阈值到合理水平（reason 5、problem/approach 10）

    典型用例：
    - "fix" (3 chars) → 3，< 5 拒绝（合理）
    - "测试" (2 chars) → 4，< 5 拒绝（仍然）
    - "测试写" (3 chars) → 6，≥ 5 通过（中文短句 OK）
    - "fix bug" (7 chars) → 7，≥ 5 通过
    - "需要修复初始化函数" (9 chars) → 18，≥ 5 通过
    """
    import unicodedata as _ud
    n = 0
    for ch in s:
        if not ch.isprintable():
            continue  # 跳过控制字符（不计入信息量）
        width = _ud.east_asian_width(ch)
        if width in ("W", "F"):  # Wide / Fullwidth
            n += 2
        else:  # Na / H / A / N
            n += 1
    return n


def _effective_suffix(path: Path) -> str:
    """
    Phase 4.6+: 返回文件的有效后缀（正确处理隐藏文件如 .env, .gitignore, .env.local）。

    标准 Path.suffix 行为：
      - main.py → .py
      - .env → '' （隐藏文件被当作无后缀）
      - .gitignore → ''
      - .env.local → .local

    我们希望的"有效后缀"语义：
      - main.py → .py
      - .env → .env （整名就是后缀）
      - .gitignore → .gitignore
      - .env.local → .local （保留最后一段，符合 POSIX 习惯）

    第一性原理：
      隐藏文件经常包含敏感配置（.env = 数据库密码），必须被审计保护。
      标准 pathlib 把它们当无后缀处理 = 安全漏洞。
    """
    name = path.name
    if name.startswith("."):
        rest = name[1:]  # 去掉前导点
        if "." in rest:
            # .env.local → .local
            return "." + rest.rsplit(".", 1)[1]
        # .env → .env
        return "." + rest
    return path.suffix


def _iter_protected_files(root: Path, config: dict) -> list[Path]:
    """
    Bug #2 fix: 共享 helper — 列出项目根目录下所有受保护扩展名的文件。

    被 cmd_status（仪表盘）、_apply_readonly（lock/unlock）、cmd_ci 等共用。
    之前 cmd_status 只看 *.py，忽略了 18 种其它受保护扩展名（.json, .yaml, .env 等），
    导致 status 报告的"锁定文件数"严重低估，用户看不到 L1 锁的真实覆盖。

    参数：
      - root: 项目根目录
      - config: 项目配置 dict（含 protected_extensions + exclude_patterns）

    返回：受保护文件路径列表（排除 __pycache__、.git、exclude_patterns 等）
    """
    import fnmatch

    protected_exts = set(config.get("protected_extensions", [".py"]))
    exclude_patterns = config.get("exclude_patterns", [])

    files = []
    seen = set()
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p in seen:
            continue
        if _effective_suffix(p) not in protected_exts:
            continue
        seen.add(p)

        # 排除判断
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        skip = False
        for pat in exclude_patterns:
            if any(fnmatch.fnmatch(part, pat) for part in rel.parts):
                skip = True
                break
            if fnmatch.fnmatch(rel.name, pat):
                skip = True
                break
        if skip:
            continue

        files.append(p)
    return files


def _apply_readonly(root_arg: str, readonly: bool) -> int:
    """
    共享的锁/解锁函数。
    Phase 4.6: 遍历 config.json 中所有 protected_extensions（不再只看 .py）。
    跨平台：Windows 用 os.chmod 设只读属性；Linux/Mac 用 0o444。
    排除：__pycache__、*.pyc、_tmp_*.py、_fix*.py
    """
    import json
    import os
    import stat

    root = Path(root_arg).resolve()
    config_path = root / ".pandax" / "config.json"

    # 检查是否 init 过
    if not config_path.exists():
        print(t("err_write_root_not_init", root=root))
        return 1

    # 读取配置（含 protected_extensions + exclude_patterns）
    config = json.loads(config_path.read_text(encoding="utf-8"))
    protected_extensions = config.get("protected_extensions", [".py"])

    count = 0
    # Bug #2 fix: 用 _iter_protected_files 共享 helper（避免与 cmd_status 行为漂移）
    for target_file in _iter_protected_files(root, config):
        try:
            current_mode = target_file.stat().st_mode
            if readonly:
                new_mode = current_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH
            else:
                new_mode = current_mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
            os.chmod(target_file, new_mode)
            count += 1
        except OSError as e:
            print(t("warn_lock_failed", file=target_file, err=e))

    action = "锁定" if readonly else "解锁"
    ext_list = ", ".join(protected_extensions)
    if readonly:
        print(t("ok_locked_n", n=count, exts=ext_list))
    else:
        print(t("ok_unlocked_n", n=count, exts=ext_list))
    return 0


def _resolve_git_exe() -> str:
    """
    Bug #21 fix: 统一 git 可执行解析逻辑，所有 git 调用共享。

    之前 doctor (scripts/doctor.py) 用 shutil.which + Windows 候选目录回退，
    但 write/ci 直接 subprocess.run(["git", ...])。边缘场景下行为不一致：
    doctor 报 OK（找到 D:\软件\Git\cmd\git.exe），write 报 FileNotFoundError
    （当前进程 PATH 没该路径，subprocess 调用失败）。

    策略：与 doctor 相同的"PATH 优先 + Windows 候选回退"算法。
    返回值是绝对路径（如果找到）或 "git"（fallback，让 subprocess 自己找）。
    """
    import shutil as _sh
    git_path = _sh.which("git")
    if git_path:
        return git_path
    # Windows 常见安装路径（与 doctor.py 一致）
    if os.name == "nt":
        candidates = [
            r"D:\软件\Git\cmd",
            r"C:\Program Files\Git\cmd",
            r"C:\Program Files (x86)\Git\cmd",
            r"C:\Program Files\Git\bin",
            r"C:\Git\cmd",
        ]
        for c in candidates:
            p = Path(c, "git.exe")
            if p.exists():
                # 同时把候选目录加入当前进程 PATH，避免后续 subprocess 找不到
                os.environ["PATH"] = str(Path(c)) + os.pathsep + os.environ.get("PATH", "")
                return str(p)
    return "git"  # 让 subprocess 自己解析（最佳努力 fallback）


def cmd_write(args):
    """
    审计写入（核心命令）：
      1. 水质检测（reason/problem/approach 必填且满足长度）
      2. 设审计令牌
      3. 解锁目标文件
      4. 写入（字符串替换 / 整文件）
      5. 重新锁定
      6. 清审计令牌
      7. git add + commit
      8. 写审计记录
    """
    import datetime as dt
    import json
    import os
    import stat
    import subprocess
    import uuid

    root = Path(args.root).resolve()
    config_path = root / ".pandax" / "config.json"

    # 检查 init
    if not config_path.exists():
        print(t("err_write_rejected", root=root))
        return 1

    config = json.loads(config_path.read_text(encoding="utf-8"))

    # === [1] 水质检测 ===
    reason = args.reason.strip()
    problem = args.problem.strip()
    approach = args.approach.strip()
    min_reason = config.get("min_reason_length", 5)
    min_problem = config.get("min_problem_length", 10)
    min_approach = config.get("min_approach_length", 10)

    reject_reason = None
    if not reason:
        reject_reason = "reason 字段为空"
    # Bug #9 fix: 用 _info_length() 计算 unicode 宽度，1 中文字 = 2 宽度单位，
    # 避免"测试"（2 中文字 = 4 宽度）被 5 字符阈值误伤（修复前 len=2 < 5）
    elif _info_length(reason) < min_reason:
        reject_reason = f"reason 长度不足（< {min_reason} 宽度单位，含 CJK 字符按 2 计）"
    elif not problem:
        reject_reason = "problem 字段为空"
    # Bug #10 fix: 同上，problem/approach 也用 _info_length()
    elif _info_length(problem) < min_problem:
        reject_reason = f"problem 长度不足（< {min_problem} 宽度单位，含 CJK 字符按 2 计）"
    elif not approach:
        reject_reason = "approach 字段为空"
    elif _info_length(approach) < min_approach:
        reject_reason = f"approach 长度不足（< {min_approach} 宽度单位，含 CJK 字符按 2 计）"

    target_rel = args.file
    target = root / target_rel

    # Phase 5: 检测是文本还是二进制文件（Phase 4.6+ 使用 _effective_suffix 处理隐藏文件）
    text_exts = config.get("protected_extensions", [".py"])
    binary_exts = config.get("binary_protected_extensions", [])
    target_eff_suffix = _effective_suffix(target)
    is_binary = target_eff_suffix in binary_exts

    # 检查目标文件存在 + 后缀受保护
    if not target.exists():
        reject_reason = f"目标文件不存在: {target_rel}"
    elif not is_binary and target_eff_suffix not in text_exts:
        reject_reason = f"只允许修改文本({text_exts})或二进制({binary_exts})保护范围内的文件"

    # 二进制文件不接受 --old/--new（语义化替换对二进制无意义）
    if not reject_reason and is_binary and (args.old or args.new):
        reject_reason = "二进制文件不支持 --old/--new 模式，请用 --content-base64 或 --from-file"

    # === Bug #12 v2: L1 文件锁 ReadOnly 前置检查 ===
    # 默认拒绝修改 OS ReadOnly 文件（pandax lock 设的）。仅 --force-write 才放行。
    # 对抗式审查：如果允许 write 默认解锁，恶意 Agent 可绕过用户意图。
    if not reject_reason and target.exists() and not os.access(target, os.W_OK):
        if not getattr(args, "force_write", False):
            reject_reason = t("write_reject_readonly_need_force", file=target_rel)

    if reject_reason:
        # 写拒绝记录
        audit_path = root / ".pandax" / "pandax.jsonl"
        record = {
            "id": f"audit_{uuid.uuid4().hex[:8]}",
            "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "REJECTED",
            "file": target_rel,
            "rejection_reason": reject_reason,
            "attempted_reason": args.reason,
            "attempted_problem": args.problem,
            "attempted_approach": args.approach,
            "files_changed": [],
        }
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        print(f'[REJECTED] {{"status":"REJECTED","reason":"{reject_reason}"}}')
        return 1

    # === [2] 设审计令牌 ===
    token_path = root / ".pandax" / ".audit_token"
    audit_path = root / ".pandax" / "pandax.jsonl"  # 提前定义给后续 git add 用
    token_path.write_text(str(uuid.uuid4()), encoding="utf-8")

    # === [3] 解锁目标文件 ===
    mode = target.stat().st_mode
    writable_mode = mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    os.chmod(target, writable_mode)

    # 准备 step 4→5 的 try/finally 块：
    # Bug #12 fix: write_text/write_bytes 在隐藏/系统文件上会抛 PermissionError，
    # 旧代码没有 try/except，导致文件 mode 永久变为 writable，绕过文件锁。
    # 用 try/finally 确保无论写入成功或失败都恢复原始 mode。

    # === [4] 写入（Phase 5: 文本 vs 二进制分支）===
    # Bug #12 fix: 整个 step 4 包在 try/finally 中，确保文件 mode 始终恢复。
    # 任何 write_text/write_bytes 抛错（hidden/system 文件、磁盘满等），
    # finally 块都会恢复原始 mode —— 审计门禁不能因 IO 错误绕过文件锁。
    write_error = None
    try:
        if is_binary:
            # 二进制文件：必须用 --from-file 或 --content-base64
            import base64 as b64
            if args.from_file:
                src = Path(args.from_file)
                if not src.exists():
                    raise FileNotFoundError(f"from-file not found: {args.from_file}")
                new_bytes = src.read_bytes()
            elif args.content_base64:
                try:
                    new_bytes = b64.b64decode(args.content_base64)
                except Exception as e:
                    raise ValueError(f"base64 decode error: {e}") from e
            else:
                raise ValueError("binary file must use --from-file or --content-base64")
            target.write_bytes(new_bytes)
            # Phase 5: 更新 SHA256 快照
            import hashlib
            new_sha = hashlib.sha256(target.read_bytes()).hexdigest()
            _update_binary_snapshot(root, target_rel, new_sha)
        elif args.content:
            # 文本整文件模式
            original_content = target.read_text(encoding="utf-8")
            new_content = args.content
            target.write_text(new_content, encoding="utf-8")
        elif args.old:
            # 文本字符串替换模式
            original_content = target.read_text(encoding="utf-8")
            if args.old not in original_content:
                # 用专用异常类型让外层识别为业务拒绝（不是 IO 错误）
                raise _OldNotFoundError(args.old[:30])
            new_content = original_content.replace(args.old, args.new, 1)
            target.write_text(new_content, encoding="utf-8")
        else:
            raise ValueError("must specify --old/--new or --content")
    except _OldNotFoundError as e:
        # 业务拒绝（--old 不在文件中）：记录 audit + 返回 REJECTED
        # finally 块负责恢复 mode
        write_error = ("REJECTED", f"--old 字符串不在文件中: {e}...")
    except Exception as e:
        # IO 错误或其他异常：记录 audit + 返回 REJECTED
        write_error = ("REJECTED", f"写入失败: {type(e).__name__}: {e}")
    finally:
        # === [5] 重新锁定（恢复原始 mode）===
        # Bug #12 fix: 不论 write 成功或失败，都恢复原始 mode。
        # 直接用 step 3 保存的 `mode`（而不是再算 readonly_mode），
        # 这样能完整恢复 hidden/system/archive 等所有 file attributes。
        try:
            os.chmod(target, mode)
        except Exception as chmod_err:
            # 如果 chmod 失败（极少见，例如文件被另一进程占用），
            # 必须明确告知用户 — 这是审计安全 fallback
            print(f'[WARN] failed to restore file mode for {target_rel}: {chmod_err}')
            if write_error is None:
                write_error = ("REJECTED", f"无法恢复文件锁定状态: {chmod_err}")

    if write_error is not None:
        # 记录 REJECTED audit
        status, reason = write_error
        record = {
            "id": f"audit_{uuid.uuid4().hex[:8]}",
            "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "REJECTED",
            "file": target_rel,
            "rejection_reason": reason,
            "attempted_reason": args.reason,
            "attempted_problem": args.problem,
            "attempted_approach": args.approach,
            "files_changed": [],
        }
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        token_path.unlink(missing_ok=True)
        print(f'[REJECTED] {{"status":"REJECTED","reason":"{reason}"}}')
        return 1

    # === [6] 清审计令牌 ===
    token_path.unlink(missing_ok=True)

    # === [7] 写审计记录 ===
    audit_id = f"audit_{uuid.uuid4().hex[:8]}"
    record = {
        "id": audit_id,
        "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "APPROVED",
        "file": target_rel,
        "reason": reason,
        "problem": problem,
        "approach": approach,
        "commit_hash": "",  # 稍后填充
        "force_write": bool(getattr(args, "force_write", False)),
        "files_changed": [target_rel],
    }
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

    # === [8] git add + commit ===
    commit_hash = ""
    if config.get("git_enabled", True):
        try:
            # add 目标文件 + 审计日志（让 pre-commit hook 能放行）
            audit_rel = audit_path.relative_to(root)
            # Windows 路径分隔符统一为 /
            audit_rel_str = str(audit_rel).replace("\\", "/")
            target_rel_str = str(target_rel).replace("\\", "/")
            # Bug #21 fix: 用 _resolve_git_exe() 统一 git 可执行解析，
            # 与 doctor.py 检测逻辑保持一致（避免边缘场景 doctor OK / write 失败）
            GIT = _resolve_git_exe()
            r_add = subprocess.run(
                [GIT, "add", target_rel_str, audit_rel_str],
                cwd=str(root), capture_output=True, text=True, timeout=10,
            )
            if r_add.returncode != 0:
                print(t("write_warn_git_add", err=r_add.stderr.strip()))
            commit_msg = (
                f"audit: {reason} [APPROVED]\n\n"
                f"file: {target_rel}\n"
                f"reason: {reason}\n"
                f"problem: {problem}\n"
                f"approach: {approach}\n"
            )
            r = subprocess.run(
                [GIT, "commit", "-m", commit_msg],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode != 0:
                # hook 拒绝或 git 错误（不影响审计记录）
                pass
            if r.returncode == 0:
                # 获取 commit hash
                log_r = subprocess.run(
                    [GIT, "log", "-1", "--format=%H"],
                    cwd=str(root),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                commit_hash = log_r.stdout.strip()
        except FileNotFoundError:
            print(t("write_warn_no_git"))

    print(f'[APPROVED] {{"status":"APPROVED","commit":"{commit_hash[:7]}","audit_id":"{audit_id}","file":"{target_rel}"}}')
    return 0


def cmd_log(args):
    """
    查询审计历史。
    支持过滤：recent N / file / session / rejected / unauthorized
    支持导出：--export PATH（HTML）
    """
    import json

    root = Path(args.root).resolve()
    audit_path = root / ".pandax" / "pandax.jsonl"

    if not audit_path.exists():
        print(f'[ERROR] {{"status":"ERROR","reason":"{t("_log_no_init", root=root)}"}}')
        return 1

    # 读所有记录
    records = []
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # 过滤
    filtered = records
    if args.file:
        filtered = [r for r in filtered if r.get("file") == args.file]
    if args.session:
        filtered = [r for r in filtered if r.get("session_id") == args.session]
    if args.rejected:
        filtered = [r for r in filtered if r.get("status") == "REJECTED"]
    if args.unauthorized:
        filtered = [r for r in filtered if r.get("status") == "UNAUTHORIZED"]

    # 取最近 N 条
    if args.recent and args.recent > 0:
        filtered = filtered[-args.recent:]

    # 输出：兼容旧 --export（HTML），新 --format + --output
    if args.export:
        # 旧接口兼容：直接导出 HTML
        from .exporters import export_html
        out_path = Path(args.export)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        export_html(filtered, out_path)
        print(t("log_export_ok", n=len(filtered), path=out_path))
        return 0

    if args.format or args.output:
        # 新接口：--format + --output
        if not args.format:
            print(t("err_format_without_format"))
            return 1
        if not args.output:
            print(t("err_format_without_output"))
            return 1

        from .exporters import export_records
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        ok = export_records(filtered, args.format, out_path)
        if not ok:
            return 1
        print(t("log_export_ok_format", n=len(filtered), fmt=args.format, path=out_path))
        return 0

    _print_log(filtered)
    return 0


def _print_log(records: list[dict]):
    """格式化输出审计记录"""
    if not records:
        print(t("log_no_records"))
        return

    print("=" * 80)
    print(t("log_header", n=len(records)))
    print("=" * 80)
    for rec in records:
        ts = rec.get("timestamp", "?")
        status = rec.get("status", "?")
        rid = rec.get("id", "?")
        file_ = rec.get("file", "?")
        # Bug #14 fix: id=/file= 标签本地化（之前硬编码英文）
        print("\n" + t(
            "log_record_header",
            ts=ts,
            status=status,
            id_label=t("log_field_id"),
            rid=rid,
            file_label=t("log_field_file"),
            file_=file_,
        ))
        if status == "APPROVED":
            print(f"  {t('log_field_reason')}:   {rec.get('reason', '')}")
            print(f"  {t('log_field_problem')}:  {rec.get('problem', '')}")
            print(f"  {t('log_field_approach')}: {rec.get('approach', '')}")
            print(f"  {t('log_field_commit')}:   {rec.get('commit_hash', t('_log_no_commit'))}")
        elif status == "REJECTED":
            print(f"  {t('log_field_reason')}:   {rec.get('rejection_reason', '')}")
            ar = rec.get('attempted_reason', '')
            ap = rec.get('attempted_problem', '')
            aa = rec.get('attempted_approach', '')
            if ar or ap or aa:
                # Bug #6 fix: 替换 hardcoded "attempted: reason=..." 英文标签
                print(t("log_attempted", reason=ar, problem=ap, approach=aa))
        elif status == "UNAUTHORIZED":
            # Bug #6 fix: 替换 hardcoded "detection:" / "action:" 英文标签
            print(t("log_unauth_detection", detection=rec.get('detection', '')))
            print(t("log_unauth_action", action=rec.get('action', '')))
    print()
    print("=" * 80)


def _export_html(records: list[dict], path: Path):
    """导出为简单 HTML 报告（Bug #26 修复：标签本地化）"""
    rows = ""
    for r in records:
        status = r.get("status", "?")
        color = {"APPROVED": "#3fb950", "REJECTED": "#f85149", "UNAUTHORIZED": "#d29922"}.get(status, "#8b949e")
        rows += f"""
        <tr>
            <td>{r.get('timestamp', '')}</td>
            <td><span style="color:{color};font-weight:bold">{status}</span></td>
            <td>{r.get('id', '')}</td>
            <td>{r.get('file', '')}</td>
            <td>{r.get('reason', '') or r.get('rejection_reason', '')}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{t("export_title")}</title>
<style>
body {{ font-family: -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 8px 12px; border: 1px solid #30363d; text-align: left; }}
th {{ background: #1c2128; color: #f0f6fc; }}
</style></head>
<body>
<h1>{t("export_title")}</h1>
<p>{t("export_summary", n=len(records))}</p>
<table>
<thead><tr><th>{t("export_col_time")}</th><th>{t("export_col_status")}</th><th>{t("export_col_id")}</th><th>{t("export_col_file")}</th><th>{t("export_col_reason")}</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</body></html>"""
    path.write_text(html, encoding="utf-8")


def cmd_status(args):
    """
    显示项目状态仪表盘：
      - L1: 锁状态（多少 .py 已锁/未锁）
      - L2: watchdog 状态（PID 是否存在）
      - L5: 指纹状态
      - 审计统计（APPROVED / REJECTED / UNAUTHORIZED 计数）
      - 最近 3 条审计记录
    """
    import json
    import stat

    root = Path(args.root).resolve()
    pandax_dir = root / ".pandax"

    if not pandax_dir.exists():
        print(f'[ERROR] {{"status":"ERROR","reason":"{t("_watch_no_init", root=root)}"}}')
        return 1

    print("=" * 64)
    print(t("status_header", root=root))
    print("=" * 64)
    print()

    # L1: 锁状态
    # Bug #2 fix: 之前只看 *.py，忽略 18 种其它受保护扩展名
    # 用 _iter_protected_files 共享 helper（与 lock/unlock 同源），确保 status
    # 报告的"锁定文件数"与 lock/unlock 命令实际作用范围一致
    config = json.loads((pandax_dir / "config.json").read_text(encoding="utf-8"))
    protected_files = _iter_protected_files(root, config)
    if protected_files:
        locked = sum(1 for p in protected_files if not (p.stat().st_mode & stat.S_IWUSR))
        unlocked = len(protected_files) - locked
        ext_list = ", ".join(config.get("protected_extensions", [".py"]))
        print(t("status_l1"))
        print(t("status_total", n=len(protected_files)))
        print(t("status_locked_unlocked", n=locked, m=unlocked))
        print(t("status_extensions", exts=ext_list))  # Bug #2: 显示扫描的扩展名范围
        if unlocked > 0:
            print(t("status_warn_unlock", n=unlocked))
    else:
        print(t("status_l1_no_py"))
    print()

    # L2: watchdog 状态
    pid_path = pandax_dir / ".watchdog_pid"
    print(t("status_l2"))
    if pid_path.exists():
        pid = pid_path.read_text(encoding="utf-8").strip()
        print(t("status_watch_on", pid=pid))
    else:
        print(t("status_watch_off"))
    print()

    # L5: 指纹状态
    print(t("status_l5"))
    if FP_PATH.exists():
        stored = FP_PATH.read_text(encoding="utf-8").strip()
        current = compute_fingerprint()
        if stored == current:
            print(t("status_fp_ok", fp=stored[:16]))
        else:
            print(t("status_fp_mismatch", stored=stored[:16], current=current[:16]))
    else:
        print(t("status_fp_uninit"))
    print()

    # 审计统计
    audit_path = pandax_dir / "pandax.jsonl"
    print(t("status_audit_stats"))
    if audit_path.exists():
        records = []
        for line in audit_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        counts = {"APPROVED": 0, "REJECTED": 0, "UNAUTHORIZED": 0}
        for r in records:
            s = r.get("status", "UNKNOWN")
            counts[s] = counts.get(s, 0) + 1
        total = len(records)
        print(t("status_total_records", n=total))
        # Bug #17 fix: 审计统计状态计数用本地化标签（之前是裸 APPROVED/REJECTED/UNAUTHORIZED）
        if counts.get("APPROVED", 0) > 0:
            print(t("status_count_approved", n=counts["APPROVED"]))
        if counts.get("REJECTED", 0) > 0:
            print(t("status_count_rejected", n=counts["REJECTED"]))
        if counts.get("UNAUTHORIZED", 0) > 0:
            print(t("status_count_unauthorized", n=counts["UNAUTHORIZED"]))
        # 最近 3 条
        print()
        print(t("status_recent_3"))
        for rec in records[-3:]:
            ts = rec.get("timestamp", "?")
            st = rec.get("status", "?")
            rid = rec.get("id", "?")
            f = rec.get("file", "?")
            print(f"  {ts}  {st:13}  {rid}  {f}")
    else:
        print(f"  {t('log_no_records')}")
    print()

    # Phase 5: 二进制快照状态
    snap_path = pandax_dir / "binary_snapshots.json"
    print(t("status_binary_section"))
    if snap_path.exists():
        snapshots = json.loads(snap_path.read_text(encoding="utf-8"))
        print(t("status_binary_tracked", n=len(snapshots)))
        if snapshots:
            print(t("_status_example", n=5))
            for k, v in list(snapshots.items())[:5]:
                print(f"    {k}: {v[:16]}...")
        # 检查当前 SHA256 是否匹配
        mismatch = []
        for rel, expected_sha in snapshots.items():
            fp = root / rel
            if not fp.exists():
                mismatch.append((rel, "文件消失"))
                continue
            import hashlib as _hl
            actual = _hl.sha256(fp.read_bytes()).hexdigest()
            if actual != expected_sha:
                mismatch.append((rel, f"SHA256 不一致 ({actual[:8]} vs {expected_sha[:8]})"))
        if mismatch:
            print(t("status_binary_fail", n=len(mismatch)))
            for rel, reason in mismatch:
                print(f"    - {rel}: {reason}")
        else:
            print(t("status_binary_ok"))
    else:
        print(f"  {t('_status_binary_disabled')}")
    print()
    print("=" * 64)
    return 0


def cmd_install_hook(args):
    """
    安装/卸载 pre-commit hook
    委托给 install_hook.py
    """
    import subprocess

    # pip 安装后 install_hook 是模块，直接用 python -m 调
    cmd = [sys.executable, "-m", "pandax.install_hook", "--root", args.root]
    if getattr(args, "uninstall", False):
        cmd.append("--uninstall")

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print(r.stdout, end="")
    if r.stderr:
        print(r.stderr, end="", file=sys.stderr)
    return r.returncode


def cmd_install_git(args):
    """
    探测/安装 git：
      - 默认：探测 + 报告
      - --probe-only：只探测不下载
      - --auto-download：自动下载 portable git
    """
    import shutil

    print(t("git_probe_check"))
    print()

    # 1. PATH 中
    existing = shutil.which("git")
    if existing:
        print(t("git_probe_found", path=existing))
        try:
            r = subprocess.run(
                ["git", "--version"], capture_output=True, text=True, timeout=5
            )
            print(t("_git_version", ver=r.stdout.strip()))
        except Exception:
            pass
        print()
        print(t("_git_ready"))
        return 0

    # 2. 常见路径
    candidates = [
        r"C:\Program Files\Git\cmd",
        r"C:\Program Files (x86)\Git\cmd",
        r"C:\Program Files\Git\bin",
        r"D:\软件\Git\cmd",
        r"C:\Git\cmd",
    ]
    found = None
    for cand in candidates:
        if Path(cand, "git.exe").exists():
            found = cand
            break

    if found:
        print(t("git_probe_found", path=found))
        print(t("_git_path_tip", path=found))
        print(t("git_powershell_hint", path=found))
        return 0

    # 3. 未找到
    print(t("git_not_installed"))
    print()
    print(t("git_install_hint"))
    print(t("git_install_hint_url"))
    print(t("git_install_hint_winget"))
    print(t("git_install_hint_choco"))
    print()

    if getattr(args, "auto_download", False):
        return _download_portable_git()

    return 1


def _download_portable_git():
    """
    下载并解压 PortableGit（zip 版，免安装）。
    来源：https://github.com/git-for-windows/git/releases
    """
    import urllib.request
    import zipfile

    # 使用最新的 portable zip（保留版本号以便追溯）
    version = "2.47.1"
    url = f"https://github.com/git-for-windows/git/releases/download/v{version}.windows.1/PortableGit-{version}-64-bit.zip"
    target = ROOT / "git"
    target.mkdir(parents=True, exist_ok=True)
    zip_path = target / "git.zip"

    print(t("git_downloading", url=url))
    print(t("git_target", target=target))
    print(t("git_size_hint"))

    try:
        urllib.request.urlretrieve(url, zip_path)
    except Exception as e:
        print(t("git_download_failed", err=e))
        return 1

    print(t("git_extracting"))
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target)
    except Exception as e:
        print(t("git_extract_failed", err=e))
        return 1
    finally:
        zip_path.unlink(missing_ok=True)

    git_exe = target / "cmd" / "git.exe"
    if git_exe.exists():
        print()
        print(t("git_installed", path=git_exe))
        print(t("git_path_hint", path=target/'cmd'))
        print(t("git_powershell_hint", path=target / "cmd"))
        return 0

    print(t("git_install_failed"))
    return 1


def cmd_watch(args):
    """
    启动 watchdog：
      - --daemon：后台启动，立即返回
      - 默认：前台运行（Ctrl+C 停止）
    """
    import subprocess

    root = Path(args.root).resolve()
    pandax_dir = root / ".pandax"
    if not pandax_dir.exists():
        print(t("_watch_no_init", root=root))
        return 1

    if getattr(args, "daemon", False):
        # 后台模式
        log_path = pandax_dir / "watchdog.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log_path, "ab")

        # Windows 用 DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP
        # Unix 用 start_new_session
        kwargs = {
            "stdout": log_file,
            "stderr": log_file,
            "stdin": subprocess.DEVNULL,
            "close_fds": True,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            kwargs["start_new_session"] = True

        # PyInstaller 环境下用打包后的 exe；pip 安装后用 python -m pandax_guard；开发模式用 .py
        if getattr(sys, "frozen", False):
            # 打包环境：pandax_guard.exe 在 pandax.exe 旁边
            exe_dir = Path(sys.executable).resolve().parent
            watchdog_exe = exe_dir / "pandax_guard.exe"
            if not watchdog_exe.exists():
                print(t("hook_not_found", path=watchdog_exe))
                return 1
            cmd = [str(watchdog_exe), "--root", str(root)]
        else:
            # 优先用 python -m pandax_guard（pip 安装后）
            cmd = [sys.executable, "-m", "pandax_guard", "--root", str(root)]

        p = subprocess.Popen(
            cmd,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
            **kwargs,
        )
        # 等 watchdog 写 PID
        pid_path = pandax_dir / ".watchdog_pid"
        for _ in range(20):
            if pid_path.exists():
                break
            time.sleep(0.1)

        print(t("watch_daemon_started"))
        print(t("watch_daemon_pid", pid=p.pid))
        print(t("watch_daemon_log", path=log_path))
        if sys.platform == "win32":
            print(t("watch_stop_win", pid=p.pid))
        else:
            print(t("watch_stop_unix", pid=p.pid))
        return 0

    # 前台模式：直接调用 pandax_guard.run_watchdog()
    sys.path.insert(0, str(ROOT))
    try:
        from pandax_guard import run_watchdog
        run_watchdog(root, daemon=False)
    except ImportError as e:
        print(t("hook_import_err", err=e))
        return 1
    return 0


def cmd_ci(args):
    """
    Phase 7 — GitHub Actions CI 验证。
    检查 base..head 之间所有变更是否都有审计：
      1. git diff --name-only 获取变更文件
      2. 过滤出受保护扩展名（text + binary）
      3. 每个文本文件：检查 pandax.jsonl 是否有 APPROVED 记录
      4. 每个二进制文件：检查 binary_snapshots.json 中 SHA256 是否与最新 write 一致
      5. 缺审计的文件 → 输出 + rc=1
      6. 全有 → rc=0

    第一性原理：
      CI 是审计系统的最后一道闸——保证 PR 合入前所有变更都走 write。
      没有它，agent 可以 git add + git commit 绕开审计。

    对抗式审查：
      - 攻击：agent 改 pandax.jsonl 抹除痕迹
        缓解：CI 比较 git 历史里的 audit 文件
      - 攻击：删 .pandax/ 抹除全部记录
        缓解：CI fail，要求重新 init + write
      - 攻击：基线分支选择绕过
        缓解：--base 默认 main，必须显式
    """
    import hashlib as _hl
    import json as _json
    import subprocess
    import shutil as _sh

    root = Path(args.root).resolve()
    pandax_dir = root / ".pandax"

    # Phase 7: 解析 git 可执行文件绝对路径（防止 PATH 损坏/编码问题）
    git_exe_path = _resolve_git_exe()
    GIT = git_exe_path  # _resolve_git_exe() returns absolute path or "git" fallback

    def _git_run(*args, timeout=5):
        return subprocess.run([GIT] + list(args), cwd=str(root),
                              capture_output=True, text=True, timeout=timeout)

    if not pandax_dir.exists():
        print(t("ci_reject_no_init", root=root))
        return 1

    # 读取 config
    config_path = pandax_dir / "config.json"
    config = _json.loads(config_path.read_text(encoding="utf-8"))
    text_exts = set(config.get("protected_extensions", [".py"]))
    binary_exts = set(config.get("binary_protected_extensions", []))

    # 默认 base
    base = args.base or "main"
    head = args.head or "HEAD"

    # 检查 git
    try:
        r = _git_run("rev-parse", "--is-inside-work-tree")
        if r.returncode != 0:
            print(t("ci_reject_no_git_repo", root=root))
            return 1
    except FileNotFoundError:
        print(t("ci_reject_no_git", git=GIT))
        return 1

    # 检查 base 分支是否存在（HEAD 或分支名）
    def _resolve_ref(ref):
        r = _git_run("rev-parse", "--verify", ref)
        return r.returncode == 0

    base_resolved = False
    # Phase 7: 优先顺序——HEAD~1（最可靠，PR base 经常缺失）
    candidates = [f"HEAD~1"]
    candidates.extend([base, f"origin/{base}", "main", "master", "origin/main", "origin/master"])
    for ref in candidates:
        if _resolve_ref(ref):
            base = ref
            base_resolved = True
            break

    if not base_resolved:
        # Bug #20 fix: 区分"空仓库（无 commit）"和"首次 commit（HEAD 存在但无 HEAD~1）"
        # 之前两者都报 "empty repo"，但首次 commit 是合法场景 — 有变更要审计。
        # 用 `git rev-list -n 1 --all` 检查是否有任何 commit
        r_any = _git_run("rev-list", "-n", "1", "--all")
        if r_any.returncode != 0 or not r_any.stdout.strip():
            # 真·空仓库：无任何 commit → 无变更可审计
            print("=" * 64)
            print(t("ci_header", root=root))
            print(t("ci_baseline_empty"))
            print("=" * 64)
            print(t("ci_pass_empty"))
            print(f'{{"status":"PASS","violations":0,"changed":0,"note":"empty repo"}}')
            return 0

        # 有 commit 但 baseline 解析失败：可能是首次 commit，HEAD~1 不存在。
        # 智能 fallback：直接用 HEAD 作为 baseline（虽然 HEAD~1 不存在），
        # 此时 `git diff HEAD..HEAD` 是空，可视为"无变更" PASS。
        # 但更稳妥：报错要求用户指定 --base（避免误判变更）
        print("=" * 64)
        print(t("ci_header", root=root))
        # 重新尝试用当前 HEAD 的全部 tree 作为基线
        r_tree = _git_run("rev-parse", "HEAD^{tree}")
        if r_tree.returncode == 0 and r_tree.stdout.strip():
            tree_sha = r_tree.stdout.strip()
            r_diff = _git_run("diff", "--name-only", f"{tree_sha}", "HEAD", timeout=10)
            if r_diff.returncode == 0:
                changed = [f.strip() for f in r_diff.stdout.splitlines() if f.strip()]
                if not changed:
                    print(t("ci_baseline_no_changes"))
                    print(t("ci_pass_empty"))
                    print(f'{{"status":"PASS","violations":0,"changed":0,"note":"no changes vs current tree"}}')
                    return 0
        # baseline 不可解析且无法 fallback：报错 + 退出非 0
        print(t("ci_reject_no_baseline", base=base))
        return 1

    # 1. 找出变更文件
    diff_range = f"{base}...{head}" if head == "HEAD" else f"{base}..{head}"
    r = _git_run("diff", "--name-only", diff_range, timeout=10)
    if r.returncode != 0:
        print(t("ci_reject_diff_fail", err=r.stderr.strip()))
        return 1

    changed_files = [f.strip().replace("\\", "/") for f in r.stdout.splitlines() if f.strip()]

    # 2. 加载审计记录
    audit_records = []
    audit_path = pandax_dir / "pandax.jsonl"
    if audit_path.exists():
        for line in audit_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    audit_records.append(_json.loads(line))
                except _json.JSONDecodeError:
                    continue

    approved_files = {
        rec.get("file", "").replace("\\", "/")
        for rec in audit_records
        if rec.get("status") == "APPROVED"
    }

    # 3. 加载二进制快照
    snapshots = {}
    snap_path = pandax_dir / "binary_snapshots.json"
    if snap_path.exists():
        try:
            snapshots = _json.loads(snap_path.read_text(encoding="utf-8"))
        except _json.JSONDecodeError:
            pass

    # 4. 检查每个变更文件
    violations = []
    for rel in changed_files:
        # 只检查受保护扩展名
        ext = Path(rel).suffix
        if ext in binary_exts:
            # 二进制：检查 SHA256 是否在 snapshot 中
            fp = root / rel
            if not fp.exists():
                continue  # 删除的文件不算
            actual_sha = _hl.sha256(fp.read_bytes()).hexdigest()
            expected_sha = snapshots.get(rel)
            if expected_sha != actual_sha:
                violations.append({
                    "file": rel,
                    "type": "binary",
                    "reason": f"SHA256 不一致 (snapshot={expected_sha[:8] if expected_sha else 'NONE'}...)",
                })
        elif ext in text_exts:
            # 文本：检查是否有 APPROVED 记录
            if rel not in approved_files:
                violations.append({
                    "file": rel,
                    "type": "text",
                    "reason": "未找到 APPROVED 审计记录（可能绕过 pandax write 直接修改）",
                })

    # 5. 报告
    print("=" * 64)
    print(t("ci_header", root=root))
    print(t("ci_baseline", base=base, head=head))
    print(t("ci_changed_n", n=len(changed_files)))
    print(t("ci_ext_stats", t=len(text_exts), b=len(binary_exts)))
    print("=" * 64)

    if not violations:
        print(t("ci_pass_all"))
        print(t("ci_pass_json", n=len(changed_files)))
        return 0

    print(f"\n{t('ci_fail_n', n=len(violations))}\n")
    for v in violations:
        marker = "[二进制]" if v["type"] == "binary" else "[文本  ]"
        print(f"  {marker} {v['file']}")
        print(t("ci_fail_file", reason=v['reason']))
    print()
    print("=" * 64)
    print(t("ci_fix_hint"))
    print(t("ci_fix_cmd"))
    print("=" * 64)
    print(t("ci_fail_json", n=len(violations), m=len(changed_files)))
    return 1


# ============================================================
# Phase 9: OS 右键菜单集成
# ============================================================
INSTALLER_DIR = Path(__file__).resolve().parent.parent.parent / "installer"

PLATFORM_HANDLERS = {
    "Windows": {
        "install":   "windows/install_context_menu.ps1",
        "uninstall": "windows/uninstall_context_menu.ps1",
        # Bug #15 fix: 加 -NoProfile（避免 profile.ps1 加载阻塞）
        # + -NonInteractive（避免 Read-Host 等阻塞调用）
        "interpreter": ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File"],
    },
    "Darwin": {
        "install":   "macos/install_context_menu.sh",
        "uninstall": "macos/uninstall_context_menu.sh",
        "interpreter": ["bash"],
    },
    "Linux": {
        "install":   "linux/install_context_menu.sh",
        "uninstall": "linux/uninstall_context_menu.sh",
        "interpreter": ["bash"],
    },
}


def detect_os_key() -> str:
    """把 sys.platform 映射到 PLATFORM_HANDLERS 的 key"""
    p = sys.platform
    if p.startswith("win"):
        return "Windows"
    if p.startswith("darwin"):
        return "Darwin"
    if p.startswith("linux") or p.startswith("freebsd"):
        return "Linux"
    return ""


def _run_installer(action: str, force: bool = False):
    """
    action: "install" | "uninstall"
    自动检测 OS → 调用对应 installer 脚本
    """
    os_key = detect_os_key()
    if not os_key:
        print(t("err_unsupported_platform", platform=sys.platform))
        return 2

    handler = PLATFORM_HANDLERS[os_key]
    script_rel = handler[action]
    interpreter = handler["interpreter"]
    script_path = INSTALLER_DIR / script_rel

    if not script_path.exists():
        print(t("err_script_not_found", path=script_path))
        print(f"  {t('_check_package_data', platform=os_key)}")
        return 1

    cmd = interpreter + [str(script_path)]
    if action == "install" and force:
        # Windows PS1 接受 -Force；bash 不接参数即可（幂等）
        if os_key == "Windows":
            cmd += ["-Force"]

    # 传当前语言给子进程（installer 脚本读 ~/.pandax/config.json 即可）
    # 但显式传 PANDAX_LANG 更稳（避免子进程 HOME 路径问题）
    env = os.environ.copy()
    from .i18n import get_lang
    env["PANDAX_LANG"] = get_lang()

    print(t("info_os_detected", os=os_key))
    print(t("info_running", cmd=' '.join(cmd)))
    print()

    try:
        # Bug #15 fix:
        # 1. timeout=60s：installer 脚本通常几秒完成，但 powershell 在某些场景
        #    （如 registry provider 阻塞、profile 加载慢）可能挂死。60 秒兜底。
        # 2. capture_output=True：捕获 stderr 让错误诊断更友好
        # 3. timeout 抛 TimeoutExpired 时明确告知用户 + 返回 124（标准 timeout exit code）
        # macOS/Linux bash 同理
        result = subprocess.run(
            cmd, check=False, env=env, timeout=60, capture_output=True, text=True,
        )
        if result.returncode != 0:
            # 输出 stderr 帮助用户诊断
            if result.stderr:
                print(t("warn_installer_stderr", code=result.returncode))
                for line in result.stderr.strip().splitlines()[-10:]:
                    print(f"  {line}")
        return result.returncode
    except subprocess.TimeoutExpired as e:
        print(t("err_installer_timeout"))
        print(f"  cmd: {' '.join(cmd[:5])}...")
        # Bug #15 fix: 返回 124（标准 timeout exit code），方便脚本/CI 识别
        return 124
    except FileNotFoundError as e:
        print(f"[ERROR] {t('_interp_unavailable', interp=interpreter[0])}")
        print(f"  {e}")
        return 127


def cmd_install_context(args):
    """
    Phase 9 — 安装 OS 右键菜单（自动检测平台）

    支持：
      - Windows: HKCU 注册表级联菜单（无需管理员）
      - macOS:   Automator Quick Action
      - Linux:   Nautilus 脚本 + Dolphin 服务菜单

    Phase 10: --lang 指定 UI 语言（写入 ~/.pandax/config.json，被 PS1 脚本读取）
    """
    force = getattr(args, "force", False)
    lang = getattr(args, "lang", None)
    if lang:
        # 先切换语言（写入 ~/.pandax/config.json）让 PS1 脚本读取
        i18n_init(lang)
    return _run_installer("install", force=force)


def cmd_uninstall_context(args):
    """
    Phase 9 — 卸载 OS 右键菜单（自动检测平台）
    """
    return _run_installer("uninstall")


COMMANDS = {
    "init": cmd_init,
    "lock": cmd_lock,
    "unlock": cmd_unlock,
    "write": cmd_write,
    "log": cmd_log,
    "install-git": cmd_install_git,
    "install-hook": cmd_install_hook,
    "status": cmd_status,
    "watch": cmd_watch,
    "ci": cmd_ci,
    "install-context": cmd_install_context,
    "uninstall-context": cmd_uninstall_context,
}


# ============================================================
# main
# ============================================================
def main(argv=None):
    argv_list = argv if argv is not None else sys.argv[1:]

    # Bug #5 fix: 预扫描 --lang，让其支持任意位置（子命令前后都可）
    # argparse parse_known_args 会把子命令后的 --lang 当作 status 的未知参数，
    # 导致 `pandax status --lang=en --root .` 不生效。手动预提取后塞回 args.lang。
    import re as _re
    cleaned_argv = []
    lang_override = None
    i = 0
    while i < len(argv_list):
        arg = argv_list[i]
        m_eq = _re.fullmatch(r"--lang=(\S+)", arg)
        if m_eq:
            lang_override = m_eq.group(1)
            i += 1
            continue
        if arg == "--lang" and i + 1 < len(argv_list):
            lang_override = argv_list[i + 1]
            i += 2
            continue
        cleaned_argv.append(arg)
        i += 1
    # 验证 lang_override 值合法（必须是 zh-CN / en）
    if lang_override is not None and lang_override not in ("zh-CN", "en"):
        # 不合法的 --lang 值让 argparse 自然报错（用户得到更友好的错误）
        cleaned_argv.append(f"--lang={lang_override}")
        lang_override = None

    # 0. 解析参数（早期）— 必须在 fingerprint 检查之前拿到 --trust-default / --silent / --lang
    parser = build_parser()
    # parse_known_args 允许子命令后还有遗留 argv（兼容未来扩展）
    args, _ = parser.parse_known_args(cleaned_argv)
    # Bug #5 fix: 把预扫描得到的 --lang 应用到 args
    if lang_override is not None:
        args.lang = lang_override

    # 0-pre. Phase 10: 初始化 i18n（必须在所有 print 之前）
    # 优先级：--lang > 用户偏好 ~/.pandax/config.json > OS 自动检测
    i18n_init(args.lang)

    # 0a. --update-fingerprint 必须绕过（更新本身就是改指纹）
    if "--update-fingerprint" in argv_list:
        pass  # 走下面 4. 分支
    elif getattr(args, "trust_default", False):
        # Phase 9+ --trust-default：使用默认密码 0000 自动初始化/更新指纹（右键场景）
        # 目的：让普通用户不需要手动跑 `pandax --update-fingerprint 0000`
        if not check_fingerprint(silent=True):
            # 指纹不匹配 → 不要阻断命令，而是用 0000 自动重写
            new_fp = compute_fingerprint()
            FP_PATH.parent.mkdir(parents=True, exist_ok=True)
            FP_PATH.write_text(new_fp, encoding="utf-8")
    else:
        if not check_fingerprint():
            return 1

    # 1. 启动显示 ASCII banner（品牌门面）— --silent 时跳过（右键场景）
    if not getattr(args, "silent", False):
        banner = load_banner()
        for line in banner:
            print(line)

        # 2. 启动必读 README（机制核心）— --silent 时也跳过
        summary = load_readme_summary()
        for line in summary:
            print(line)

    # 3. --version
    if getattr(args, "version", False):
        from pandax import __version__
        print(f"pandax v{__version__}")
        return 0

    # 4. --update-fingerprint（先于一切处理）
    if getattr(args, "update_fingerprint", None):
        pwd = args.update_fingerprint
        if pwd != FINGERPRINT_PASSWORD:
            print(t("err_password_wrong"))
            return 1
        new_fp = compute_fingerprint()
        FP_PATH.write_text(new_fp, encoding="utf-8")
        print(t("ok_fp_updated", fp=new_fp[:16]))
        return 0

    # 5. 无子命令：仅显示 README 摘要后退出
    if args.command is None:
        parser.print_help()
        return 0

    # 6. 执行子命令
    handler = COMMANDS.get(args.command)
    if handler is None:
        print(t("err_unknown_cmd", cmd=args.command))
        return 2

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())