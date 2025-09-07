import time
import os
import base64
from fastapi import APIRouter
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest
from mcp.gmail_tools.tools.firestore_services import get_tokens, create_credentials_from_dict, update_watch_expiration

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
            from mcp.gmail_tools.tools.firestore_services import store_tokens
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
            from firestore_services import update_start_history_id
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
        from firestore_services import get_watch_expiration
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

