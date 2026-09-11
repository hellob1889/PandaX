"""
04_mcp_client.py
================
Pandaone AI Agent MCP 协议客户端 demo

演示：作为 AI Agent，通过 stdio JSON-RPC 调用 pandaone_mcp server。
任何 MCP 客户端（Claude/Cursor/Trae）都能复用此逻辑。
"""
import json
import subprocess
import sys
from pathlib import Path


def call_mcp(proc, method, params=None, id_=1):
    """发送 JSON-RPC 请求并接收响应"""
    payload = {"jsonrpc": "2.0", "method": method, "id": id_}
    if params is not None:
        payload["params"] = params
    proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    return json.loads(line) if line else {}


def banner(msg):
    print("\n" + "=" * 60)
    print(f"  {msg}")
    print("=" * 60)


def main():
    project_root = sys.argv[1] if len(sys.argv) > 1 else "demo_04_mcp"
    project_root = str(Path(project_root).resolve())

    print(f"\n[Demo] Pandaone MCP Client")
    print(f"  Project: {project_root}\n")

    # 启动 MCP server
    print("[1] 启动 pandaone-mcp server (stdio JSON-RPC)...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "pandaone_mcp"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )

    try:
        # Step 1: initialize
        banner("Step 1: initialize")
        resp = call_mcp(proc, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "demo-mcp-client", "version": "1.0"},
        }, id_=1)
        server_info = resp.get("result", {}).get("serverInfo", {})
        print(f"  Server: {server_info.get('name')} v{server_info.get('version')}")

        # Step 2: tools/list
        banner("Step 2: 发现可用工具")
        resp = call_mcp(proc, "tools/list", id_=2)
        tools = resp.get("result", {}).get("tools", [])
        print(f"  发现 {len(tools)} 个工具:")
        for t in tools:
            print(f"    • {t['name']}: {t.get('description', '')[:60]}")

        # Step 3: 调用 init
        banner("Step 3: pandaone_init")
        resp = call_mcp(proc, "tools/call", {
            "name": "pandaone_init",
            "arguments": {"root": project_root},
        }, id_=3)
        content = "".join(c.get("text", "") for c in resp.get("result", {}).get("content", []))
        print(f"  Result: {content[:300]}...")

        # Step 4: 调用 write
        banner("Step 4: pandaone_write")
        # 先创建文件
        Path(project_root).mkdir(parents=True, exist_ok=True)
        main_py = Path(project_root) / "main.py"
        main_py.write_text("INITIAL = 1\n", encoding="utf-8")

        resp = call_mcp(proc, "tools/call", {
            "name": "pandaone_write",
            "arguments": {
                "root": project_root,
                "file": "main.py",
                "reason": "MCP client demo 修改",
                "problem": "演示 AI Agent 通过 MCP 写入",
                "approach": "用 pandaone_write 工具调用",
                "old": "INITIAL = 1",
                "new": "INITIAL = 2",
            },
        }, id_=4)
        content = "".join(c.get("text", "") for c in resp.get("result", {}).get("content", []))
        print(f"  Result: {content[:200]}")

        # Step 5: 查询状态
        banner("Step 5: pandaone_status")
        resp = call_mcp(proc, "tools/call", {
            "name": "pandaone_status",
            "arguments": {"root": project_root},
        }, id_=5)
        content = "".join(c.get("text", "") for c in resp.get("result", {}).get("content", []))
        # 只显示关键行
        for line in content.splitlines():
            if any(kw in line for kw in ["APPROVED", "总记录", "已锁定", "Phase"]):
                print(f"  {line.strip()}")

        # Step 6: 错误处理
        banner("Step 6: 错误处理（未知工具）")
        resp = call_mcp(proc, "tools/call", {
            "name": "nonexistent_tool",
            "arguments": {},
        }, id_=6)
        if "error" in resp:
            err = resp["error"]
            print(f"  ✓ 正确返回错误: code={err.get('code')}, msg={err.get('message')[:60]}")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

    print("\n" + "=" * 60)
    print("  ✓ Demo 4 完成 — MCP 协议工作流")
    print("=" * 60)


if __name__ == "__main__":
    main()