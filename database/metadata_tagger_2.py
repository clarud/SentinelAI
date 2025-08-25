from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetadataTagger:
    """Handles metadata tagging for fraud detection documents - Version 2
    
    This version sets all documents to 'unknown' risk level since the actual
    risk assessment will be performed by the main agent using MCP server tools.
    """
    
    def __init__(self):
        # Keep risk keywords for potential future use or reference
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
    
    def set_default_risk_assessment(self) -> Dict[str, Any]:
        """Set default risk assessment for documents before main agent processing"""
        return {
            'risk_level': 'unknown',
            'scam_probability': None,  # Will be set by main agent
            'risk_score': None,       # Will be calculated by main agent
            'risk_factors': []        # Will be populated by main agent
        }
    
    def create_metadata(self, chunked_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive metadata for the document and its chunks
        
        All documents are initially tagged as 'unknown' risk level since
        the actual risk assessment will be performed by the main agent.
        """
        
        original_doc = chunked_doc.get('original_document', {})
        file_info = original_doc.get('file_info', {})
        entities = original_doc.get('entities', {})
        suspicious_patterns = original_doc.get('suspicious_patterns', {})
        
        # Determine source type
        source = self.determine_source_type(file_info)
        
        # Get document name
        document_name = file_info.get('filename', 'unknown_document')
        
        # Set default risk assessment (unknown until main agent processes)
        document_risk = self.set_default_risk_assessment()
        
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
            },
            # Store raw analysis data for future use by main agent
            'raw_entities': entities,
            'raw_suspicious_patterns': suspicious_patterns,
            'requires_risk_assessment': True  # Flag indicating this needs main agent processing
        }
        
        # Create metadata for each chunk
        chunks_with_metadata = []
        for chunk in chunked_doc.get('chunks', []):
            # Set default risk assessment for chunks as well
            chunk_risk = self.set_default_risk_assessment()
            
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
                'high_risk_chunks': 0,    # Will be updated after main agent processing
                'medium_risk_chunks': 0,  # Will be updated after main agent processing
                'low_risk_chunks': 0,     # Will be updated after main agent processing
                'unknown_risk_chunks': len(chunks_with_metadata)  # All chunks start as unknown
            }
        }
        
        logger.info(f"Created initial metadata for document '{document_name}': "
                   f"{result['processing_summary']['total_chunks']} chunks, "
                   f"risk level: {base_metadata['risk_level']} "
                   f"(awaiting main agent risk assessment)")
        
        return result
    
    def update_risk_assessment(self, 
                             metadata: Dict[str, Any], 
                             risk_level: str, 
                             scam_probability: Optional[float] = None,
                             risk_score: Optional[float] = None,
                             risk_factors: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update risk assessment after main agent processing
        
        This method will be used to update the metadata after the main agent
        has determined the actual risk level and scam probability.
        """
        
        # Update document-level risk assessment
        metadata['document_metadata']['risk_level'] = risk_level
        metadata['document_metadata']['scam_probability'] = scam_probability
        metadata['document_metadata']['document_risk_score'] = risk_score
        metadata['document_metadata']['document_risk_factors'] = risk_factors or []
        metadata['document_metadata']['requires_risk_assessment'] = False
        metadata['document_metadata']['risk_assessment_timestamp'] = datetime.now().isoformat()
        
        # Update chunk-level risk assessment (assuming same risk level for all chunks)
        for chunk in metadata['chunks_with_metadata']:
            chunk['metadata']['chunk_risk_level'] = risk_level
            chunk['metadata']['chunk_scam_probability'] = scam_probability
            chunk['metadata']['chunk_risk_score'] = risk_score
            chunk['metadata']['chunk_risk_factors'] = risk_factors or []
        
        # Update processing summary
        total_chunks = len(metadata['chunks_with_metadata'])
        if risk_level == 'scam':
            metadata['processing_summary']['high_risk_chunks'] = total_chunks
            metadata['processing_summary']['medium_risk_chunks'] = 0
            metadata['processing_summary']['low_risk_chunks'] = 0
        elif risk_level == 'not_scam':
            metadata['processing_summary']['high_risk_chunks'] = 0
            metadata['processing_summary']['medium_risk_chunks'] = 0
            metadata['processing_summary']['low_risk_chunks'] = total_chunks
        else:  # unknown
            metadata['processing_summary']['high_risk_chunks'] = 0
            metadata['processing_summary']['medium_risk_chunks'] = total_chunks
            metadata['processing_summary']['low_risk_chunks'] = 0
        
        metadata['processing_summary']['unknown_risk_chunks'] = 0
        
        logger.info(f"Updated risk assessment for document "
                   f"'{metadata['document_metadata']['document_name']}': "
                   f"risk level: {risk_level}, "
                   f"probability: {scam_probability}")
        
        return metadata
