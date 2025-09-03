"""
Tiny MCP client with a minimal WS protocol.
Request:  {"type":"call_tool","name":"<tool>","arguments":{...}}
Response: {"type":"tool_result","ok":true,"data":{...}} or {"type":"tool_result","ok":false,"error":"..."}
"""
from __future__ import annotations
import asyncio, json
from typing import Any, Dict
import websockets
from .registry import MCP_SERVERS

async def _acall(url: str, tool: str, args: Dict[str, Any], timeout_s: float) -> Dict[str, Any]:
    async with websockets.connect(url, ping_interval=None, max_size=2**24) as ws:
        req = {"type": "call_tool", "name": tool, "arguments": args}
        await ws.send(json.dumps(req))
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout_s)
        resp = json.loads(raw)
        if resp.get("type") != "tool_result":
            raise RuntimeError(f"Bad MCP response type: {resp.get('type')}")
        if not resp.get("ok", False):
            raise RuntimeError(resp.get("error", "tool failed"))
        return resp.get("data", {})

def call_tool(server_key: str, tool: str, **kwargs) -> Dict[str, Any]:
    cfg = MCP_SERVERS[server_key]
    url, timeout_s = cfg["url"], float(cfg.get("timeout", 3.0))
    return asyncio.run(_acall(url, tool, kwargs, timeout_s))

# Optional: list tools
async def _alist(url: str, timeout_s: float):
    async with websockets.connect(url, ping_interval=None) as ws:
        await ws.send(json.dumps({"type":"list_tools"}))
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout_s)
        return json.loads(raw)

def list_tools(server_key: str):
    cfg = MCP_SERVERS[server_key]
    return asyncio.run(_alist(cfg["url"], float(cfg.get("timeout", 3.0))))
