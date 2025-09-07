# Centralized MCP server with FastAPI WebSocket support for all tool types

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import json
import asyncio

from mcp.data_processor.tools.process_email import process_email
from mcp.data_processor.tools.process_pdf import process_pdf
from mcp.extraction_tools.tools.extract_link import extract_link
from mcp.extraction_tools.tools.extract_number import extract_number
from mcp.extraction_tools.tools.extract_organisation import extract_organisation
from mcp.gmail_tools.tools.gmail_tools import mark_as_scam
from mcp.gmail_tools.tools.google_drive_tool import create_and_upload_analysis_pdf
from mcp.gmail_tools.tools.firestore_tools import store_analysis_data
from mcp.rag_tools.tools.call_rag import call_rag
from mcp.rag_tools.tools.store_rag import store_rag

PORT = int(os.getenv("PORT", "7030"))

app = FastAPI(
    title="SentinelAI MCP Server",
    description="Model Context Protocol server with FastAPI WebSocket support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized tool registry with proper namespacing
TOOLS = {
    # Data processor tools
    "process_email": lambda args: process_email(args["document"]),
    "process_pdf": lambda args: process_pdf(args["document"]),

    # Extraction tools
    "extract_link": lambda args: extract_link(args["text"]),
    "extract_number": lambda args: extract_number(args["text"]),
    "extract_organisation": lambda args: extract_organisation(args["text"]),

    #Gmail tools
    "mark_as_scam": lambda args: mark_as_scam(args["user_email"], args["message_id"]),
    "create_analysis_pdf": lambda args: create_and_upload_analysis_pdf(
        args["user_email"], 
        args["message_id"], 
        args["analysis_data"], 
        args.get("title", "Email Fraud Analysis")
    ),
    "store_analysis_data": lambda args: store_analysis_data(args["data"]),
    
    # RAG tools
    "call_rag": lambda args: call_rag(args["document"]),
    "store_rag": lambda args: store_rag(args["output"]),
}

# Health check endpoints
@app.get("/")
async def health_check():
    return {"status": "ok", "service": "SentinelAI MCP Server"}

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "tools_available": len(TOOLS),
        "tools": list(TOOLS.keys())
    }

@app.get("/tools")
async def list_tools():
    return {"tools": list(TOOLS.keys())}

# WebSocket endpoint for MCP protocol
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket client connected")
    
    try:
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                req = json.loads(data)

                if req.get("type") == "list_tools":
                    await websocket.send_text(json.dumps({
                        "type": "tools",
                        "tools": list(TOOLS.keys())
                    }))
                    continue

                if req.get("type") == "call_tool":
                    name = req.get("name")
                    args = req.get("arguments", {})
                    
                    if name not in TOOLS:
                        await websocket.send_text(json.dumps({
                            "type": "tool_result",
                            "ok": False,
                            "error": f"unknown tool: {name}"
                        }))
                        continue
                    
                    try:
                        result = TOOLS[name](args)
                        await websocket.send_text(json.dumps({
                            "type": "tool_result",
                            "ok": True,
                            "data": result
                        }))
                    except Exception as tool_error:
                        await websocket.send_text(json.dumps({
                            "type": "tool_result",
                            "ok": False,
                            "error": f"tool execution failed: {str(tool_error)}"
                        }))
                    continue

                # Unknown request type
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"unknown request type: {req.get('type')}"
                }))
                
            except json.JSONDecodeError as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"invalid JSON: {str(e)}"
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"server error: {str(e)}"
                }))
                break
                
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print("WebSocket connection closed")

if __name__ == "__main__":
    import uvicorn
    print(f"Starting SentinelAI MCP Server on port {PORT}")
    print(f"Available tools: {list(TOOLS.keys())}")
    print(f"WebSocket endpoint: ws://localhost:{PORT}/ws")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
