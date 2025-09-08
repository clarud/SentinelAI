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
import requests

def _warmup(base_url: str, timeout_s: float = 10):
    try:
        resp = requests.get(f"{base_url}/health", timeout=timeout_s)
        if resp.status_code == 200:
            print("✅ Warmed up:", resp.json())
        else:
            print("⚠️ Warmup failed:", resp.status_code, resp.text)
    except Exception as e:
        print("⚠️ Warmup error:", e)

import asyncio

async def _retry_connect(url, max_retries=3, delay=2):
    for attempt in range(max_retries):
        try:
            return await websockets.connect(url, ping_interval=None, max_size=2**24)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"⚠️ Connect failed ({e}), retrying in {delay}s...")
            await asyncio.sleep(delay)


async def _acall(url: str, tool: str, args: Dict[str, Any], timeout_s: float) -> Dict[str, Any]:
    # Warm up service
    base_url = url.replace("wss://", "https://").replace("ws://", "http://").rstrip("/ws")
    _warmup(base_url)

    async with await _retry_connect(url) as ws:
        req = {"type": "call_tool", "name": tool, "arguments": args}
        await ws.send(json.dumps(req))

        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout_s)
        except asyncio.TimeoutError:
            return {"error": f"Timeout after {timeout_s}s"}

        try:
            resp = json.loads(raw)
        except Exception as e:
            raise RuntimeError(f"Invalid JSON from server: {raw} ({e})")

        if resp.get("type") != "tool_result":
            raise RuntimeError(f"Bad MCP response: {resp}")
        if not resp.get("ok", False):
            raise RuntimeError(f"Tool {tool} failed: {resp.get('error')}")
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
