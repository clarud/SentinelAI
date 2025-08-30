# RAG Tools Test

This directory contains test cases for the RAG tools WebSocket server.

## Setup

1. **Install dependencies:**
   ```bash
   pip install websockets
   ```

2. **Set environment variables:**
   ```bash
   export PINECONE_API_KEY="your-api-key"
   export PINECONE_INDEX_HOST="your-index-host"
   ```

3. **Start the RAG tools server:**
   ```bash
   cd services/mcp/rag-tools
   python server.py
   ```

4. **Run the tests:**
   ```bash
   cd test/mcp
   python test_rag_tools.py
   ```

## Test Cases

- **Test 1:** List available tools (`rag.query`, `rag.store`)
- **Test 2:** Store mock fraud detection data with scam labels
- **Test 3:** Query stored data using semantic search

The test uses mock data including:
- Phishing/scam messages
- Legitimate messages
- Lottery scam examples

Each test verifies the WebSocket communication and tool functionality.
