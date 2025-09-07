"""
Number extraction tool for identifying and analyzing phone numbers and numeric patterns in text.
"""

import re
from typing import List, Dict, Any


def extract_number(text: str) -> Dict[str, Any]:
    """
    Extract and analyze phone numbers and suspicious numeric patterns from text.
    
    Args:
        text: Input text to extract numbers from
        
    Returns:
        dict: Contains extracted numbers and risk analysis
    """
    if not isinstance(text, str):
        raise ValueError("Input text must be a string")
    
    # Extract different types of numbers
    phone_numbers = _extract_phone_numbers(text)
    credit_card_patterns = _extract_credit_card_patterns(text)
    ssn_patterns = _extract_ssn_patterns(text)
    bank_account_patterns = _extract_bank_account_patterns(text)
    
    # Calculate risk score based on findings
    risk_score = 0.0
    risk_factors = []
    
    if phone_numbers:
        risk_score += len(phone_numbers) * 1.0
        risk_factors.append(f"Found {len(phone_numbers)} phone number(s)")
    
    if credit_card_patterns:
        risk_score += len(credit_card_patterns) * 5.0
        risk_factors.append(f"Found {len(credit_card_patterns)} potential credit card pattern(s)")
    
    if ssn_patterns:
        risk_score += len(ssn_patterns) * 7.0
        risk_factors.append(f"Found {len(ssn_patterns)} potential SSN pattern(s)")
    
    if bank_account_patterns:
        risk_score += len(bank_account_patterns) * 4.0
        risk_factors.append(f"Found {len(bank_account_patterns)} potential bank account pattern(s)")
    
    return {
        "phone_numbers": phone_numbers,
        "credit_card_patterns": credit_card_patterns,
        "ssn_patterns": ssn_patterns,
        "bank_account_patterns": bank_account_patterns,
        "total_numbers": len(phone_numbers) + len(credit_card_patterns) + len(ssn_patterns) + len(bank_account_patterns),
        "risk_score": min(risk_score, 10.0),  # Cap at 10
        "risk_factors": risk_factors,
        "is_suspicious": risk_score > 5.0
    }


def _extract_phone_numbers(text: str) -> List[Dict[str, Any]]:
    """Extract phone numbers from text."""
    patterns = [
        r'\b(?:\+?1[-.\s]?)?(?:\(?[0-9]{3}\)?[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{4}\b',  # US format
        r'\b(?:\+?[1-9]{1}[0-9]{0,3}[-.\s]?)?(?:\(?[0-9]{1,4}\)?[-.\s]?)?[0-9]{1,4}[-.\s]?[0-9]{1,9}\b',  # International
    ]
    
    phone_numbers = []
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            number = match.group().strip()
            if len(re.sub(r'[^\d]', '', number)) >= 7:  # At least 7 digits
                phone_numbers.append({
                    "number": number,
                    "position": match.span(),
                    "type": "phone"
                })
    
    return phone_numbers


def _extract_credit_card_patterns(text: str) -> List[Dict[str, Any]]:
    """Extract potential credit card numbers."""
    # Pattern for 13-19 digit numbers (common credit card lengths)
    pattern = r'\b(?:\d{4}[-\s]?){3}\d{1,4}\b'
    
    credit_cards = []
    matches = re.finditer(pattern, text)
    for match in matches:
        number = re.sub(r'[^\d]', '', match.group())
        if 13 <= len(number) <= 19:
            credit_cards.append({
                "pattern": match.group().strip(),
                "position": match.span(),
                "type": "credit_card_pattern",
                "masked": number[:4] + '*' * (len(number) - 8) + number[-4:]
            })
    
    return credit_cards


def _extract_ssn_patterns(text: str) -> List[Dict[str, Any]]:
    """Extract potential Social Security Numbers."""
    pattern = r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
    
    ssn_patterns = []
    matches = re.finditer(pattern, text)
    for match in matches:
        ssn_patterns.append({
            "pattern": match.group().strip(),
            "position": match.span(),
            "type": "ssn_pattern",
            "masked": "***-**-" + match.group().strip()[-4:]
        })
    
    return ssn_patterns


def _extract_bank_account_patterns(text: str) -> List[Dict[str, Any]]:
    """Extract potential bank account numbers."""
    # Pattern for 8-17 digit bank account numbers
    pattern = r'\b\d{8,17}\b'
    
    bank_accounts = []
    matches = re.finditer(pattern, text)
    for match in matches:
        number = match.group()
        bank_accounts.append({
            "pattern": number,
            "position": match.span(),
            "type": "bank_account_pattern",
            "masked": number[:4] + '*' * (len(number) - 8) + number[-4:] if len(number) >= 8 else number
        })
    
    return bank_accounts
