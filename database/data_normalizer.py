import re
import string
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataNormalizer:
    """Handles data cleaning and normalization for fraud detection"""
    
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        
    def clean_text(self, text: str) -> str:
        """Basic text cleaning operations"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove non-printable characters but keep basic punctuation
        text = ''.join(char for char in text if char.isprintable())
        
        # Normalize common separators
        text = re.sub(r'[—–]', '-', text)  # Em dash and en dash to hyphen
        text = re.sub(r'["""]', '"', text)  # Smart quotes to regular quotes
        text = re.sub(r"[''']", "'", text)  # Smart apostrophes to regular apostrophes
        
        return text
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract common entities like emails, phone numbers, URLs"""
        entities = {
            'emails': self.email_pattern.findall(text),
            'phone_numbers': [match[0] + match[1] if match[0] else match[1] 
                            for match in self.phone_pattern.findall(text)],
            'urls': self.url_pattern.findall(text)
        }
        
        # Remove duplicates while preserving order
        for key in entities:
            entities[key] = list(dict.fromkeys(entities[key]))
        
        return entities
    
    def detect_suspicious_patterns(self, text: str) -> Dict[str, Any]:
        """Detect patterns commonly associated with fraud"""
        suspicious_indicators = {
            'urgency_words': [],
            'financial_terms': [],
            'suspicious_phrases': [],
            'excessive_caps': False,
            'excessive_punctuation': False
        }
        
        text_lower = text.lower()
        
        # Urgency indicators
        urgency_words = [
            'urgent', 'immediate', 'asap', 'quickly', 'hurry', 'deadline',
            'expires', 'limited time', 'act now', 'don\'t wait'
        ]
        
        for word in urgency_words:
            if word in text_lower:
                suspicious_indicators['urgency_words'].append(word)
        
        # Financial terms that might indicate scams
        financial_terms = [
            'money', 'cash', 'payment', 'transfer', 'wire', 'bitcoin',
            'cryptocurrency', 'investment', 'profit', 'guarantee',
            'refund', 'credit card', 'bank account', 'social security'
        ]
        
        for term in financial_terms:
            if term in text_lower:
                suspicious_indicators['financial_terms'].append(term)
        
        # Suspicious phrases
        suspicious_phrases = [
            'click here', 'verify account', 'confirm identity', 'update information',
            'suspended account', 'security alert', 'congratulations you\'ve won',
            'nigerian prince', 'lottery winner', 'inheritance money'
        ]
        
        for phrase in suspicious_phrases:
            if phrase in text_lower:
                suspicious_indicators['suspicious_phrases'].append(phrase)
        
        # Check for excessive capitalization (> 30% of letters)
        alpha_chars = [c for c in text if c.isalpha()]
        if alpha_chars:
            caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
            suspicious_indicators['excessive_caps'] = caps_ratio > 0.3
        
        # Check for excessive punctuation
        punct_count = sum(1 for c in text if c in string.punctuation)
        if len(text) > 0:
            punct_ratio = punct_count / len(text)
            suspicious_indicators['excessive_punctuation'] = punct_ratio > 0.1
        
        return suspicious_indicators
    
    def normalize_document(self, parsed_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Main normalization method for parsed documents"""
        content = parsed_doc.get('content', '')
        
        # Clean the text content
        cleaned_content = self.clean_text(content)
        
        # Extract entities
        entities = self.extract_entities(cleaned_content)
        
        # Detect suspicious patterns
        suspicious_patterns = self.detect_suspicious_patterns(cleaned_content)
        
        # Calculate basic statistics
        stats = {
            'original_length': len(content),
            'cleaned_length': len(cleaned_content),
            'word_count': len(cleaned_content.split()) if cleaned_content else 0,
            'sentence_count': len([s for s in cleaned_content.split('.') if s.strip()]),
            'entity_count': sum(len(entities[key]) for key in entities)
        }
        
        # Create normalized document
        normalized_doc = {
            'original_content': content,
            'cleaned_content': cleaned_content,
            'entities': entities,
            'suspicious_patterns': suspicious_patterns,
            'stats': stats,
            'file_info': parsed_doc.get('file_info', {}),
            'original_metadata': parsed_doc.get('metadata', {})
        }
        
        logger.info(f"Normalized document: {stats['word_count']} words, "
                   f"{stats['entity_count']} entities extracted")
        
        return normalized_doc
