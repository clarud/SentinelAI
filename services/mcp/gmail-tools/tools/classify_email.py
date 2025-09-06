"""
Email classification tool for categorizing emails by type and threat level.
"""

from typing import Dict, Any
import re


def classify_email(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify email by type and assess threat level.
    
    Args:
        email_data: Email data dictionary containing subject, content, sender, etc.
        
    Returns:
        dict: Classification results with type, threat level, and confidence
    """
    if not isinstance(email_data, dict):
        raise ValueError("Email data must be a dictionary")
    
    # Extract email components
    subject = email_data.get("subject", "")
    content = email_data.get("content", email_data.get("body", ""))
    sender = email_data.get("sender", email_data.get("from", ""))
    
    # Combine all text for analysis
    full_text = f"{subject} {content} {sender}".lower()
    
    # Classify email type
    email_type = _classify_email_type(full_text, subject, content, sender)
    
    # Assess threat level
    threat_level, threat_score = _assess_threat_level(full_text, email_type)
    
    # Calculate confidence based on pattern matches
    confidence = _calculate_classification_confidence(full_text, email_type)
    
    # Identify specific indicators
    indicators = _identify_classification_indicators(full_text, email_type)
    
    return {
        "classification": email_type,
        "threat_level": threat_level,
        "threat_score": threat_score,
        "confidence": confidence,
        "indicators": indicators,
        "is_suspicious": threat_score > 6.0,
        "requires_action": threat_score > 8.0
    }


def _classify_email_type(full_text: str, subject: str, content: str, sender: str) -> str:
    """Classify the email into categories."""
    
    # Phishing patterns
    phishing_patterns = [
        r'\b(?:verify|confirm|update|suspend|expire|urgent|immediate)\b',
        r'\b(?:click here|act now|limited time|expires soon)\b',
        r'\b(?:account|password|security|login|credentials)\b',
        r'\b(?:suspended|blocked|compromised|unauthorized)\b'
    ]
    
    # Spam patterns
    spam_patterns = [
        r'\b(?:free|winner|prize|lottery|congratulations)\b',
        r'\b(?:million|dollars|\$\d+|money|cash|reward)\b',
        r'\b(?:viagra|pills|medication|pharmacy)\b',
        r'\b(?:weight loss|diet|supplement)\b'
    ]
    
    # Business/marketing patterns
    marketing_patterns = [
        r'\b(?:newsletter|unsubscribe|promotion|offer|sale)\b',
        r'\b(?:discount|coupon|deal|special)\b',
        r'\b(?:company|business|service|product)\b'
    ]
    
    # Count pattern matches
    phishing_score = sum(1 for pattern in phishing_patterns if re.search(pattern, full_text))
    spam_score = sum(1 for pattern in spam_patterns if re.search(pattern, full_text))
    marketing_score = sum(1 for pattern in marketing_patterns if re.search(pattern, full_text))
    
    # Classify based on highest score
    if phishing_score >= 2:
        return "phishing"
    elif spam_score >= 2:
        return "spam"
    elif marketing_score >= 2:
        return "marketing"
    elif any(word in full_text for word in ["invoice", "receipt", "payment", "transaction"]):
        return "financial"
    elif any(word in full_text for word in ["meeting", "schedule", "appointment", "calendar"]):
        return "business"
    else:
        return "general"


def _assess_threat_level(full_text: str, email_type: str) -> tuple:
    """Assess the threat level of the email."""
    
    threat_score = 0.0
    
    # Base score by email type
    type_scores = {
        "phishing": 7.0,
        "spam": 5.0,
        "marketing": 2.0,
        "financial": 3.0,
        "business": 1.0,
        "general": 1.0
    }
    
    threat_score += type_scores.get(email_type, 1.0)
    
    # Additional threat indicators
    high_threat_indicators = [
        r'\b(?:malware|virus|trojan|ransomware)\b',
        r'\b(?:bitcoin|cryptocurrency|crypto)\b',
        r'\b(?:social security|ssn|tax|irs)\b',
        r'\b(?:wire transfer|western union|moneygram)\b'
    ]
    
    medium_threat_indicators = [
        r'\b(?:download|attachment|zip|exe)\b',
        r'\b(?:refund|rebate|tax return)\b',
        r'\b(?:personal information|private data)\b'
    ]
    
    # Add points for threat indicators
    for pattern in high_threat_indicators:
        if re.search(pattern, full_text):
            threat_score += 2.0
    
    for pattern in medium_threat_indicators:
        if re.search(pattern, full_text):
            threat_score += 1.0
    
    # Cap at 10
    threat_score = min(threat_score, 10.0)
    
    # Convert to threat level
    if threat_score >= 8.0:
        threat_level = "critical"
    elif threat_score >= 6.0:
        threat_level = "high"
    elif threat_score >= 4.0:
        threat_level = "medium"
    elif threat_score >= 2.0:
        threat_level = "low"
    else:
        threat_level = "minimal"
    
    return threat_level, round(threat_score, 1)


def _calculate_classification_confidence(full_text: str, email_type: str) -> float:
    """Calculate confidence in the classification."""
    
    # Base confidence by type certainty
    base_confidence = 0.6
    
    # Increase confidence for clear indicators
    clear_indicators = {
        "phishing": [r'\b(?:phishing|scam|fraud)\b', r'\b(?:verify.*account|confirm.*identity)\b'],
        "spam": [r'\b(?:spam|junk|promotional)\b', r'\b(?:unsubscribe|opt.*out)\b'],
        "marketing": [r'\b(?:newsletter|marketing|promotional)\b'],
        "financial": [r'\b(?:invoice|bill|payment|transaction)\b'],
        "business": [r'\b(?:meeting|project|deadline)\b']
    }
    
    if email_type in clear_indicators:
        matches = sum(1 for pattern in clear_indicators[email_type] if re.search(pattern, full_text))
        base_confidence += matches * 0.15
    
    return min(round(base_confidence, 2), 1.0)


def _identify_classification_indicators(full_text: str, email_type: str) -> list:
    """Identify specific indicators that led to the classification."""
    
    indicators = []
    
    # Type-specific indicators
    if email_type == "phishing":
        if re.search(r'\b(?:verify|confirm).*account\b', full_text):
            indicators.append("Account verification request")
        if re.search(r'\b(?:urgent|immediate|expires?)\b', full_text):
            indicators.append("Urgency language")
        if re.search(r'\b(?:click here|act now)\b', full_text):
            indicators.append("Call-to-action phrases")
    
    elif email_type == "spam":
        if re.search(r'\b(?:free|winner|prize)\b', full_text):
            indicators.append("Prize/giveaway language")
        if re.search(r'\b(?:million|dollars|\$\d+)\b', full_text):
            indicators.append("Money-related content")
    
    elif email_type == "marketing":
        if re.search(r'\b(?:unsubscribe|opt.*out)\b', full_text):
            indicators.append("Unsubscribe options")
        if re.search(r'\b(?:promotion|offer|sale)\b', full_text):
            indicators.append("Promotional content")
    
    # General suspicious indicators
    if re.search(r'\b(?:password|login|credentials)\b', full_text):
        indicators.append("Credential-related content")
    
    if re.search(r'\b(?:suspended|blocked|compromised)\b', full_text):
        indicators.append("Account status warnings")
    
    return indicators
