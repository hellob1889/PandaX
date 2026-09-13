#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pandaone_mcp.server — MCP (Model Context Protocol) server, stdio JSON-RPC 2.0 transport
v0.7.7: BUG-01 fixed + version bump
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT.parent

TOOLS = [
    {"name": "pandaone_init", "description": "在指定目录初始化 Pandaone AI Agent"},
    {"name": "pandaone_lock", "description": "锁定所有受保护扩展名的文件"},
    {"name": "pandaone_unlock", "description": "解锁所有受保护扩展名的文件"},
    {"name": "pandaone_write", "description": "审计写入（核心命令）"},
    {"name": "pandaone_log", "description": "查看审计日志"},
    {"name": "pandaone_status", "description": "查看 Pandaone 状态"},
    {"name": "pandaone_install_hook", "description": "安装 pre-commit hook"},
    {"name": "pandaone_watch", "description": "启动 watchdog 守护进程"},
    {"name": "pandaone_install_git", "description": "安装便携版 git"},
    {"name": "pandaone_fingerprint_update", "description": "更新密码指纹"},
    {"name": "pandaone_ci", "description": "CI 审计验证"},
]

HANDLERS = {
    "pandaone_init": lambda p: _run_cli(["init"]),
    "pandaone_lock": lambda p: _run_cli(["lock"]),
    "pandaone_unlock": lambda p: _run_cli(["unlock"]),
    "pandaone_write": lambda p: _run_cli(["write"]),
    "pandaone_log": lambda p: _run_cli(["log"]),
    "pandaone_status": lambda p: _run_cli(["status"]),
    "pandaone_install_hook": lambda p: _run_cli(["install-hook"]),
    "pandaone_watch": lambda p: _run_cli(["watch"]),
    "pandaone_install_git": lambda p: _run_cli(["install-git"]),
    "pandaone_fingerprint_update": lambda p: _run_cli(["--update-fingerprint"]),
    "pandaone_ci": lambda p: _run_cli(["ci"]),
}

def _run_cli(args, timeout=10):
    return subprocess.run(["pandaone"] + args, capture_output=True, text=True, timeout=timeout)

def _handle_request(req):
    method = req.get("method")
    params = req.get("params", {})
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req.get("id"), "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "pandaone", "version": "0.7.7"},  # v0.7.7: 同步 pandaone-guard 版本
        }}
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req.get("id"), "result": {"tools": TOOLS}}
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        if name not in HANDLERS:
            return {"jsonrpc": "2.0", "id": req.get("id"), "error": {"code": -32602, "message": f"Unknown tool: {name}"}}
        result = HANDLERS[name](args)
        return {"jsonrpc": "2.0", "id": req.get("id"), "result": result}
    return {"jsonrpc": "2.0", "id": req.get("id"), "error": {"code": -32601, "message": "Method not found"}}

def serve_stdio():
    sys.stdout.reconfigure(line_buffering=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle_request(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()

def main():
    serve_stdio()

if __name__ == "__main__":
    main()