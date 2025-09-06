#!/usr/bin/env python3

"""
Test script for the document processing MCP WebSocket server.
"""

import asyncio
import json
import websockets


async def test_mcp_websocket_server():
    """Test the MCP WebSocket server communication."""
    print("=== Testing MCP WebSocket Server ===")
    
    # Connect to the WebSocket server
    uri = "ws://localhost:7032"
    
    try:
        async with websockets.connect(uri) as websocket:
            
            # Test 1: List tools
            list_request = {"type": "list_tools"}
            await websocket.send(json.dumps(list_request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print("Test 1 - List tools:")
            print(json.dumps(response_data, indent=2))
            print()
            
            # Test 2: Call email processing tool
            email_request = {
                "type": "call_tool",
                "name": "email.process",
                "arguments": {
                    "document": {
                        "subject": "Phishing Alert",
                        "sender": "attacker@fake-bank.com",
                        "text": "Your account has been suspended. Click here to reactivate: http://evil-site.com"
                    }
                }
            }
            
            await websocket.send(json.dumps(email_request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print("Test 2 - Call email.process:")
            print(json.dumps(response_data, indent=2))
            print()
            
            # Test 3: Call PDF processing tool
            pdf_request = {
                "type": "call_tool",
                "name": "pdf.process",
                "arguments": {
                    "document": "This is a PDF document with suspicious content about winning lottery prizes."
                }
            }
            
            await websocket.send(json.dumps(pdf_request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print("Test 3 - Call pdf.process:")
            print(json.dumps(response_data, indent=2))
            print()
            
            # Test 4: Invalid tool call
            invalid_request = {
                "type": "call_tool",
                "name": "invalid.tool",
                "arguments": {}
            }
            
            await websocket.send(json.dumps(invalid_request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print("Test 4 - Invalid tool (expected error):")
            print(json.dumps(response_data, indent=2))
            print()
            
    except ConnectionRefusedError:
        print("Error: Could not connect to WebSocket server at ws://localhost:7032")
        print("Make sure the server is running with: python server.py")
        return
        
    print("MCP WebSocket server tests completed!")


if __name__ == "__main__":
    asyncio.run(test_mcp_websocket_server())
