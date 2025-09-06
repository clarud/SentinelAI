"""
Link extraction tool for identifying and analyzing URLs in text content.
"""

import re
from typing import List, Dict, Any
from urllib.parse import urlparse


def extract_link(text: str) -> Dict[str, Any]:
    """
    Extract and analyze links from text content.
    
    Args:
        text: Input text to extract links from
        
    Returns:
        dict: Contains extracted links and risk analysis
    """
    if not isinstance(text, str):
        raise ValueError("Input text must be a string")
    
    # Regular expression to find URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    # Find all URLs in the text
    urls = re.findall(url_pattern, text)
    
    # Remove duplicates while preserving order
    unique_urls = list(dict.fromkeys(urls))
    
    # Analyze each URL for risk factors
    analyzed_links = []
    risk_score = 0.0
    
    for url in unique_urls:
        link_analysis = _analyze_url(url)
        analyzed_links.append(link_analysis)
        risk_score += link_analysis["risk_score"]
    
    # Calculate average risk score
    avg_risk_score = risk_score / len(analyzed_links) if analyzed_links else 0.0
    
    return {
        "total_links": len(analyzed_links),
        "links": analyzed_links,
        "average_risk_score": round(avg_risk_score, 2),
        "high_risk_count": sum(1 for link in analyzed_links if link["risk_score"] > 7.0)
    }


def _analyze_url(url: str) -> Dict[str, Any]:
    """
    Analyze a single URL for risk factors.
    
    Args:
        url: URL to analyze
        
    Returns:
        dict: URL analysis results
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        risk_factors = []
        risk_score = 0.0
        
        # Check for suspicious domain patterns
        if any(suspicious in domain for suspicious in ['bit.ly', 'tinyurl', 'goo.gl', 't.co']):
            risk_factors.append("URL shortener")
            risk_score += 2.0
        
        # Check for suspicious TLDs
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.cc']
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            risk_factors.append("Suspicious TLD")
            risk_score += 3.0
        
        # Check for suspicious keywords in domain
        suspicious_keywords = ['secure', 'verify', 'update', 'confirm', 'urgent']
        if any(keyword in domain for keyword in suspicious_keywords):
            risk_factors.append("Suspicious keywords in domain")
            risk_score += 2.5
        
        # Check for suspicious path patterns
        if any(pattern in path for pattern in ['/login', '/verify', '/update', '/secure']):
            risk_factors.append("Suspicious path")
            risk_score += 1.5
        
        # Check for IP addresses instead of domain names
        if re.match(r'^\d+\.\d+\.\d+\.\d+', domain):
            risk_factors.append("IP address instead of domain")
            risk_score += 4.0
        
        return {
            "url": url,
            "domain": domain,
            "risk_score": min(risk_score, 10.0),  # Cap at 10
            "risk_factors": risk_factors,
            "is_suspicious": risk_score > 5.0
        }
        
    except Exception as e:
        return {
            "url": url,
            "domain": "unknown",
            "risk_score": 5.0,
            "risk_factors": ["URL parsing error"],
            "is_suspicious": True,
            "error": str(e)
        }
