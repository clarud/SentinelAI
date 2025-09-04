import time
import os
import base64
import json
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest
from app.services.firestore_services import get_tokens, create_credentials_from_dict, update_watch_expiration, get_all_watching_users
from app.api.routers.gmail_oauth import get_gmail_service
from app.services.celery_client import celery
from app.schema import email

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
        """Start watching for email changes and store startHistoryId"""
        service = self._get_service()
        request = {
            'labelIds': ['INBOX'],
            'topicName': topic_name,
            'labelFilterAction': 'include'
        }
        try:
            response = service.users().watch(userId='me', body=request).execute()
            expiration = response.get('expiration', int(time.time() * 1000) + 3600000)
            history_id = response.get('historyId')
            update_watch_expiration(self.user_email, expiration)
            from app.services.firestore_services import update_start_history_id
            update_start_history_id(self.user_email, history_id)
            return {
                'status': 'watching',
                'expiration': expiration,
                'historyId': history_id
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

    def refresh_watch_if_needed(self):
        """Refresh watch if it's about to expire"""
        from app.services.firestore_services import get_watch_expiration
        expiration = get_watch_expiration(self.user_email)
        current_time = int(time.time() * 1000)
        
        # Refresh if no expiration or will expire in next 5 minutes
        if not expiration or current_time >= (expiration - (5 * 60 * 1000)):
            topic_name = os.getenv("PUBSUB_TOPIC")
            return self.start_watch(topic_name)
        return None
    
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
async def handle_notification(request: email.NotificationRequest):
    """Handle Gmail push notifications and print email details"""
    try:
        print(f"📨 Received notification: {json.dumps(request.model_dump(), indent=2)[:500]}...")

        # Check for subscription verification
        if request.challenge:
            print("✅ Subscription verification challenge received")
            return email.NotificationResponse(status="verified").model_dump()

        # Parse Pub/Sub message
        message = request.message
        message_id = message.message_id
        data = message.data

        if not data:
            print("⚠️ No data in message")
            return email.NotificationResponse(status="no_data").model_dump()
        
        # Decode and parse notification
        try:
            decoded_data = base64.b64decode(data).decode('utf-8')
            notification = json.loads(decoded_data)
        except Exception as e:
            print(f"❌ Failed to decode notification: {e}")
            return email.NotificationResponse(status="decode_error").model_dump()
        
        email_address = notification.get('emailAddress')
        history_id = notification.get('historyId')
        
        print(f"📧 Notification for {email_address}, historyId: {history_id}")
        
        # Process the email to get full details
        from app.services.firestore_services import get_start_history_id, update_start_history_id, store_email
        try:
            watcher = GmailWatcher(email_address)
            service = watcher._get_service()
            start_history_id = get_start_history_id(email_address)
            if not start_history_id:
                print("No startHistoryId found for user, skipping notification.")
                return email.NotificationResponse(status="no_start_history_id", email_data=None,).model_dump()

            print(f"🔄 Using startHistoryId: {start_history_id}")
            # Use Gmail history API to get only new messages
            history = service.users().history().list(
                userId='me',
                startHistoryId=start_history_id,
                historyTypes=['messageAdded']
            ).execute()
            history_items = history.get('history', [])
            print(f"📊 History API returned {len(history_items)} items")

            processed_message_ids = set()
            for item in history_items:
                messages = item.get('messagesAdded', [])
                for msg in messages:
                    msg_id = msg['message']['id']
                    if msg_id in processed_message_ids:
                        continue
                    processed_message_ids.add(msg_id)
                    try:
                        email_data = watcher.get_email_details(msg_id)
                        email_data = email.EmailData(
                            id=email_data['id'],
                            sender=email_data['from'],
                            subject=email_data['subject'],
                            date=email_data['date'],
                            to=email_data['to'],
                            snippet=email_data['snippet'],
                            threadId=email_data['threadId'],
                            body=email_data['body'],
                            body_preview=email_data['body_preview']
                        )

                        task = celery.send_task("email_triage", args=[email_data.model_dump()])

                        print(f"Storing email {msg_id} for user {email_address}")
                        print(f"Email details: From: {email_data.sender}, Subject: {email_data.subject}, Date: {email_data.date}, To: {email_data.to}, Snippet: {email_data.snippet}")
                        store_email(email_address, email_data)

        
                    except Exception as email_error:
                        print(f"⚠️ Error processing message {msg_id}: {email_error}")
                        continue

            # Update startHistoryId to the latest historyId from this notification
            update_start_history_id(email_address, history_id)

        except Exception as processing_error:
            print(f"❌ Error processing notification: {processing_error}")
            # Continue to acknowledge anyway

        print(f"Celery Task Added Task ID: {task.id}")
        return email.NotificationResponse(status="processed", email=email_address, history_id=str(history_id), processed_message_ids=list(processed_message_ids), email_data=email_data, task_id=task.id).model_dump()

        
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

# Background task to refresh watches
@router.on_event("startup")
async def start_watch_refresh_task():
    """Start the background task to periodically refresh watches"""
    asyncio.create_task(periodic_watch_refresh())

async def periodic_watch_refresh():
    """Periodically refresh watches before they expire"""
    import logging
    logger = logging.getLogger(__name__)
    
    while True:
        logger.info("Running watch refresh task")
        try:
            users = get_all_watching_users()
            for user_email in users:
                try:
                    watcher = GmailWatcher(user_email)
                    result = watcher.refresh_watch_if_needed()
                    if result:
                        logger.info(f"Refreshed watch for {user_email}")
                except Exception as e:
                    logger.error(f"Failed to refresh watch for {user_email}: {e}")
        except Exception as e:
            logger.error(f"Watch refresh task error: {e}")
            
        # Wait for 5 minutes before next refresh
        await asyncio.sleep(300)