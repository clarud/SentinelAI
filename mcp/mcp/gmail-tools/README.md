# Gmail & Google Drive Tools MCP Server

This Model Context Protocol (MCP) server provides Gmail label manipulation and Google Drive PDF upload tools for the SentinelAI fraud detection system.

## Overview

The server provides two main functionalities:
1. **Gmail Tools**: Label emails as scam and move them out of inbox
2. **Google Drive Tools**: Create PDF reports from analysis data and upload to Google Drive

## Features

### Gmail Tools

#### Primary Tool: `gmail.markAsScam`
- Marks an email as scam by adding a "SCAM" label
- Removes the email from the INBOX
- Creates the SCAM label if it doesn't exist (red background for visibility)

#### Fallback Tool: `gmail.modifyLabels`
- **Default behavior**: If no labels specified, marks email as scam (same as markAsScam)
- **Custom behavior**: Allows specifying custom labels to add/remove

### Google Drive Tools

#### Primary Tool: `drive.uploadAnalysis`
- Converts analysis dictionary to formatted PDF
- Uploads PDF to user's Google Drive
- Stores shareable link in Firestore linked to the email
- Makes file publicly viewable (anyone with link can view)

## Usage

### Gmail Tools - For AI Agent (Primary Use Case)
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

### Google Drive Tools - For Analysis Reports
When you want to create and store a PDF report of analysis results:

```json
{
  "type": "call_tool",
  "name": "drive.uploadAnalysis",
  "arguments": {
    "user_email": "user@example.com",
    "message_id": "email_message_id",
    "analysis_data": {
      "fraud_score": 0.95,
      "risk_level": "HIGH",
      "detected_issues": ["phishing", "suspicious_links"],
      "recommendation": "BLOCK"
    },
    "title": "Email Fraud Analysis Report"
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
        ├── server.py                    # MCP server (Gmail + Drive tools)
        ├── tools/
        │   ├── gmail_tools.py          # Gmail scam marking logic
        │   └── google_drive_tool.py    # PDF creation & Drive upload
        ├── test_client.py              # Gmail tools test script
        ├── test_drive_tools.py         # Google Drive tools test script
        └── requirements.txt            # Including reportlab for PDF
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

### Gmail Tools Testing
Run the Gmail test client to verify scam labeling functionality:

```bash
python test_client.py
```

### Google Drive Tools Testing
Run the Drive test client to verify PDF creation and upload:

```bash
python test_drive_tools.py
```

### Combined Testing
Both tools can be tested together since they're served by the same MCP server.

## Required Scopes

Make sure your Google OAuth includes these scopes:
- `https://www.googleapis.com/auth/gmail.modify` (for Gmail tools)
- `https://www.googleapis.com/auth/drive.file` (for Google Drive tools)

## PDF Output Format

The Google Drive tool creates PDFs with:
- Document title and timestamp
- JSON-formatted analysis data with syntax highlighting
- Monospace font for better readability
- Automatic page breaks for long content
- Professional styling
```

## Security Notes

- Uses existing Gmail OAuth tokens from Firestore
- Requires Gmail API scopes: `gmail.modify`
- Only operates on emails the user has already authorized access to
- Creates visible SCAM labels for user transparency
