from mcp.gmail_tools.tools.gmail_watcher import GmailWatcher

def get_or_create_scam_label(service):
    """
    Get the SCAM label ID, creating it if it doesn't exist
    
    Args:
        service: Authenticated Gmail service
        
    Returns:
        str: The label ID for SCAM
    """
    try:
        # List all labels to check if SCAM label exists
        labels = service.users().labels().list(userId='me').execute()
        
        for label in labels.get('labels', []):
            if label['name'].upper() == 'SCAM':
                return label['id']
        
        # Create SCAM label if it doesn't exist
        label_object = {
            'name': 'SCAM',
            'messageListVisibility': 'show',
            'labelListVisibility': 'labelShow',
            'color': {
                'textColor': '#ffffff',
                'backgroundColor': '#000000'  # Red background for scam
            }
        }
        
        created_label = service.users().labels().create(
            userId='me',
            body=label_object
        ).execute()
        
        return created_label['id']
        
    except Exception as e:
        raise Exception(f"Failed to get or create SCAM label: {e}")

def mark_as_scam(user_email: str, message_id: str):
    """
    Mark an email as scam by adding SCAM label and removing from INBOX
    
    Args:
        user_email (str): The email address of the user
        message_id (str): The ID of the message to mark as scam
        
    Returns:
        dict: Result of the operation
    """
    try:
        watcher = GmailWatcher(user_email)
        service = watcher._get_service()
        
        # Get or create the SCAM label
        scam_label_id = get_or_create_scam_label(service)
        
        # Mark as scam: add SCAM label and remove from INBOX
        label_modifications = {
            'addLabelIds': [scam_label_id],
            'removeLabelIds': ['INBOX']
        }
        
        # Apply label modifications
        result = service.users().messages().modify(
            userId='me',
            id=message_id,
            body=label_modifications
        ).execute()
        
        return {
            "status": "success",
            "action": "marked_as_scam",
            "message_id": message_id,
            "scam_label_id": scam_label_id,
            "labels": result.get('labelIds', [])
        }
        
    except Exception as e:
        raise Exception(f"Failed to mark email as scam: {e}")

def modify_labels(user_email: str, message_id: str, add_labels: list = None, remove_labels: list = None):
    """
    Modify labels for a specific email message
    
    Args:
        user_email (str): The email address of the user
        message_id (str): The ID of the message to modify
        add_labels (list): List of label IDs to add (optional)
        remove_labels (list): List of label IDs to remove (optional)
        
    Returns:
        dict: The modified message object from Gmail API
        
    Note: If no labels are specified, defaults to marking the email as scam
    """
    # Default behavior: mark as scam if no specific labels provided
    if not add_labels and not remove_labels:
        return mark_as_scam(user_email, message_id)
    
    try:
        watcher = GmailWatcher(user_email)
        service = watcher._get_service()
        
        # Prepare label modifications
        label_modifications = {}
        if add_labels:
            label_modifications['addLabelIds'] = add_labels
        if remove_labels:
            label_modifications['removeLabelIds'] = remove_labels
            
        # Apply label modifications
        result = service.users().messages().modify(
            userId='me',
            id=message_id,
            body=label_modifications
        ).execute()
        
        return {
            "status": "success",
            "action": "custom_labels_modified",
            "message_id": message_id,
            "labels": result.get('labelIds', [])
        }
        
    except Exception as e:
        raise Exception(f"Failed to modify labels: {e}")
