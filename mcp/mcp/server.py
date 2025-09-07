# Centralized MCP server with WebSocket support for all tool types

import os
import sys
import json
import asyncio
import websockets

# Add the MCP directory to Python path to find the tool modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import all tools from different modules using correct paths
sys.path.insert(0, os.path.join(current_dir, 'data-processor'))
sys.path.insert(0, os.path.join(current_dir, 'extraction-tools'))
sys.path.insert(0, os.path.join(current_dir, 'gmail-tools'))
sys.path.insert(0, os.path.join(current_dir, 'rag-tools'))

from tools.process_email import process_email
from tools.process_pdf import process_pdf
from tools.extract_link import extract_link
from tools.extract_number import extract_number
from tools.extract_organisation import extract_organisation
from tools.classify_email import classify_email
from tools.send_report_to_drive import send_report_to_drive
from tools.call_rag import call_rag
from tools.store_rag import store_rag

PORT = int(os.getenv("PORT", "7030"))

# Centralized tool registry with proper namespacing
TOOLS = {
    # Data processor tools
    "data-processor.process_email": lambda args: process_email(args["document"]),
    "data-processor.process_pdf": lambda args: process_pdf(args["document"]),
    
    # Extraction tools
    "extraction-tools.extract_link": lambda args: extract_link(args["text"]),
    "extraction-tools.extract_number": lambda args: extract_number(args["text"]),
    "extraction-tools.extract_organisation": lambda args: extract_organisation(args["text"]),
    
    # Gmail tools
    "gmail-tools.classify_email": lambda args: classify_email(args["email_data"]),
    "gmail-tools.send_report_to_drive": lambda args: send_report_to_drive(args["report_data"]),
    
    # RAG tools
    "rag-tools.call_rag": lambda args: call_rag(args["document"]),
    "rag-tools.store_rag": lambda args: store_rag(args["output"]),
}

async def handle(ws):
    """Handle WebSocket connections and route requests to appropriate tools."""
    async for raw in ws:
        try:
            req = json.loads(raw)
            
            if req.get("type") == "list_tools":
                # Return all available tools
                await ws.send(json.dumps({
                    "type": "tools", 
                    "tools": list(TOOLS.keys())
                }))
                continue
                
            if req.get("type") == "call_tool":
                name = req.get("name")
                args = req.get("arguments", {})
                
                # Check if tool exists
                if name not in TOOLS:
                    await ws.send(json.dumps({
                        "type": "tool_result", 
                        "ok": False, 
                        "error": f"unknown tool: {name}"
                    }))
                    continue
                
                # Execute the tool
                try:
                    data = TOOLS[name](args)
                    await ws.send(json.dumps({
                        "type": "tool_result", 
                        "ok": True, 
                        "data": data
                    }))
                except Exception as tool_error:
                    await ws.send(json.dumps({
                        "type": "tool_result", 
                        "ok": False, 
                        "error": f"tool execution failed: {str(tool_error)}"
                    }))
                continue
            
            # Unknown request type
            await ws.send(json.dumps({
                "type": "error", 
                "message": f"unknown request type: {req.get('type')}"
            }))
            
        except json.JSONDecodeError as e:
            await ws.send(json.dumps({
                "type": "error", 
                "message": f"invalid JSON: {str(e)}"
            }))
        except Exception as e:
            await ws.send(json.dumps({
                "type": "error", 
                "message": f"server error: {str(e)}"
            }))

async def main():
    """Start the centralized MCP server."""
    print(f"[mcp-centralized] ws://0.0.0.0:{PORT}")
    print("Available tools:")
    for tool_name in TOOLS.keys():
        print(f"  - {tool_name}")
    
    async with websockets.serve(handle, "0.0.0.0", PORT, ping_interval=None):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())