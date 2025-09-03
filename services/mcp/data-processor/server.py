# Document processing MCP server with WebSocket support

import os
import json
import asyncio
import websockets
from tools.process_email import process_email
from tools.process_pdf import process_pdf

PORT = int(os.getenv("PORT", "7032"))

TOOLS = {
    "email.process": lambda args: process_email(args["document"]),
    "pdf.process": lambda args: process_pdf(args["document"]),
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
    print(f"[data-processor] ws://0.0.0.0:{PORT}")
    async with websockets.serve(handle, "0.0.0.0", PORT, ping_interval=None):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())