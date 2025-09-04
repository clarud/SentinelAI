# Gmail Tools MCP Server

This Model Context Protocol (MCP) server provides Gmail label manipulation tools for the SentinelAI fraud detection system.

## Overview

The Gmail Tools server is designed specifically for fraud detection scenarios where emails identified as scams need to be automatically labeled and moved out of the inbox.

## Features

### Primary Tool: `gmail.markAsScam`
- Marks an email as scam by adding a "SCAM" label
- Removes the email from the INBOX
- Creates the SCAM label if it doesn't exist (red background for visibility)

### Fallback Tool: `gmail.modifyLabels`
- **Default behavior**: If no labels specified, marks email as scam (same as markAsScam)
- **Custom behavior**: Allows specifying custom labels to add/remove

## Usage

### For AI Agent (Primary Use Case)
When the fraud detection model determines an email is a scam:

```json
{
  "type": "call_tool",
  "name": "gmail.markAsScam", 
  "arguments": {
    "user_email": "user@example.com",
    "message_id": "email_message_id"
  }
}
```

### Default Behavior Example
Calling `gmail.modifyLabels` without any label arguments will default to scam marking:

```json
{
  "type": "call_tool",
  "name": "gmail.modifyLabels",
  "arguments": {
    "user_email": "user@example.com", 
    "message_id": "email_message_id"
  }
}
```

## Architecture

```
services/
├── api/
│   └── app/
│       ├── services/
│       │   └── firestore_services.py    # Shared authentication
│       └── api/routers/
│           └── gmail_watch.py           # Gmail API integration
└── mcp/
    └── gmail-tools/
        ├── server.py                    # MCP server
        ├── tools/
        │   └── gmail_tools.py          # Scam marking logic
        ├── test_client.py              # Test script
        └── requirements.txt
```

## Setup

1. Install dependencies:
   ```bash
   cd services/mcp/gmail-tools
   pip install -r requirements.txt
   ```

2. Ensure Gmail API credentials are configured (shared with main API service)

3. Start the server:
   ```bash
   python server.py
   ```

4. The server runs on `ws://localhost:7032`

## Integration

The server is registered in the worker's tool registry:

```python
# services/worker/worker/tools/registry.py
MCP_SERVERS = {
    "gmail-tools": {
        "url": "ws://localhost:7032",
        "timeout": 3.0,
    },
}
```

## Testing

Run the test client to verify functionality:

```bash
python test_client.py
```

## Security Notes

- Uses existing Gmail OAuth tokens from Firestore
- Requires Gmail API scopes: `gmail.modify`
- Only operates on emails the user has already authorized access to
- Creates visible SCAM labels for user transparency
