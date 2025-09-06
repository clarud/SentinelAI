"""
Organization extraction tool for identifying companies, institutions, and entities in text.
"""

import re
from typing import List, Dict, Any


def extract_organisation(text: str) -> Dict[str, Any]:
    """
    Extract and analyze organizations and entities mentioned in text.
    
    Args:
        text: Input text to extract organizations from
        
    Returns:
        dict: Contains extracted organizations and legitimacy analysis
    """
    if not isinstance(text, str):
        raise ValueError("Input text must be a string")
    
    # Extract different types of organizations
    banks = _extract_banks(text)
    tech_companies = _extract_tech_companies(text)
    government_agencies = _extract_government_agencies(text)
    generic_organizations = _extract_generic_organizations(text)
    
    # Combine all organizations
    all_organizations = banks + tech_companies + government_agencies + generic_organizations
    
    # Calculate legitimacy score
    legitimacy_score = _calculate_legitimacy_score(all_organizations)
    
    # Identify suspicious patterns
    suspicious_indicators = _identify_suspicious_patterns(text, all_organizations)
    
    return {
        "banks": banks,
        "tech_companies": tech_companies,
        "government_agencies": government_agencies,
        "other_organizations": generic_organizations,
        "total_organizations": len(all_organizations),
        "legitimacy_score": legitimacy_score,
        "suspicious_indicators": suspicious_indicators,
        "is_suspicious": legitimacy_score < 5.0 or len(suspicious_indicators) > 0
    }


def _extract_banks(text: str) -> List[Dict[str, Any]]:
    """Extract bank names from text."""
    bank_patterns = [
        r'\b(?:Bank of America|BOA)\b',
        r'\b(?:Wells Fargo|WF)\b',
        r'\b(?:Chase|JP Morgan|JPMorgan)\b',
        r'\b(?:Citibank|Citi)\b',
        r'\b(?:US Bank|U\.S\. Bank)\b',
        r'\b(?:Capital One)\b',
        r'\b(?:PNC Bank|PNC)\b',
        r'\b(?:TD Bank)\b',
        r'\b(?:Fifth Third|5/3)\b',
        r'\b(?:HSBC)\b',
        r'\b(?:Santander)\b',
        r'\b(?:Credit Union)\b',
        r'\b\w+\s+Bank\b',
        r'\b\w+\s+Credit\s+Union\b'
    ]
    
    banks = []
    for pattern in bank_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            banks.append({
                "name": match.group().strip(),
                "position": match.span(),
                "type": "bank",
                "confidence": 0.8
            })
    
    return banks


def _extract_tech_companies(text: str) -> List[Dict[str, Any]]:
    """Extract technology company names from text."""
    tech_patterns = [
        r'\b(?:Apple|Microsoft|Google|Amazon|Facebook|Meta)\b',
        r'\b(?:PayPal|Venmo|Cash App|Zelle)\b',
        r'\b(?:Netflix|Spotify|Adobe)\b',
        r'\b(?:Twitter|LinkedIn|Instagram|WhatsApp)\b',
        r'\b(?:Dropbox|OneDrive|iCloud)\b',
        r'\b(?:Gmail|Yahoo|Outlook|Hotmail)\b'
    ]
    
    tech_companies = []
    for pattern in tech_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            tech_companies.append({
                "name": match.group().strip(),
                "position": match.span(),
                "type": "tech_company",
                "confidence": 0.9
            })
    
    return tech_companies


def _extract_government_agencies(text: str) -> List[Dict[str, Any]]:
    """Extract government agency names from text."""
    gov_patterns = [
        r'\b(?:IRS|Internal Revenue Service)\b',
        r'\b(?:FBI|Federal Bureau of Investigation)\b',
        r'\b(?:CIA|Central Intelligence Agency)\b',
        r'\b(?:NSA|National Security Agency)\b',
        r'\b(?:DHS|Department of Homeland Security)\b',
        r'\b(?:SSA|Social Security Administration)\b',
        r'\b(?:USPS|United States Postal Service)\b',
        r'\b(?:DMV|Department of Motor Vehicles)\b'
    ]
    
    agencies = []
    for pattern in gov_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            agencies.append({
                "name": match.group().strip(),
                "position": match.span(),
                "type": "government_agency",
                "confidence": 0.85
            })
    
    return agencies


def _extract_generic_organizations(text: str) -> List[Dict[str, Any]]:
    """Extract generic organization patterns from text."""
    # Pattern for words ending in common organization suffixes
    org_patterns = [
        r'\b\w+\s+(?:Inc|Corp|Corporation|LLC|Ltd|Limited|Co|Company)\b',
        r'\b\w+\s+(?:Institute|Foundation|Association|Organization)\b',
        r'\b\w+\s+(?:University|College|School)\b',
        r'\b\w+\s+(?:Hospital|Medical|Health)\b'
    ]
    
    organizations = []
    for pattern in org_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            organizations.append({
                "name": match.group().strip(),
                "position": match.span(),
                "type": "organization",
                "confidence": 0.6
            })
    
    return organizations


def _calculate_legitimacy_score(organizations: List[Dict[str, Any]]) -> float:
    """Calculate overall legitimacy score based on extracted organizations."""
    if not organizations:
        return 5.0  # Neutral score
    
    total_score = 0.0
    weight_sum = 0.0
    
    type_scores = {
        "bank": 8.0,
        "tech_company": 7.0,
        "government_agency": 9.0,
        "organization": 6.0
    }
    
    for org in organizations:
        org_type = org.get("type", "organization")
        confidence = org.get("confidence", 0.5)
        base_score = type_scores.get(org_type, 5.0)
        
        weighted_score = base_score * confidence
        total_score += weighted_score
        weight_sum += confidence
    
    return round(total_score / weight_sum if weight_sum > 0 else 5.0, 2)


def _identify_suspicious_patterns(text: str, organizations: List[Dict[str, Any]]) -> List[str]:
    """Identify suspicious patterns in organization mentions."""
    suspicious_indicators = []
    
    # Check for impersonation patterns
    impersonation_patterns = [
        r'\b(?:fake|phishing|scam|fraudulent)\s+\w+',
        r'\b\w+[-_]\w+\.(?:com|net|org)\b',  # Suspicious domain-like patterns
        r'\b\w+\d+\w*\b'  # Names with random numbers
    ]
    
    for pattern in impersonation_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            suspicious_indicators.append("Potential impersonation pattern detected")
            break
    
    # Check for multiple conflicting organizations
    org_types = set(org["type"] for org in organizations)
    if len(org_types) > 2:
        suspicious_indicators.append("Multiple organization types mentioned")
    
    # Check for urgent language around organizations
    urgent_patterns = [
        r'\b(?:urgent|immediate|expires?|suspend|block|verify)\b.*(?:' + '|'.join([org["name"] for org in organizations]) + r')',
        r'(?:' + '|'.join([org["name"] for org in organizations]) + r').*\b(?:urgent|immediate|expires?|suspend|block|verify)\b'
    ]
    
    for pattern in urgent_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            suspicious_indicators.append("Urgent language used with organization names")
            break
    
    return suspicious_indicators
