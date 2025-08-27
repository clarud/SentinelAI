import time
import os
import base64
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest
from app.services.firestore_services import get_tokens, create_credentials_from_dict, update_watch_expiration
from app.api.routers.gmail_oauth import get_gmail_service

router = APIRouter()

class GmailWatcher:
    def __init__(self, user_email: str):
        self.user_email = user_email
        self.service = None
        
    def _get_service(self):
        """Get authenticated Gmail service with token refresh"""
        if self.service:
            return self.service
            
        token_data = get_tokens(self.user_email)
        if not token_data:
            raise Exception("No tokens found for user")
            
        credentials = create_credentials_from_dict(token_data)
        
        # Refresh token if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            # Update stored tokens
            token_data.update({
                'access_token': credentials.token,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            })
            from app.services.firestore_services import store_tokens
            store_tokens(self.user_email, token_data)
        
        self.service = build("gmail", "v1", credentials=credentials)
        return self.service
    
    def start_watch(self, topic_name: str):
        """Start watching for email changes"""
        service = self._get_service()
        
        request = {
            'labelIds': ['INBOX'],
            'topicName': topic_name,
            'labelFilterAction': 'include'
        }
        
        try:
            response = service.users().watch(userId='me', body=request).execute()
            expiration = response.get('expiration', int(time.time() * 1000) + 3600000)
            
            update_watch_expiration(self.user_email, expiration)
            return {
                'status': 'watching',
                'expiration': expiration,
                'historyId': response.get('historyId')
            }
        except Exception as e:
            raise Exception(f"Failed to start watch: {e}")
    
    def stop_watch(self):
        """Stop watching for email changes"""
        service = self._get_service()
        try:
            service.users().stop(userId='me').execute()
            update_watch_expiration(self.user_email, 0)
            return {'status': 'stopped'}
        except Exception as e:
            raise Exception(f"Failed to stop watch: {e}")
    
    def get_email(self, message_id: str):
        """Fetch email content by message ID"""
        service = self._get_service()
        try:
            message = service.users().messages().get(
                userId='me', 
                id=message_id,
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date', 'To']
            ).execute()
            
            headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
            
            return {
                'id': message_id,
                'from': headers.get('From', ''),
                'subject': headers.get('Subject', ''),
                'date': headers.get('Date', ''),
                'to': headers.get('To', ''),
                'snippet': message.get('snippet', ''),
                'threadId': message.get('threadId', '')
            }
        except Exception as e:
            raise Exception(f"Failed to get email: {e}")
        
    def get_email_details(self, message_id: str):
        """Fetch complete email content including body, subject, and sender"""
        service = self._get_service()
        try:
            # Get full email content with body
            message = service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'  # Changed from 'metadata' to 'full' to get body content
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
            
            # Extract email body content
            email_body = self._extract_email_body(message.get('payload', {}))
            
            return {
                'id': message_id,
                'from': headers.get('From', ''),
                'subject': headers.get('Subject', ''),
                'date': headers.get('Date', ''),
                'to': headers.get('To', ''),
                'snippet': message.get('snippet', ''),
                'threadId': message.get('threadId', ''),
                'body': email_body,
                'body_preview': email_body[:200] + '...' if len(email_body) > 200 else email_body
            }
        except Exception as e:
            raise Exception(f"Failed to get email: {e}")
        
    def _extract_email_body(self, payload: dict) -> str:
        """Recursively extract email body content from payload"""
        body = ""
        
        # If the payload has parts (multipart email), recursively check them
        if 'parts' in payload:
            for part in payload['parts']:
                body += self._extract_email_body(part)
        
        # If this part has a body and is text content
        if 'body' in payload and 'data' in payload['body']:
            mime_type = payload.get('mimeType', '')
            
            # Only process text content
            if mime_type.startswith('text/plain') or mime_type.startswith('text/html'):
                try:
                    # Decode base64 encoded email body
                    body_data = payload['body']['data']
                    decoded_bytes = base64.urlsafe_b64decode(body_data)
                    body += decoded_bytes.decode('utf-8', errors='ignore') + "\n\n"
                except Exception as e:
                    print(f"Error decoding body: {e}")
        
        return body.strip()

@router.post("/start-watch/{user_email}")
def start_watch(user_email: str):
    """Start watching user's inbox"""
    try:
        watcher = GmailWatcher(user_email)
        topic_name = os.getenv("PUBSUB_TOPIC", "projects/your-project/topics/gmail-notifications")
        result = watcher.start_watch(topic_name)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stop-watch/{user_email}")
def stop_watch(user_email: str):
    """Stop watching user's inbox"""
    try:
        watcher = GmailWatcher(user_email)
        result = watcher.stop_watch()
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/notifications")
async def handle_notification(request: dict):
    """Handle Gmail push notifications and print email details"""
    try:
        print(f"📨 Received notification: {json.dumps(request, indent=2)[:500]}...")
        
        # Check for subscription verification
        if request.get('challenge'):
            print("✅ Subscription verification challenge received")
            return JSONResponse({"challenge": request['challenge']})
        
        # Parse Pub/Sub message
        message = request.get('message', {})
        message_id = message.get('messageId')
        data = message.get('data', '')
        
        if not data:
            print("⚠️ No data in message")
            return JSONResponse({"status": "no data"})
        
        # Decode and parse notification
        try:
            decoded_data = base64.b64decode(data).decode('utf-8')
            notification = json.loads(decoded_data)
        except Exception as e:
            print(f"❌ Failed to decode notification: {e}")
            return JSONResponse({"status": "decode_error"})
        
        email_address = notification.get('emailAddress')
        history_id = notification.get('historyId')
        
        print(f"📧 Notification for {email_address}, historyId: {history_id}")
        
        # Process the email to get full details
        try:
            watcher = GmailWatcher(email_address)
            service = watcher._get_service()
            
            # Instead of using history API (which can be unreliable for recent messages),
            # let's get the most recent messages directly
            print("🔍 Checking for recent messages...")
            
            # Get the list of recent messages
            response = service.users().messages().list(
                userId='me',
                maxResults=5,  # Check last 5 messages
                labelIds=['INBOX']
            ).execute()
            
            messages = response.get('messages', [])
            
            if not messages:
                print("ℹ️ No recent messages found in inbox")
                return JSONResponse({"status": "no_recent_messages"})
            
            print(f"📥 Found {len(messages)} recent messages")
            
            # Process each recent message
            for msg in messages:
                message_id = msg['id']
                
                try:
                    # Get FULL email details including body
                    email_data = watcher.get_email_details(message_id)
                    
                    # Check if this message is recent (within last 5 minutes)
                    print(f"📋 Processing message: {email_data['subject']}")
                    
                    # Print all email details
                    print("\n" + "="*60)
                    print("📧 EMAIL DETAILS")
                    print("="*60)
                    print(f"From: {email_data['from']}")
                    print(f"To: {email_data['to']}")
                    print(f"Subject: {email_data['subject']}")
                    print(f"Date: {email_data['date']}")
                    print(f"Message ID: {email_data['id']}")
                    print("-"*40)
                    print("BODY PREVIEW:")
                    print(email_data['body_preview'])
                    print("-"*40)
                    print("FULL BODY (first 500 chars):")
                    print(email_data['body'][:500] + "..." if len(email_data['body']) > 500 else email_data['body'])
                    print("="*60 + "\n")
                    
                except Exception as email_error:
                    print(f"⚠️ Error processing message {message_id}: {email_error}")
                    continue
            
            # Also try the history approach for completeness
            try:
                print("🔄 Also trying history API approach...")
                history = service.users().history().list(
                    userId='me',
                    startHistoryId=history_id,
                    historyTypes=['messageAdded']
                ).execute()
                
                history_items = history.get('history', [])
                print(f"📊 History API returned {len(history_items)} items")
                
            except Exception as history_error:
                print(f"⚠️ History API error: {history_error}")
        
        except Exception as processing_error:
            print(f"❌ Error processing notification: {processing_error}")
            # Continue to acknowledge anyway
        
        return JSONResponse({
            "status": "processed",
            "message_id": message_id,
            "email": email_address,
            "history_id": history_id
        })
        
    except Exception as e:
        print(f"❌ Notification error: {e}")
        return JSONResponse({"status": "error", "error": str(e)})

@router.get("/test-email/{user_email}/{message_id}")
def test_email_fetch(user_email: str, message_id: str):
    """Test endpoint to fetch a specific email"""
    try:
        watcher = GmailWatcher(user_email)
        email_data = watcher.get_email(message_id)
        return JSONResponse(email_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))