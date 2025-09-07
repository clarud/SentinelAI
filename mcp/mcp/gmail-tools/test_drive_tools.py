#!/usr/bin/env python3
"""
Test script for Google Drive Tools
Tests PDF creation and upload functionality
"""

import asyncio
import websockets
import json
import sys

async def test_drive_tools():
    """Test the Google Drive Tools via MCP server"""
    uri = "ws://localhost:7032"
    
    # Sample analysis data (like what would come from fraud detection)
    sample_analysis = {
        "email_analysis": {
            "message_id": "test_message_123",
            "fraud_score": 0.85,
            "risk_level": "HIGH",
            "detected_issues": [
                "Suspicious sender domain",
                "Phishing keywords detected",
                "Urgent language patterns"
            ],
            "sender_info": {
                "email": "suspicious@fake-bank.com",
                "domain_age": "2 days",
                "reputation": "BLACKLISTED"
            },
            "content_analysis": {
                "suspicious_links": [
                    "http://fake-bank-login.ru/secure",
                    "http://phishing-site.tk/verify"
                ],
                "attachment_analysis": "No attachments",
                "language_analysis": "Urgent, threatening tone detected"
            },
            "recommendation": "BLOCK AND QUARANTINE",
            "confidence": "95%"
        },
        "metadata": {
            "analysis_timestamp": "2025-09-05T10:30:00Z",
            "model_version": "SentinelAI-v2.1",
            "processing_time_ms": 1250
        }
    }
    
    try:
        print("Connecting to Gmail Tools MCP server (with Drive tools)...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Get user input
            user_email = input("Enter your Gmail address: ").strip()
            if not user_email:
                print("No email provided, exiting...")
                return
                
            message_id = input("Enter a message ID (or press Enter for test ID): ").strip()
            if not message_id:
                message_id = "test_message_" + str(int(asyncio.get_event_loop().time()))
            
            # Test 1: List available tools
            print("\n1. Listing available tools...")
            await websocket.send(json.dumps({"type": "list_tools"}))
            response = await websocket.recv()
            tools_response = json.loads(response)
            print(f"Available tools: {tools_response.get('tools', [])}")
            
            # Test 2: Upload analysis to Google Drive
            print(f"\n2. Testing Google Drive PDF upload for {user_email}...")
            print(f"   Message ID: {message_id}")
            
            drive_request = {
                "type": "call_tool",
                "name": "drive.uploadAnalysis",
                "arguments": {
                    "user_email": user_email,
                    "message_id": message_id,
                    "analysis_data": sample_analysis,
                    "title": "Fraud Detection Analysis Report"
                }
            }
            
            print("Sending request...")
            await websocket.send(json.dumps(drive_request))
            response = await websocket.recv()
            result = json.loads(response)
            
            print("Response received:")
            print(json.dumps(result, indent=2))
            
            if result.get("ok"):
                data = result.get("data", {})
                if data.get("status") == "success":
                    print(f"\n✅ Success! PDF uploaded to Google Drive")
                    print(f"Drive Link: {data.get('drive_link')}")
                    print(f"Filename: {data.get('filename')}")
                    print("The analysis PDF is now available in your Google Drive!")
                else:
                    print(f"\n❌ Upload failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"\n❌ Tool call failed: {result.get('error', 'Unknown error')}")
                
    except ConnectionRefusedError:
        print("\n❌ Error: Could not connect to MCP server")
        print("Make sure the server is running:")
        print("  cd services/mcp/gmail-tools")
        print("  python server.py")
    except Exception as e:
        print(f"\n❌ Error testing Google Drive Tools: {e}")

def test_direct_pdf_creation():
    """Test PDF creation directly without MCP server"""
    print("\nDirect PDF Creation Test")
    print("=" * 30)
    
    try:
        from tools.google_drive_tool import create_pdf_from_dict
        
        # Sample data
        test_data = {
            "analysis_result": "This email is likely a phishing attempt",
            "confidence": 0.95,
            "risk_factors": ["suspicious_domain", "urgent_language", "credential_request"],
            "recommendation": "Block and quarantine"
        }
        
        # Create PDF
        pdf_buffer = create_pdf_from_dict(test_data, "Test Analysis")
        
        # Save to file for inspection
        with open("test_analysis.pdf", "wb") as f:
            f.write(pdf_buffer.getvalue())
            
        print("✅ PDF created successfully: test_analysis.pdf")
        print("You can open this file to see how the analysis data is formatted")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install required packages: pip install reportlab")
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")

async def main():
    print("Google Drive Tools Test Suite")
    print("=" * 40)
    print("This script tests the Google Drive PDF upload functionality")
    print()
    
    print("Choose test method:")
    print("1. Test via MCP server (end-to-end)")
    print("2. Test PDF creation only (direct)")
    print("3. Both")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice in ["2", "3"]:
        test_direct_pdf_creation()
        print()
    
    if choice in ["1", "3"]:
        await test_drive_tools()

if __name__ == "__main__":
    asyncio.run(main())
