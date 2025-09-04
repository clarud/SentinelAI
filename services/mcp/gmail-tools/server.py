import os
import json
import asyncio
import websockets
import sys

# Add the services path to Python path to access shared modules
services_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'services'))
sys.path.append(services_path)

from tools.gmail_tools import modify_labels, mark_as_scam

PORT = int(os.getenv("PORT", "7032"))

TOOLS = {
    "gmail.markAsScam": lambda args: mark_as_scam(args["user_email"], args["message_id"]),
    "gmail.modifyLabels": lambda args: modify_labels(args["user_email"], args["message_id"], args.get("add_labels"), args.get("remove_labels")),
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
    async with websockets.serve(handle, "localhost", PORT):
        print(f"Gmail Tools MCP server running on ws://localhost:{PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
