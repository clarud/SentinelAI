from typing import List, Dict, Any, Optional
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentChunker:
    """Handles chunking of normalized documents for embedding generation"""
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 min_chunk_size: int = 100):
        """
        Initialize the document chunker
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum size for a chunk to be considered valid
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - can be enhanced with more sophisticated NLP
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return paragraphs
    
    def create_overlapping_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Create overlapping chunks from text"""
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 200 characters
                search_start = max(end - 200, start)
                sentence_endings = [m.end() for m in re.finditer(r'[.!?]\s+', text[search_start:end])]
                
                if sentence_endings:
                    # Use the last sentence ending within our range
                    end = search_start + sentence_endings[-1]
                elif end - start > self.chunk_size + 200:
                    # If chunk is too large and no sentence boundary found, force break
                    end = start + self.chunk_size
            
            chunk_text = text[start:end].strip()
            
            # Only add chunk if it meets minimum size requirement
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'start_position': start,
                    'end_position': end,
                    'chunk_size': len(chunk_text)
                })
                chunk_id += 1
            
            # Move start position for next chunk with overlap
            start = max(end - self.chunk_overlap, start + 1)
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def create_semantic_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Create chunks based on semantic boundaries (paragraphs, then sentences)"""
        chunks = []
        chunk_id = 0
        
        # First, try to split by paragraphs
        paragraphs = self.split_by_paragraphs(text)
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk + paragraph) > self.chunk_size and current_chunk:
                # Save current chunk if it meets minimum size
                if len(current_chunk.strip()) >= self.min_chunk_size:
                    chunks.append({
                        'chunk_id': chunk_id,
                        'text': current_chunk.strip(),
                        'chunk_size': len(current_chunk.strip()),
                        'chunk_type': 'semantic'
                    })
                    chunk_id += 1
                
                current_chunk = paragraph
            else:
                current_chunk += ("\n\n" if current_chunk else "") + paragraph
        
        # Add the last chunk
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunks.append({
                'chunk_id': chunk_id,
                'text': current_chunk.strip(),
                'chunk_size': len(current_chunk.strip()),
                'chunk_type': 'semantic'
            })
        
        # If no semantic chunks were created or chunks are too large, fall back to overlapping chunks
        if not chunks or any(chunk['chunk_size'] > self.chunk_size * 1.5 for chunk in chunks):
            logger.info("Falling back to overlapping chunks due to large semantic chunks")
            return self.create_overlapping_chunks(text)
        
        return chunks
    
    def chunk_document(self, normalized_doc: Dict[str, Any], method: str = "semantic") -> Dict[str, Any]:
        """
        Main method to chunk a normalized document
        
        Args:
            normalized_doc: Document from data_normalizer
            method: Chunking method ('semantic' or 'overlapping')
        
        Returns:
            Dictionary containing chunked document with metadata
        """
        content = normalized_doc.get('cleaned_content', '')
        
        if not content:
            logger.warning("No content to chunk")
            return {
                'chunks': [],
                'chunk_count': 0,
                'total_characters': 0,
                'original_document': normalized_doc
            }
        
        logger.info(f"Chunking document using {method} method")
        
        if method == "semantic":
            chunks = self.create_semantic_chunks(content)
        elif method == "overlapping":
            chunks = self.create_overlapping_chunks(content)
        else:
            raise ValueError(f"Unknown chunking method: {method}")
        
        # Add document metadata to each chunk
        for chunk in chunks:
            chunk.update({
                'document_filename': normalized_doc.get('file_info', {}).get('filename', 'unknown'),
                'document_filepath': normalized_doc.get('file_info', {}).get('filepath', 'unknown'),
                'document_entities': normalized_doc.get('entities', {}),
                'document_suspicious_patterns': normalized_doc.get('suspicious_patterns', {}),
                'chunking_method': method
            })
        
        chunked_doc = {
            'chunks': chunks,
            'chunk_count': len(chunks),
            'total_characters': sum(chunk['chunk_size'] for chunk in chunks),
            'chunking_method': method,
            'chunking_config': {
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'min_chunk_size': self.min_chunk_size
            },
            'original_document': normalized_doc
        }
        
        logger.info(f"Created {len(chunks)} chunks with total {chunked_doc['total_characters']} characters")
        
        return chunked_doc
