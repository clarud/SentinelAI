from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetadataTagger:
    """Handles metadata tagging for fraud detection documents"""
    
    def __init__(self):
        self.risk_keywords = {
            'high_risk': [
                'urgent payment', 'wire transfer', 'bitcoin', 'cryptocurrency',
                'nigerian prince', 'lottery winner', 'inheritance', 'tax refund',
                'suspended account', 'verify immediately', 'click here now',
                'congratulations you won', 'limited time offer', 'act now'
            ],
            'medium_risk': [
                'payment required', 'update information', 'confirm account',
                'security alert', 'unusual activity', 'refund available',
                'investment opportunity', 'guaranteed profit', 'easy money'
            ],
            'low_risk': [
                'newsletter', 'subscription', 'notification', 'reminder',
                'receipt', 'confirmation', 'welcome', 'thank you'
            ]
        }
    
    def determine_source_type(self, file_info: Dict[str, Any]) -> str:
        """Determine the source type based on file information"""
        filename = file_info.get('filename', '').lower()
        filepath = file_info.get('filepath', '').lower()
        file_extension = file_info.get('file_extension', '').lower()
        
        # Check file extension first
        if file_extension == '.pdf':
            if any(keyword in filename for keyword in ['email', 'message', 'mail']):
                return 'email_pdf'
            elif any(keyword in filename for keyword in ['invoice', 'receipt', 'bill']):
                return 'invoice_pdf'
            elif any(keyword in filename for keyword in ['report', 'document', 'form']):
                return 'document_pdf'
            else:
                return 'pdf'
        
        elif file_extension == '.csv':
            return 'csv_data'
        
        elif file_extension == '.txt':
            if any(keyword in filename for keyword in ['email', 'message']):
                return 'email_text'
            elif any(keyword in filename for keyword in ['log', 'transcript']):
                return 'log_text'
            else:
                return 'text'
        
        # Check for email-like content patterns
        elif 'email' in filename or 'message' in filename:
            return 'email'
        
        # Check for web-related content
        elif any(keyword in filename for keyword in ['web', 'html', 'url', 'website']):
            return 'website'
        
        # Default fallback
        return 'unknown'
    
    def calculate_risk_level(self, 
                           content: str, 
                           entities: Dict[str, List[str]], 
                           suspicious_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk level and probability based on content analysis"""
        
        content_lower = content.lower()
        risk_score = 0.0
        risk_factors = []
        
        # Check for high-risk keywords (weight: 3.0 each)
        for keyword in self.risk_keywords['high_risk']:
            if keyword in content_lower:
                risk_score += 3.0
                risk_factors.append(f"High-risk keyword: {keyword}")
        
        # Check for medium-risk keywords (weight: 1.5 each)
        for keyword in self.risk_keywords['medium_risk']:
            if keyword in content_lower:
                risk_score += 1.5
                risk_factors.append(f"Medium-risk keyword: {keyword}")
        
        # Check for low-risk keywords (weight: -0.5 each, reduces risk)
        for keyword in self.risk_keywords['low_risk']:
            if keyword in content_lower:
                risk_score -= 0.5
                risk_factors.append(f"Low-risk keyword: {keyword}")
        
        # Analyze suspicious patterns
        if suspicious_patterns.get('urgency_words'):
            risk_score += len(suspicious_patterns['urgency_words']) * 0.5
            risk_factors.append(f"Urgency indicators: {len(suspicious_patterns['urgency_words'])}")
        
        if suspicious_patterns.get('financial_terms'):
            risk_score += len(suspicious_patterns['financial_terms']) * 0.3
            risk_factors.append(f"Financial terms: {len(suspicious_patterns['financial_terms'])}")
        
        if suspicious_patterns.get('suspicious_phrases'):
            risk_score += len(suspicious_patterns['suspicious_phrases']) * 2.0
            risk_factors.append(f"Suspicious phrases: {len(suspicious_patterns['suspicious_phrases'])}")
        
        if suspicious_patterns.get('excessive_caps'):
            risk_score += 1.0
            risk_factors.append("Excessive capitalization")
        
        if suspicious_patterns.get('excessive_punctuation'):
            risk_score += 0.5
            risk_factors.append("Excessive punctuation")
        
        # Analyze entities for risk indicators
        if entities.get('emails'):
            # Multiple email addresses might indicate forwarded scams
            if len(entities['emails']) > 3:
                risk_score += 1.0
                risk_factors.append(f"Multiple email addresses: {len(entities['emails'])}")
        
        if entities.get('urls'):
            # Multiple URLs might indicate phishing
            if len(entities['urls']) > 2:
                risk_score += 1.5
                risk_factors.append(f"Multiple URLs: {len(entities['urls'])}")
            
            # Check for suspicious domains
            suspicious_domains = ['bit.ly', 'tinyurl', 'goo.gl', 't.co']
            for url in entities['urls']:
                if any(domain in url.lower() for domain in suspicious_domains):
                    risk_score += 2.0
                    risk_factors.append(f"Suspicious URL shortener: {url}")
        
        # Convert score to probability (0-1)
        # Using sigmoid-like function to map score to probability
        max_score = 20.0  # Theoretical maximum score
        probability = min(max(risk_score / max_score, 0.0), 1.0)
        
        # Determine risk category
        if probability >= 0.7:
            risk_level = "scam"
        elif probability >= 0.3:
            risk_level = "unknown"
        else:
            risk_level = "not_scam"
        
        return {
            'risk_level': risk_level,
            'scam_probability': round(probability, 3),
            'risk_score': round(risk_score, 2),
            'risk_factors': risk_factors
        }
    
    def create_metadata(self, chunked_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive metadata for the document and its chunks"""
        
        original_doc = chunked_doc.get('original_document', {})
        file_info = original_doc.get('file_info', {})
        entities = original_doc.get('entities', {})
        suspicious_patterns = original_doc.get('suspicious_patterns', {})
        
        # Determine source type
        source = self.determine_source_type(file_info)
        
        # Get document name
        document_name = file_info.get('filename', 'unknown_document')
        
        # Calculate risk for the full document
        full_content = original_doc.get('cleaned_content', '')
        document_risk = self.calculate_risk_level(full_content, entities, suspicious_patterns)
        
        # Create base metadata that applies to the entire document
        base_metadata = {
            'source': source,
            'document_name': document_name,
            'risk_level': document_risk['risk_level'],
            'scam_probability': document_risk['scam_probability'],
            'document_risk_score': document_risk['risk_score'],
            'document_risk_factors': document_risk['risk_factors'],
            'processed_timestamp': datetime.now().isoformat(),
            'file_size': file_info.get('file_size', 0),
            'file_extension': file_info.get('file_extension', ''),
            'chunk_count': chunked_doc.get('chunk_count', 0),
            'total_characters': chunked_doc.get('total_characters', 0),
            'entities_found': {
                'emails': len(entities.get('emails', [])),
                'phone_numbers': len(entities.get('phone_numbers', [])),
                'urls': len(entities.get('urls', []))
            }
        }
        
        # Create metadata for each chunk
        chunks_with_metadata = []
        for chunk in chunked_doc.get('chunks', []):
            # Calculate risk for individual chunk
            chunk_risk = self.calculate_risk_level(
                chunk['text'], 
                entities,  # Use document-level entities for context
                suspicious_patterns
            )
            
            chunk_metadata = {
                **base_metadata,  # Include all base metadata
                'chunk_id': chunk['chunk_id'],
                'chunk_size': chunk['chunk_size'],
                'chunk_risk_level': chunk_risk['risk_level'],
                'chunk_scam_probability': chunk_risk['scam_probability'],
                'chunk_risk_score': chunk_risk['risk_score'],
                'chunk_risk_factors': chunk_risk['risk_factors'],
                'start_position': chunk.get('start_position'),
                'end_position': chunk.get('end_position'),
                'chunking_method': chunk.get('chunking_method', 'unknown')
            }
            
            chunks_with_metadata.append({
                'text': chunk['text'],
                'metadata': chunk_metadata
            })
        
        result = {
            'document_metadata': base_metadata,
            'chunks_with_metadata': chunks_with_metadata,
            'processing_summary': {
                'total_chunks': len(chunks_with_metadata),
                'high_risk_chunks': len([c for c in chunks_with_metadata 
                                       if c['metadata']['chunk_risk_level'] == 'scam']),
                'medium_risk_chunks': len([c for c in chunks_with_metadata 
                                         if c['metadata']['chunk_risk_level'] == 'unknown']),
                'low_risk_chunks': len([c for c in chunks_with_metadata 
                                      if c['metadata']['chunk_risk_level'] == 'not_scam'])
            }
        }
        
        logger.info(f"Created metadata for document '{document_name}': "
                   f"{result['processing_summary']['total_chunks']} chunks, "
                   f"risk level: {base_metadata['risk_level']} "
                   f"(probability: {base_metadata['scam_probability']})")
        
        return result
