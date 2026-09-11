#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pandaone_mcp.server
===================
MCP (Model Context Protocol) server — stdio JSON-RPC 2.0 transport。

第一性原理：
  - MCP 是让 AI Agent "发现工具 → 调用工具" 的标准化协议
  - JSON-RPC 2.0 over stdio（无网络暴露，最小攻击面）
  - 每个工具 = 一个 CLI 子命令的封装，复用现有 pandaone.py

设计：
  - 单进程：stdio 读写循环
  - 工具注册表：TOOLS dict 描述每个工具的 name / description / inputSchema
  - handler：调用 subprocess 执行 CLI，捕获输出返回

对抗式审查：
  - 攻击：恶意 stdin 注入
    缓解：JSON-RPC 严格校验，只接受 json.loads 成功的请求
  - 攻击：handler 阻塞
    缓解：subprocess.run 带 timeout，异常时返回 -32603
  - 攻击：进程作为攻击面
    缓解：stdio-only，不监听端口，进程由 IDE 管理生命周期
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# ============================================================
# 路径常量
# ============================================================
ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT.parent  # src/


# ============================================================
# 工具定义（MCP tools/list 返回的 schema）
# ============================================================
TOOLS = [
    {
        "name": "pandaone_init",
        "description": "在指定目录初始化 Pandaone AI Agent（创建 .pandaone/、config.json、pandaone.jsonl、可选 binary_snapshots.json）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "description": "项目根目录路径", "default": "."},
                "ext": {"type": "array", "items": {"type": "string"},
                        "description": "自定义受保护扩展名（如 ['.py', '.md']）"},
                "no_binary": {"type": "boolean", "default": False,
                              "description": "禁用二进制 SHA256 快照保护"},
            },
            "required": ["root"],
        },
    },
    {
        "name": "pandaone_lock",
        "description": "锁定所有受保护扩展名的文件（attrib +r / chmod -w）",
        "inputSchema": {
            "type": "object",
            "properties": {"root": {"type": "string", "default": "."}},
            "required": ["root"],
        },
    },
    {
        "name": "pandaone_unlock",
        "description": "解锁所有受保护扩展名的文件",
        "inputSchema": {
            "type": "object",
            "properties": {"root": {"type": "string", "default": "."}},
            "required": ["root"],
        },
    },
    {
        "name": "pandaone_write",
        "description": "审计写入（核心命令）：reason/problem/approach 必填；文本用 --old/--new 或 --content；二进制用 --from-file 或 --content-base64",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
                "file": {"type": "string", "description": "目标文件路径（相对 root）"},
                "reason": {"type": "string", "minLength": 5,
                           "description": "改动原因（必填，至少 5 字符）"},
                "problem": {"type": "string", "minLength": 10,
                            "description": "解决的问题（必填，至少 10 字符）"},
                "approach": {"type": "string", "minLength": 10,
                             "description": "采用的方法（必填，至少 10 字符）"},
                "old": {"type": "string", "description": "原字符串（仅文本）"},
                "new": {"type": "string", "description": "新字符串（仅文本）"},
                "content": {"type": "string", "description": "整文件文本内容"},
                "content_base64": {"type": "string",
                                   "description": "整文件二进制内容（base64）"},
                "from_file": {"type": "string",
                              "description": "从本地路径读取内容"},
            },
            "required": ["file", "reason", "problem", "approach"],
        },
    },
    {
        "name": "pandaone_log",
        "description": "查询审计历史，支持过滤和导出（13 种格式：text/csv/tsv/json/yaml/md/html/xlsx/docx/pdf/sqlite/rst/asciidoc）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
                "recent": {"type": "integer", "default": 20,
                           "description": "最近 N 条"},
                "file": {"type": "string", "description": "按文件过滤"},
                "rejected": {"type": "boolean", "default": False,
                             "description": "只看拒绝记录"},
                "unauthorized": {"type": "boolean", "default": False,
                                 "description": "只看非授权写入"},
                "format": {"type": "string",
                           "description": "导出格式（text/csv/json/yaml/md/html/xlsx/docx/pdf/sqlite/rst/asciidoc/tsv）"},
                "output": {"type": "string", "description": "导出文件路径"},
            },
            "required": ["root"],
        },
    },
    {
        "name": "pandaone_status",
        "description": "显示项目状态仪表盘（L1 锁 / L2 watchdog / L5 指纹 / 审计统计 / 二进制快照）",
        "inputSchema": {
            "type": "object",
            "properties": {"root": {"type": "string", "default": "."}},
            "required": ["root"],
        },
    },
    {
        "name": "pandaone_install_hook",
        "description": "安装 pre-commit hook（L3 防御，git commit 时强制审计）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
                "uninstall": {"type": "boolean", "default": False,
                              "description": "卸载而非安装"},
            },
            "required": ["root"],
        },
    },
    {
        "name": "pandaone_watch",
        "description": "启动 watchdog 守护进程（L2 防御：实时监控+git checkout 回滚）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
                "daemon": {"type": "boolean", "default": False,
                           "description": "后台运行"},
            },
            "required": ["root"],
        },
    },
    {
        "name": "pandaone_install_git",
        "description": "探测/安装 git（缺失时自动下载 portable 版本）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "probe_only": {"type": "boolean", "default": True,
                               "description": "只探测不下载"},
                "auto_download": {"type": "boolean", "default": False,
                                  "description": "自动下载 portable git"},
            },
        },
    },
    {
        "name": "pandaone_fingerprint_update",
        "description": "更新 pandaone 自身的 SHA256 指纹（合法修改 CLI源码后必须调用）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "password": {"type": "string", "default": "0000",
                              "description": "更新密码（默认 0000）"},
            },
        },
    },
    {
        "name": "pandaone_ci",
        "description": "GitHub Actions CI 验证：检查 PR 所有变更是否都有审计记录（无审计 = rc=1）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
                "base": {"type": "string", "default": "",
                         "description": "基线分支（默认 main，缺失则 fallback 到 HEAD~1）"},
                "head": {"type": "string", "default": "HEAD"},
            },
            "required": ["root"],
        },
    },
]


# ============================================================
# 工具 handler（每个调用 subprocess 执行 CLI）
# ============================================================
def _run_cli(args: list, timeout: int = 30) -> dict:
    """调用 pandaone CLI 子进程，返回 {returncode, stdout, stderr}"""
    cmd = [sys.executable, "-m", "pandaone", *args]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONPATH": str(SRC_DIR) + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        return {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "timeout"}
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e)}


def _args_from(params: dict, mapping: list) -> list:
    """把 MCP 参数映射成 CLI 参数列表

    mapping: [(param_key, cli_flag_or_None), ...]
    - param_key: MCP 参数名
    - cli_flag: CLI 参数（如（"--root"）
    - None 表示布尔开关（True 时加 flag）
    """
    out = []
    for key, flag in mapping:
        val = params.get(key)
        if val is None or val is False:
            continue
        if flag is None:
            # 布尔开关
            continue
        if isinstance(val, list):
            out.extend([flag, *val])
        else:
            out.extend([flag, str(val)])
    return out


HANDLERS = {
    "pandaone_init": lambda p: _run_cli(["init", *_args_from(p, [
        ("root", "--root"), ("ext", "--ext"), ("no_binary", "--no-binary")])], timeout=60),
    "pandaone_lock": lambda p: _run_cli(["lock", *_args_from(p, [("root", "--root")])]),
    "pandaone_unlock": lambda p: _run_cli(["unlock", *_args_from(p, [("root", "--root")])]),
    "pandaone_write": lambda p: _run_cli(["write", *_args_from(p, [
        ("root", "--root"), ("file", "--file"),
        ("reason", "--reason"), ("problem", "--problem"), ("approach", "--approach"),
        ("old", "--old"), ("new", "--new"),
        ("content", "--content"), ("content_base64", "--content-base64"),
        ("from_file", "--from-file")])], timeout=30),
    "pandaone_log": lambda p: _run_cli(["log", *_args_from(p, [
        ("root", "--root"), ("recent", "--recent"),
        ("file", "--file"), ("format", "--format"), ("output", "--output"),
    ])] + (["--rejected"] if p.get("rejected") else []) +
       (["--unauthorized"] if p.get("unauthorized") else []), timeout=30),
    "pandaone_status": lambda p: _run_cli(["status", *_args_from(p, [("root", "--root")])]),
    "pandaone_install_hook": lambda p: _run_cli(
        ["install-hook", *_args_from(p, [("root", "--root"), ("uninstall", "--uninstall")])]),
    "pandaone_watch": lambda p: _run_cli(
        ["watch", *_args_from(p, [("root", "--root"), ("daemon", "--daemon")])],
        timeout=5),  # watchdog 是长进程，5s 后 timeout 也 OK（实际是后台 spawn）
    "pandaone_install_git": lambda p: _run_cli(
        ["install-git",
         *(["--probe-only"] if not p.get("auto_download") else []),
         *(["--auto-download"] if p.get("auto_download") else [])]),
    "pandaone_fingerprint_update": lambda p: _run_cli(
        ["--update-fingerprint", p.get("password", "0000")]),
    "pandaone_ci": lambda p: _run_cli(["ci", *_args_from(p, [
        ("root", "--root"), ("base", "--base"), ("head", "--head")])], timeout=30),
}


# ============================================================
# JSON-RPC 2.0 dispatcher
# ============================================================
def _make_response(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _make_error(id_, code, message, data=None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": err}


def _handle_request(req: dict) -> dict | None:
    """处理一条 JSON-RPC 请求，返回响应 dict（或 None 表示通知）"""
    if not isinstance(req, dict):
        return _make_error(None, -32600, "Invalid Request")
    method = req.get("method")
    params = req.get("params", {}) or {}
    id_ = req.get("id")
    is_notification = id_ is None

    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "pandaone", "version": "0.6.0"},
        }
        return _make_response(id_, result) if not is_notification else None

    elif method == "notifications/initialized":
        # 客户端通知：已初始化。不需要响应
        return None

    elif method == "tools/list":
        result = {"tools": TOOLS}
        return _make_response(id_, result) if not is_notification else None

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {}) or {}
        if tool_name not in HANDLERS:
            return _make_error(id_, -32602, f"Unknown tool: {tool_name}")

        try:
            handler_result = HANDLERS[tool_name](arguments)
            rc = handler_result.get("returncode", 0)
            stdout = handler_result.get("stdout", "")
            stderr = handler_result.get("stderr", "")

            content = []
            if stdout:
                content.append({"type": "text", "text": stdout})
            if stderr:
                content.append({"type": "text", "text": f"[stderr] {stderr}"})

            result = {
                "content": content,
                "isError": rc != 0,
            }
            return _make_response(id_, result) if not is_notification else None
        except Exception as e:
            return _make_error(id_, -32603, f"Internal error: {e}")

    elif method == "ping":
        return _make_response(id_, {}) if not is_notification else None

    else:
        return _make_error(id_, -32601, f"Method not found: {method}")


# ============================================================
# stdio 主循环
# ============================================================
def serve_stdio():
    """stdio JSON-RPC 2.0 服务器主循环"""
    # 不缓冲 stdout，确保 JSON-RPC 消息立即到达客户端
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            err_resp = _make_error(None, -32700, "Parse error", str(e))
            sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue

        resp = _handle_request(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def main():
    serve_stdio()


if __name__ == "__main__":
    main()