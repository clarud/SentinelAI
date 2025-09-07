# Extraction tools MCP server with WebSocket support

import os
import json
import asyncio
import websockets
from tools.extract_link import extract_link
from tools.extract_number import extract_number
from tools.extract_organisation import extract_organisation

PORT = int(os.getenv("PORT", "7033"))

TOOLS = {
    "extract_link": lambda args: extract_link(args["text"]),
    "extract_number": lambda args: extract_number(args["text"]),
    "extract_organisation": lambda args: extract_organisation(args["text"]),
}

async def handle(ws):
    async for raw in ws:
        try:
            req = json.loads(raw)
            if req.get("type") == "list_tools":
                await ws.send(json.dumps({"type": "tools", "tools": list(TOOLS.keys())}))
                continue
            if req.get("type") == "call_tool":
                name = req.get("name")
                args = req.get("arguments", {})
                if name not in TOOLS:
                    await ws.send(json.dumps({"type": "tool_result", "ok": False, "error": "unknown tool"}))
                    continue
                data = TOOLS[name](args)
                await ws.send(json.dumps({"type": "tool_result", "ok": True, "data": data}))
                continue
            await ws.send(json.dumps({"type": "error", "message": "unknown request"}))
        except Exception as e:
            await ws.send(json.dumps({"type": "tool_result", "ok": False, "error": str(e)}))

async def main():
    print(f"[extraction-tools] ws://0.0.0.0:{PORT}")
    async with websockets.serve(handle, "0.0.0.0", PORT, ping_interval=None):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
