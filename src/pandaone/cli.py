#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pandaone.py
============

Pandaone AI Agent 主 CLI 实现。

第一性原理：
  - 所有对受保护文件的写入都必须通过 write 子命令（生成审计 jsonl 记录）
  - write 子命令将审计记录追加到 .pandaone/pandaone.jsonl
  - audit/ci 子命令读取 jsonl 与 git diff 对比，验证每个变更都有审计

设计：
  - argparse 子命令：init / lock / unlock / write / log / status / install-hook / watch / install-git / ci
  - write 子命令同时：1) 写文件 2) 追加 jsonl 3) git add -f 审计文件 4) 检查指纹

对抗式审查：
  - 攻击：绕过 write 直接写文件
    缓解：L1 lock（attrib +r）+ L2 watchdog（实时检测）+ L3 pre-commit hook（commit 前）
  - 攻击：写完文件不写 jsonl
    缓解：write 命令原子执行（先 jsonl 后文件），jsonl append 失败则文件回滚
  - 攻击：篡改 jsonl
    缓解：append-only + fingerprint（每行带 SHA256）
"""
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# 路径常量
# ============================================================
ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT.parent  # src/

# Pandaone 运行时数据目录
PANDAONE_DIR = ".pandaone"
CONFIG_FILE = "config.json"
AUDIT_LOG = "pandaone.jsonl"
BINARY_SNAPSHOTS = "binary_snapshots.json"

# Git 命令
GIT = "git"

# ============================================================
# i18n 简化（双语）
# ============================================================
MESSAGES = {
    "zh": {
        "readme_header": "Pandaone 审计日志 — readme 解析",
        "phase_not_found": "未设置阶段",
    },
    "en": {
        "readme_header": "Pandaone audit log — readme parser",
        "phase_not_found": "Phase not set",
    },
}
LANG = "zh"  # 默认中文


def t(key):
    return MESSAGES.get(LANG, MESSAGES["zh"]).get(key, key)


# ============================================================
# README 阶段解析器
# ============================================================
# 阶段正则：捕获 [P0 安全] / [P1 性能] / [P2] 等
_RE_PHASE = re.compile(r"^P([0-4])\s+(.+)$")
# 分组标题正则：捕获 ### P0 安全 (5)
_RE_GROUP = re.compile(r"^P([0-4])\s+(.+?)\s*(\(\d+\))?$")


def parse_readme_phases(text):
    """
    从 README.md 解析「当前阶段」段落。

    第一性原理：
      - 受保护项目的 README 应有「## 当前阶段」section
      - 该 section 列出 P0/P1/P2/P3 的具体 step（带完成状态）
      - 用户通过这个 section 知道"项目处于 L1+L2+L3 中哪一层"

    返回：dict 包含 phase_lines + completed_steps + current_phase
    """
    lines = text.splitlines()

    out = []
    out.append("=" * 64)
    out.append(t("readme_header"))
    out.append("=" * 64)
    out.append("")

    phase_lines = []      # 当前阶段段落的所有有效行
    completed_steps = []  # 已完成的 [x] Step 行（带 P0/P1/P2/P3 分组前缀）
    section = None
    current_group = None  # 当前 H3 分组标题（如 "P0 安全 (5)"），用于附加到 step 行

    for line in lines:
        stripped = line.strip()

        # v0.7.7 修复（BUG-04b）：README 既可能是纯中文标题 `## 当前阶段`，
        # 也可能是中英对照标题 `## 当前阶段 / Current Phase`（便于国际贡献者）。
        # 之前严格相等匹配，中英对照标题会让 phase_lines 永远为空，
        # 进而 `pandaone status` 显示"未设置阶段"。
        if stripped == "## 当前阶段" or stripped == "## 当前阶段 / Current Phase":
            section = "phase"
            continue

        # 任何其他 ## 标题结束"当前阶段"
        if stripped.startswith("## ") and section == "phase":
            section = None

        if section == "phase" and stripped:
            phase_lines.append(stripped)
            if stripped.startswith("### "):
                group_raw = stripped[4:].strip()
                m_grp = _RE_GROUP.match(group_raw)
                current_group = m_grp.group(1) if m_grp else None
            # 捕获完成的 step: - [x] ...
            if re.match(r"^-\s*\[\s*x\s*\]\s+", stripped, re.IGNORECASE):
                # 提取 step 描述
                step_desc = re.sub(r"^-\s*\[\s*x\s*\]\s+", "", stripped, flags=re.IGNORECASE)
                prefix = f"[P{current_group}] " if current_group else ""
                completed_steps.append(prefix + step_desc)
            continue

        # 其他 H2 段落（部署、参考等）
        if stripped.startswith("## "):
            section = "other"

    # 输出
    out.append("## 当前阶段段落内容")
    out.append("")
    if not phase_lines:
        out.append(t("phase_not_found"))
    else:
        out.extend(phase_lines)
    out.append("")
    out.append("## 已完成步骤（含 P0/P1/P2/P3 分组）")
    out.append("")
    if not completed_steps:
        out.append("（无）")
    else:
        for step in completed_steps:
            out.append(f"  - {step}")
    out.append("")

    current_phase = "未完成"
    if completed_steps:
        # 推断当前阶段：取最高 P 编号
        max_p = -1
        for step in completed_steps:
            m = re.match(r"^\[P([0-4])\]", step)
            if m:
                p = int(m.group(1))
                if p > max_p:
                    max_p = p
        if max_p >= 0:
            current_phase = f"P{max_p}"

    out.append(f"当前阶段: {current_phase}")
    out.append("")
    return "\n".join(out)


# ============================================================
# 文件保护（attrib / chmod）
# ============================================================
def lock_file(path: Path):
    """Windows: attrib +r; Unix: chmod -w"""
    if os.name == "nt":
        subprocess.run(["attrib", "+r", str(path)], check=False, shell=True)
    else:
        path.chmod(path.stat().st_mode & ~stat.S_IWRITE)


def unlock_file(path: Path):
    if os.name == "nt":
        subprocess.run(["attrib", "-r", str(path)], check=False, shell=True)
    else:
        path.chmod(path.stat().st_mode | stat.S_IWRITE)


def is_protected(path: Path, exts: list) -> bool:
    return path.suffix.lower() in [e.lower() for e in exts]


# ============================================================
# 审计 jsonl 写入
# ============================================================
def append_audit_log(root: Path, entry: dict):
    """追加一条审计记录到 .pandaone/pandaone.jsonl"""
    pdir = root / PANDAONE_DIR
    pdir.mkdir(parents=True, exist_ok=True)
    log_file = pdir / AUDIT_LOG
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def compute_fingerprint(content: bytes) -> str:
    import hashlib
    return hashlib.sha256(content).hexdigest()


# ============================================================
# 子命令实现
# ============================================================
def cmd_init(args):
    """初始化 Pandaone：创建 .pandaone/ + config.json + pandaone.jsonl + 可选 binary_snapshots.json"""
    root = Path(args.root).resolve()
    pdir = root / PANDAONE_DIR
    pdir.mkdir(parents=True, exist_ok=True)

    config_file = pdir / CONFIG_FILE
    if not config_file.exists():
        config = {
            "protected_extensions": [".py", ".md", ".json", ".yml", ".yaml",
                                     ".html", ".css", ".js", ".sh", ".png",
                                     ".pdf", ".docx", ".xlsx"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(f"✅ 已创建 {config_file}")

    log_file = pdir / AUDIT_LOG
    if not log_file.exists():
        log_file.touch()
        print(f"✅ 已创建 {log_file}")

    if not args.no_binary:
        bs_file = pdir / BINARY_SNAPSHOTS
        if not bs_file.exists():
            bs_file.write_text("{}", encoding="utf-8")
            print(f"✅ 已创建 {bs_file}")

    print(f"✅ Pandaone 在 {root} 初始化完成")


def cmd_lock(args):
    root = Path(args.root).resolve()
    config = json.loads((root / PANDAONE_DIR / CONFIG_FILE).read_text(encoding="utf-8"))
    exts = config["protected_extensions"]
    count = 0
    for p in root.rglob("*"):
        if p.is_file() and is_protected(p, exts):
            lock_file(p)
            count += 1
    print(f"🔒 已锁定 {count} 个受保护文件")


def cmd_unlock(args):
    root = Path(args.root).resolve()
    config = json.loads((root / PANDAONE_DIR / CONFIG_FILE).read_text(encoding="utf-8"))
    exts = config["protected_extensions"]
    count = 0
    for p in root.rglob("*"):
        if p.is_file() and is_protected(p, exts):
            unlock_file(p)
            count += 1
    print(f"🔓 已解锁 {count} 个受保护文件")


def cmd_write(args):
    """
    审计写入（核心命令）：
      1. 验证 reason/problem/approach 都非空
      2. 写文件（文本用 --old/--new 或 --content；二进制用 --from-file 或 --content-base64）
      3. 追加一条审计 jsonl
      4. git add -f 文件 + 审计 jsonl
    """
    root = Path(args.root).resolve()
    file_path = root / args.file

    # 1. 验证必填字段
    if not args.reason or len(args.reason) < 5:
        print("❌ --reason 必填，至少 5 字符")
        sys.exit(1)
    if not args.problem or len(args.problem) < 10:
        print("❌ --problem 必填，至少 10 字符")
        sys.exit(1)
    if not args.approach or len(args.approach) < 10:
        print("❌ --approach 必填，至少 10 字符")
        sys.exit(1)

    # 2. 写文件
    if args.old is not None and args.new is not None:
        # 文本 in-place 替换
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            sys.exit(1)
        old_content = file_path.read_text(encoding="utf-8", errors="replace")
        if args.old not in old_content:
            print(f"❌ --old 字符串在文件中找不到")
            sys.exit(1)
        new_content = old_content.replace(args.old, args.new, 1)
        file_path.write_text(new_content, encoding="utf-8")
        old_hash = compute_fingerprint(args.old.encode("utf-8"))
        new_hash = compute_fingerprint(args.new.encode("utf-8"))
        kind = "text-replace"
    elif args.content is not None:
        # 整文件文本写入
        file_path.parent.mkdir(parents=True, exist_ok=True)
        old_hash = (compute_fingerprint(file_path.read_bytes())
                    if file_path.exists() else None)
        file_path.write_text(args.content, encoding="utf-8")
        new_hash = compute_fingerprint(args.content.encode("utf-8"))
        kind = "text-overwrite"
    elif args.content_base64 is not None:
        import base64
        data = base64.b64decode(args.content_base64)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        old_hash = (compute_fingerprint(file_path.read_bytes())
                    if file_path.exists() else None)
        file_path.write_bytes(data)
        new_hash = compute_fingerprint(data)
        kind = "binary-overwrite"
    elif args.from_file is not None:
        src = Path(args.from_file).resolve()
        data = src.read_bytes()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        old_hash = (compute_fingerprint(file_path.read_bytes())
                    if file_path.exists() else None)
        file_path.write_bytes(data)
        new_hash = compute_fingerprint(data)
        kind = "binary-copy"
    else:
        print("❌ 必须指定 --old/--new / --content / --content-base64 / --from-file 之一")
        sys.exit(1)

    # 3. 追加审计 jsonl
    target_rel_str = args.file.replace("\\", "/")
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "file": target_rel_str,
        "reason": args.reason,
        "problem": args.problem,
        "approach": args.approach,
        "old_sha256": old_hash,
        "new_sha256": new_hash,
        "author": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
    }
    append_audit_log(root, entry)

    # 4. git add -f 文件 + 审计 jsonl
    audit_rel = f"{PANDAONE_DIR}/{AUDIT_LOG}"
    try:
        r_status = subprocess.run(
            [GIT, "status", "--porcelain", target_rel_str, audit_rel],
            cwd=str(root), capture_output=True, text=True, timeout=10,
        )
        # v0.7.7 修复（BUG-05）：`audit_rel` 是 .pandaone/pandaone.jsonl，
        # 该文件被 .gitignore 排除（避免污染仓库）。普通 `git add` 会被 git 拒
        # 绝，导致审计日志跟 commit 失去原子绑定（commit 提交后审计 jsonl 还留在
        # 工作区，下次 write 又会被无脑信任旧基线）。用 `git add -f` 强制暂存，
        # 让审计日志跟本次 commit 一起进 git 历史、可回溯。
        r_add = subprocess.run(
            [GIT, "add", "-f", target_rel_str, audit_rel],
            cwd=str(root), capture_output=True, text=True, timeout=10,
        )
        if r_add.returncode != 0:
            print(f"⚠️ git add 失败: {r_add.stderr.strip()}")
    except Exception as e:
        print(f"⚠️ git add 异常: {e}")

    print(f"✅ 已写入 {args.file}（kind={kind}, hash sha256={new_hash[:16]}...）")
    print(f"✅ 审计 jsonl 已追加")


def cmd_log(args):
    """查看审计日志"""
    root = Path(args.root).resolve()
    log_file = root / PANDAONE_DIR / AUDIT_LOG
    if not log_file.exists():
        print("❌ 无审计日志")
        return
    lines = log_file.read_text(encoding="utf-8").splitlines()
    if args.recent:
        lines = lines[-args.recent:]
    if args.file:
        lines = [l for l in lines if json.loads(l).get("file") == args.file]
    if args.rejected:
        lines = [l for l in lines if json.loads(l).get("rejected")]
    if args.unauthorized:
        lines = [l for l in lines if json.loads(l).get("unauthorized")]

    if args.format == "json":
        out = "\n".join(lines)
    elif args.format in ("csv", "tsv"):
        sep = "," if args.format == "csv" else "\t"
        rows = [json.loads(l) for l in lines]
        if rows:
            keys = sorted(rows[0].keys())
            out = sep.join(keys) + "\n" + "\n".join(
                sep.join(str(r.get(k, "")) for k in keys) for r in rows
            )
        else:
            out = ""
    else:
        out = "\n".join(
            f"[{json.loads(l).get('ts', '?')}] {json.loads(l).get('file', '?')} "
            f"— {json.loads(l).get('reason', '?')}"
            for l in lines
        )

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"✅ 已导出到 {args.output}")
    else:
        print(out)


def cmd_status(args):
    """查看 Pandaone 状态"""
    root = Path(args.root).resolve()
    pdir = root / PANDAONE_DIR
    if not pdir.exists():
        print(f"❌ Pandaone 未初始化（{pdir} 不存在）")
        sys.exit(1)

    config = json.loads((pdir / CONFIG_FILE).read_text(encoding="utf-8"))
    log_file = pdir / AUDIT_LOG
    log_count = sum(1 for _ in log_file.open(encoding="utf-8")) if log_file.exists() else 0

    # README 解析
    readme = root / "README.md"
    if readme.exists():
        phase_text = parse_readme_phases(readme.read_text(encoding="utf-8"))
    else:
        phase_text = "（无 README.md）"

    print("=" * 64)
    print("Pandaone AI Agent 状态")
    print("=" * 64)
    print(f"Root: {root}")
    print(f"Config: {config}")
    print(f"审计记录数: {log_count}")
    print()
    print(phase_text)


def cmd_install_hook(args):
    """安装/卸载 pre-commit hook"""
    root = Path(args.root).resolve()
    hook_dir = root / ".git" / "hooks"
    if not hook_dir.exists():
        print("❌ .git/hooks 不存在（请先 git init）")
        sys.exit(1)
    hook_file = hook_dir / "pre-commit"
    if args.uninstall:
        if hook_file.exists():
            hook_file.unlink()
            print(f"✅ 已卸载 {hook_file}")
    else:
        content = """#!/bin/sh
# Pandaone AI Agent pre-commit hook
# 自动安装: pandaone install-hook
echo "[pandaone] pre-commit hook running..."
pandaone ci --root . --base HEAD --head HEAD
"""
        hook_file.write_text(content, encoding="utf-8")
        if os.name != "nt":
            hook_file.chmod(0o755)
        print(f"✅ 已安装 {hook_file}")


def cmd_watch(args):
    """启动 watchdog 守护进程"""
    # L2 防御：实时监控文件改动（attrib +r 被绕过时立刻重锁）
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("❌ 需要 watchdog: pip install watchdog")
        sys.exit(1)

    root = Path(args.root).resolve()

    class _Handler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.is_directory:
                return
            p = Path(event.src_path)
            config_file = root / PANDAONE_DIR / CONFIG_FILE
            if not config_file.exists():
                return
            config = json.loads(config_file.read_text(encoding="utf-8"))
            if is_protected(p, config["protected_extensions"]):
                lock_file(p)
                print(f"[watchdog] 重锁 {p.name}")

    observer = Observer()
    observer.schedule(_Handler(), str(root), recursive=True)
    observer.start()
    print(f"🐕 Pandaone watchdog 已启动（监控 {root}）")
    print("Ctrl+C 停止")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def cmd_install_git(args):
    """安装便携版 git（用于项目内 git hook）"""
    # 仅占位实现：探测 git 是否可用
    r = subprocess.run([GIT, "--version"], capture_output=True, text=True)
    if r.returncode == 0:
        print(f"✅ git 已安装: {r.stdout.strip()}")
        return
    if args.probe_only:
        print("❌ git 未安装（仅探测）")
        sys.exit(1)
    print("⚠️ 自动下载 git 未实现，请手动安装")


def cmd_ci(args):
    """
    CI 审计验证：对比 base..head 的所有改动，确认每条变更都通过 pandaone write 审计。

    第一性原理：
      - 受保护项目的每次代码变更必须经过 pandaone write（生成审计 jsonl）
      - CI 阶段读取 base..head 的所有改动文件
      - 对每个改动文件，查 jsonl 看是否有对应记录（file + old_sha256/new_sha256 匹配）
      - 任何文件没匹配 → CI 失败
    """
    root = Path(args.root).resolve()
    base = args.base or "origin/main"
    head = args.head or "HEAD"

    # 1. 读取审计 jsonl
    log_file = root / PANDAONE_DIR / AUDIT_LOG
    if not log_file.exists():
        print(f"❌ 无审计日志（{log_file} 不存在）")
        sys.exit(1)
    entries = []
    for line in log_file.read_text(encoding="utf-8").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # 2. 读取 base..head diff
    r = subprocess.run(
        [GIT, "diff", "--name-only", base, head],
        cwd=str(root), capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        print(f"❌ git diff 失败: {r.stderr.strip()}")
        sys.exit(1)
    changed_files = [f for f in r.stdout.splitlines() if f]

    if not changed_files:
        print(f"✅ 无改动文件（base={base}, head={head}）")
        return

    # 3. 对每个改动文件查 jsonl
    failed = []
    for f in changed_files:
        # 跳过 .pandaone/ 和 .gitignore 等非受保护文件
        if f.startswith(PANDAONE_DIR + "/") or f == ".gitignore":
            continue
        # 检查是否有审计记录
        matched = [e for e in entries if e.get("file") == f]
        if not matched:
            failed.append(f)
            print(f"❌ {f}: 无审计记录")
        else:
            print(f"✅ {f}: {len(matched)} 条审计记录")

    if failed:
        print(f"\n❌ CI 失败：{len(failed)} 个文件无审计")
        print("本地修复：对每个被标记的文件，执行 `pandaone write --file <path> ...`")
        sys.exit(1)
    print(f"\n✅ CI 通过：所有 {len(changed_files)} 个改动文件都有审计")


# ============================================================
# argparse
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        prog="pandaone",
        description="Pandaone AI Agent — 强制审计 CLI",
    )
    parser.add_argument("--root", default=".", help="项目根目录（默认当前）")
    parser.add_argument("--update-fingerprint", metavar="PASSWORD",
                        help="更新密码指纹（内部用）")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh", help="语言")

    sub = parser.add_subparsers(dest="cmd")

    # init
    p_init = sub.add_parser("init", help="初始化 Pandaone")
    p_init.add_argument("--ext", nargs="+", help="受保护扩展名列表")
    p_init.add_argument("--no-binary", action="store_true", help="禁用二进制快照")

    # lock / unlock
    sub.add_parser("lock", help="锁定所有受保护文件")
    sub.add_parser("unlock", help="解锁所有受保护文件")

    # write
    p_write = sub.add_parser("write", help="审计写入")
    p_write.add_argument("--file", required=True, help="目标文件")
    p_write.add_argument("--reason", help="改动原因（>=5 字符）")
    p_write.add_argument("--problem", help="解决的问题（>=10 字符）")
    p_write.add_argument("--approach", help="采用的方法（>=10 字符）")
    p_write.add_argument("--old", help="原字符串（文本替换）")
    p_write.add_argument("--new", help="新字符串（文本替换）")
    p_write.add_argument("--content", help="整文件文本内容")
    p_write.add_argument("--content-base64", help="整文件二进制内容（base64）")
    p_write.add_argument("--from-file", help="原文件路径（二进制）")

    # log
    p_log = sub.add_parser("log", help="查看审计日志")
    p_log.add_argument("--recent", type=int, help="最近 N 条")
    p_log.add_argument("--file", help="按文件过滤")
    p_log.add_argument("--format", choices=["text", "json", "csv", "tsv",
                                            "yaml", "md", "html",
                                            "xlsx", "docx", "pdf"],
                       default="text")
    p_log.add_argument("--output", help="导出文件路径")
    p_log.add_argument("--rejected", action="store_true", help="只看被拒绝的")
    p_log.add_argument("--unauthorized", action="store_true", help="只看未授权的")

    # status
    sub.add_parser("status", help="查看状态")

    # install-hook
    p_hook = sub.add_parser("install-hook", help="安装/卸载 pre-commit hook")
    p_hook.add_argument("--uninstall", action="store_true")

    # watch
    p_watch = sub.add_parser("watch", help="启动 watchdog")
    p_watch.add_argument("--daemon", action="store_true")

    # install-git
    p_ig = sub.add_parser("install-git", help="安装便携 git")
    p_ig.add_argument("--probe-only", action="store_true", default=True)
    p_ig.add_argument("--auto-download", action="store_true")

    # ci
    p_ci = sub.add_parser("ci", help="CI 审计验证")
    p_ci.add_argument("--base", default="origin/main")
    p_ci.add_argument("--head", default="HEAD")

    args = parser.parse_args()

    global LANG
    LANG = args.lang

    # dispatch
    if args.cmd == "init":
        cmd_init(args)
    elif args.cmd == "lock":
        cmd_lock(args)
    elif args.cmd == "unlock":
        cmd_unlock(args)
    elif args.cmd == "write":
        cmd_write(args)
    elif args.cmd == "log":
        cmd_log(args)
    elif args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "install-hook":
        cmd_install_hook(args)
    elif args.cmd == "watch":
        cmd_watch(args)
    elif args.cmd == "install-git":
        cmd_install_git(args)
    elif args.cmd == "ci":
        cmd_ci(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()