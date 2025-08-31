#!/usr/bin/env python3
"""
Test client for RAG tools WebSocket server.
Tests both call_rag and store_rag functionality.
"""

import asyncio
import json
import websockets
import uuid

class RAGToolsTestClient:
    def __init__(self, server_url="ws://localhost:7031"):
        self.server_url = server_url

    async def connect_and_test(self):
        """Connect to server and run all tests"""
        try:
            async with websockets.connect(self.server_url) as websocket:
                print(f"✅ Connected to RAG tools server at {self.server_url}")
                
                # Test 1: List available tools
                await self.test_list_tools(websocket)
                
                # Test 2: Store some mock data
                await self.test_store_rag(websocket)
                
                # Test 3: Query the stored data
                await self.test_call_rag(websocket)
                
                print("\n🎉 All tests completed successfully!")
                
        except ConnectionRefusedError:
            print(f"❌ Failed to connect to server at {self.server_url}")
            print("Make sure the RAG tools server is running:")
            print("cd services/mcp/rag-tools && python server.py")
        except Exception as e:
            print(f"❌ Test failed with error: {e}")

    async def test_list_tools(self, websocket):
        """Test listing available tools"""
        print("\n🧪 Test 1: List Tools")
        
        request = {"type": "list_tools"}
        await websocket.send(json.dumps(request))
        
        response = json.loads(await websocket.recv())
        print(f"Response: {response}")
        
        assert response["type"] == "tools"
        assert "rag.query" in response["tools"]
        assert "rag.store" in response["tools"]
        print("✅ Tool listing works correctly")

    async def test_store_rag(self, websocket):
        """Test storing mock fraud detection data"""
        print("\n🧪 Test 2: Store RAG Data")
        
        # Mock fraud detection data
        mock_data = [
            {
                "text": "URGENT: Your account has been compromised! Click here to verify your identity immediately.",
                "is_scam": "scam",
                "confidence_level": 0.95,
                "scam_probability": 0.98
            },
            {
                "text": "Hi John, thanks for your purchase. Your order #12345 will be shipped tomorrow.",
                "is_scam": "not_scam",
                "confidence_level": 0.87,
                "scam_probability": 0.02
            },
            {
                "text": "Congratulations! You've won $1,000,000! Send us your bank details to claim your prize.",
                "is_scam": "scam",
                "confidence_level": 0.99,
                "scam_probability": 0.99
            }
        ]
        
        for i, data in enumerate(mock_data):
            request = {
                "type": "call_tool",
                "name": "rag.store",
                "arguments": {"output": data}
            }
            
            await websocket.send(json.dumps(request))
            response = json.loads(await websocket.recv())
            
            print(f"Stored record {i+1}: {response}")
            assert response["ok"] == True
        
        print("✅ All mock data stored successfully")

    async def test_call_rag(self, websocket):
        """Test querying stored data"""
        print("\n🧪 Test 3: Query RAG Data")
        
        # Test queries
        test_queries = [
            "urgent account security issue",
            "order shipment notification", 
            "lottery winner prize money"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            
            request = {
                "type": "call_tool", 
                "name": "rag.query",
                "arguments": {"text": query}
            }
            
            await websocket.send(json.dumps(request))
            response = json.loads(await websocket.recv())
            
            print(f"Response: {response}")
            assert response["ok"] == True
            
            results = response["data"]
            print(f"Found {len(results)} similar records:")
            
            for i, result in enumerate(results[:3]):  # Show top 3
                print(f"  {i+1}. Text: {result['text'][:60]}...")
                print(f"     Is Scam: {result['is_scam']}")
                print(f"     Confidence: {result['confidence_level']}")
                print(f"     Scam Probability: {result['scam_probability']}")
        
        print("✅ Query functionality works correctly")

async def main():
    """Run the test suite"""
    print("🚀 Starting RAG Tools Test Suite")
    print("=" * 50)
    
    client = RAGToolsTestClient()
    await client.connect_and_test()

if __name__ == "__main__":
    asyncio.run(main())
