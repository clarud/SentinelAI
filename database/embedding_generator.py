import os
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Handles generation of embeddings using OpenAI's text-embedding-3-small model"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the embedding generator
        
        Args:
            api_key: OpenAI API key (if not provided, will try to load from environment)
        """
        # Load environment variables
        load_dotenv()
        
        if OpenAI is None:
            raise ImportError(
                "OpenAI library not installed. Please install it with: pip install openai"
            )
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY environment variable "
                "or pass it directly to the constructor."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "text-embedding-3-small"
        self.embedding_dimension = 1536  # Dimension for text-embedding-3-small
        
        logger.info(f"Initialized embedding generator with model: {self.model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return [0.0] * self.embedding_dimension
        
        try:
            # Clean and prepare text
            cleaned_text = text.strip()
            
            # OpenAI's embedding models have a token limit, truncate if necessary
            # Rough estimation: 1 token ≈ 4 characters for English text
            max_chars = 8000 * 4  # Conservative limit for text-embedding-3-small
            if len(cleaned_text) > max_chars:
                cleaned_text = cleaned_text[:max_chars]
                logger.warning(f"Text truncated to {max_chars} characters for embedding")
            
            response = self.client.embeddings.create(
                input=cleaned_text,
                model=self.model
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding for text of length {len(cleaned_text)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        logger.info(f"Generating embeddings for {len(texts)} texts in {total_batches} batches")
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)")
            
            try:
                # Clean and prepare batch
                cleaned_batch = []
                for text in batch:
                    if not text or not text.strip():
                        cleaned_batch.append(" ")  # Use space for empty texts
                    else:
                        cleaned_text = text.strip()
                        # Truncate if necessary
                        max_chars = 8000 * 4
                        if len(cleaned_text) > max_chars:
                            cleaned_text = cleaned_text[:max_chars]
                        cleaned_batch.append(cleaned_text)
                
                response = self.client.embeddings.create(
                    input=cleaned_batch,
                    model=self.model
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {str(e)}")
                # Add zero embeddings for failed batch
                failed_embeddings = [[0.0] * self.embedding_dimension] * len(batch)
                embeddings.extend(failed_embeddings)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def process_chunks_with_embeddings(self, chunks_with_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process chunks with metadata and add embeddings
        
        Args:
            chunks_with_metadata: List of chunks with their metadata
            
        Returns:
            List of chunks with embeddings added
        """
        if not chunks_with_metadata:
            return []
        
        logger.info(f"Processing {len(chunks_with_metadata)} chunks for embedding generation")
        
        # Extract texts for embedding generation
        texts = [chunk['text'] for chunk in chunks_with_metadata]
        
        # Generate embeddings
        embeddings = self.generate_batch_embeddings(texts)
        
        # Combine chunks with their embeddings
        processed_chunks = []
        for i, chunk in enumerate(chunks_with_metadata):
            processed_chunk = {
                'text': chunk['text'],
                'metadata': chunk['metadata'],
                'embedding': embeddings[i] if i < len(embeddings) else [0.0] * self.embedding_dimension,
                'embedding_model': self.model,
                'embedding_dimension': len(embeddings[i]) if i < len(embeddings) else self.embedding_dimension
            }
            processed_chunks.append(processed_chunk)
        
        logger.info(f"Successfully processed {len(processed_chunks)} chunks with embeddings")
        return processed_chunks
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the embedding model and configuration"""
        return {
            'model': self.model,
            'dimension': self.embedding_dimension,
            'provider': 'OpenAI',
            'api_key_configured': bool(self.api_key)
        }
