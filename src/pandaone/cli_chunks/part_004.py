# cli.py chunk 4/6: lines 1202-1611
def _query_records(args):
    """共享 query + filter 逻辑（cmd_log 和 cmd_export 共用）。"""
    import json
    root = Path(args.root).resolve()
    audit_path = root / ".pandaone" / "pandaone.jsonl"
    if not audit_path.exists():
        return [], None
    records = []
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    filtered = records
    if getattr(args, "file", ""):
        filtered = [r for r in filtered if r.get("file") == args.file]
    if getattr(args, "session", ""):
        filtered = [r for r in filtered if r.get("session_id") == args.session]
    if getattr(args, "rejected", False):
        filtered = [r for r in filtered if r.get("status") == "REJECTED"]
    if getattr(args, "unauthorized", False):
        filtered = [r for r in filtered if r.get("status") == "UNAUTHORIZED"]
    if getattr(args, "recent", 0) and getattr(args, "recent", 0) > 0:
        filtered = filtered[-args.recent:]
    if getattr(args, "agent", ""):
        target_agent = args.agent
        filtered = [r for r in filtered if r.get("agent") == target_agent]
    return filtered, root


def cmd_log(args):
    """查询审计历史。"""
    filtered, root = _query_records(args)
    if root is None:
        return 1
    if getattr(args, "export", ""):
        from .exporters import export_html
        out_path = Path(args.export)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        export_html(filtered, out_path)
        print(t("log_export_ok", n=len(filtered), path=out_path))
        return 0
    if getattr(args, "format", "") or getattr(args, "output", ""):
        if not getattr(args, "format", ""):
            print(t("err_format_without_format"))
            return 1
        if not getattr(args, "output", ""):
            print(t("err_format_without_output"))
            return 1
        print(t("warn_log_export_use_export_subcommand"))
    if getattr(args, "format", "") and getattr(args, "output", ""):
        from .exporters import export_records
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        ok = export_records(filtered, args.format, out_path)
        if not ok:
            return 1
        print(t("log_export_ok_format", n=len(filtered), fmt=args.format, path=out_path))
        return 0
    _print_log._verbose = getattr(args, "verbose", False)
    _print_log(filtered)
    _print_log._verbose = False
    return 0


def cmd_export(args):
    """Bug #25 fix: 独立 export 子命令。"""
    filtered, root = _query_records(args)
    if root is None:
        return 1
    if not getattr(args, "format", ""):
        print(t("export_err_no_format"))
        return 1
    if not getattr(args, "output", ""):
        print(t("export_err_no_output"))
        return 1
    from .exporters import export_records
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok = export_records(filtered, args.format, out_path)
    if not ok:
        return 1
    print(t("export_ok", n=len(filtered), fmt=args.format, path=out_path))
    return 0


def _print_log(records):
    """格式化输出审计记录（v0.7.3 面板格式）"""
    verbose = getattr(_print_log, "_verbose", False)
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
        agent = rec.get("agent", "user:anonymous")
        if status == "APPROVED":
            status_icon = _colorize("OK APPROVED", "green")
        elif status == "REJECTED":
            status_icon = _colorize("X REJECTED", "red")
        elif status == "UNAUTHORIZED":
            status_icon = _colorize("WARN UNAUTHORIZED", "yellow")
        else:
            status_icon = status
        header_line = f"{status_icon} - {rid} - {ts} - by {_colorize(agent, 'cyan')}"
        print("--- record ---")
        print(f"file: {file_}")
        commit = rec.get("commit_hash") or "no_commit"
        print(f"commit: {commit[:12]}")
        if status == "APPROVED":
            print(f"reason: {rec.get('reason', '')}")
            print(f"problem: {rec.get('problem', '')}")
            print(f"approach: {rec.get('approach', '')}")
        elif status == "REJECTED":
            print(f"rejection: {rec.get('rejection_reason', '')}")
        print("--- end ---")


def cmd_status(args):
    """显示项目状态仪表盘。"""
    import json
    import stat
    root = Path(args.root).resolve()
    pandaone_dir = root / ".pandaone"
    if not pandaone_dir.exists():
        return 1
    print("=" * 64)
    print(t("status_header", root=root))
    print("=" * 64)
    protected_files = _iter_protected_files(root, {})
    if protected_files:
        locked = sum(1 for p in protected_files if not (p.stat().st_mode & stat.S_IWUSR))
        unlocked = len(protected_files) - locked
        print(t("status_l1"))
        print(t("status_total", n=len(protected_files)))
        print(t("status_locked_unlocked", n=locked, m=unlocked))
    print()
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
    audit_path = pandaone_dir / "pandaone.jsonl"
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
        total = len(records)
        print(t("status_total_records", n=total))
    print()
    print("=" * 64)
    return 0
