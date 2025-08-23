import os
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
import time
from datetime import datetime
from dotenv import load_dotenv

try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
except ImportError:
    pinecone = None
    Pinecone = None
    ServerlessSpec = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorIndexer:
    """Handles indexing of embeddings into Pinecone vector database"""
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 environment: Optional[str] = None,
                 index_name: Optional[str] = None):
        """
        Initialize the vector indexer
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment
            index_name: Name of the Pinecone index to use
        """
        # Load environment variables
        load_dotenv()
        
        if Pinecone is None:
            raise ImportError(
                "Pinecone library not installed. Please install it with: pip install pinecone-client"
            )
        
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        self.environment = environment or os.getenv('PINECONE_ENVIRONMENT')
        self.index_name = index_name or os.getenv('PINECONE_INDEX_NAME', 'fraud-detection-docs')
        
        if not self.api_key:
            raise ValueError(
                "Pinecone API key not found. Please set PINECONE_API_KEY environment variable "
                "or pass it directly to the constructor."
            )
        
        # Initialize Pinecone
        try:
            self.pc = Pinecone(api_key=self.api_key)
            logger.info("Successfully connected to Pinecone")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {str(e)}")
            raise
        
        self.index = None
        self.embedding_dimension = 1536  # Default for OpenAI text-embedding-3-small
        
    def create_index_if_not_exists(self, dimension: int = 1536, metric: str = "cosine") -> None:
        """
        Create Pinecone index if it doesn't exist
        
        Args:
            dimension: Dimension of the embeddings
            metric: Distance metric to use (cosine, euclidean, dotproduct)
        """
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                
                self.pc.create_index(
                    name=self.index_name,
                    dimension=dimension,
                    metric=metric,
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=self.environment or 'us-east-1'
                    )
                )
                
                # Wait for index to be ready
                logger.info("Waiting for index to be ready...")
                time.sleep(10)
            else:
                logger.info(f"Index {self.index_name} already exists")
            
            # Connect to the index
            self.index = self.pc.Index(self.index_name)
            self.embedding_dimension = dimension
            
            # Get index stats
            stats = self.index.describe_index_stats()
            logger.info(f"Connected to index {self.index_name}. "
                       f"Total vectors: {stats['total_vector_count']}")
            
        except Exception as e:
            logger.error(f"Error creating/connecting to index: {str(e)}")
            raise
    
    def prepare_vectors_for_upload(self, chunks_with_embeddings: List[Dict[str, Any]]) -> List[Tuple[str, List[float], Dict[str, Any]]]:
        """
        Prepare vectors for upload to Pinecone
        
        Args:
            chunks_with_embeddings: List of chunks with embeddings and metadata
            
        Returns:
            List of tuples (id, embedding, metadata) ready for Pinecone upload
        """
        vectors = []
        
        for i, chunk in enumerate(chunks_with_embeddings):
            # Create unique ID for the vector
            document_name = chunk['metadata'].get('document_name', 'unknown')
            chunk_id = chunk['metadata'].get('chunk_id', i)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            vector_id = f"{document_name}_{chunk_id}_{timestamp}_{i}"
            
            # Prepare metadata (Pinecone has limitations on metadata size and types)
            metadata = {
                'text': chunk['text'][:1000],  # Truncate text for metadata storage
                'source': chunk['metadata'].get('source', 'unknown'),
                'document_name': chunk['metadata'].get('document_name', 'unknown'),
                'risk_level': chunk['metadata'].get('risk_level', 'unknown'),
                'chunk_risk_level': chunk['metadata'].get('chunk_risk_level', 'unknown'),
                'chunk_id': chunk['metadata'].get('chunk_id', i),
                'chunk_size': chunk['metadata'].get('chunk_size', 0),
                'file_extension': chunk['metadata'].get('file_extension', ''),
                'processed_timestamp': chunk['metadata'].get('processed_timestamp', ''),
                'embedding_model': chunk.get('embedding_model', 'text-embedding-3-small')
            }
            
            # Add probability scores if available
            if 'scam_probability' in chunk['metadata']:
                metadata['scam_probability'] = chunk['metadata']['scam_probability']
            if 'chunk_scam_probability' in chunk['metadata']:
                metadata['chunk_scam_probability'] = chunk['metadata']['chunk_scam_probability']
            
            # Add entity counts
            entities_found = chunk['metadata'].get('entities_found', {})
            for entity_type, count in entities_found.items():
                metadata[f'{entity_type}_count'] = count
            
            # Convert any non-string, non-number values to strings
            for key, value in metadata.items():
                if not isinstance(value, (str, int, float, bool)):
                    metadata[key] = str(value)
            
            vectors.append((vector_id, chunk['embedding'], metadata))
        
        logger.info(f"Prepared {len(vectors)} vectors for upload")
        return vectors
    
    def upload_vectors(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]], batch_size: int = 100) -> Dict[str, Any]:
        """
        Upload vectors to Pinecone index
        
        Args:
            vectors: List of (id, embedding, metadata) tuples
            batch_size: Number of vectors to upload in each batch
            
        Returns:
            Dictionary with upload statistics
        """
        if not self.index:
            raise RuntimeError("Index not initialized. Call create_index_if_not_exists() first.")
        
        if not vectors:
            logger.warning("No vectors to upload")
            return {'uploaded': 0, 'failed': 0, 'batches': 0}
        
        total_batches = (len(vectors) + batch_size - 1) // batch_size
        uploaded_count = 0
        failed_count = 0
        
        logger.info(f"Uploading {len(vectors)} vectors in {total_batches} batches")
        
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                logger.info(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} vectors)")
                
                # Prepare batch for Pinecone
                batch_data = [
                    {
                        'id': vector_id,
                        'values': embedding,
                        'metadata': metadata
                    }
                    for vector_id, embedding, metadata in batch
                ]
                
                # Upload batch
                upsert_response = self.index.upsert(vectors=batch_data)
                uploaded_count += upsert_response.upserted_count
                
                logger.info(f"Successfully uploaded batch {batch_num}")
                
            except Exception as e:
                logger.error(f"Error uploading batch {batch_num}: {str(e)}")
                failed_count += len(batch)
        
        # Wait a moment for indexing to complete
        time.sleep(2)
        
        # Get updated stats
        stats = self.index.describe_index_stats()
        
        result = {
            'uploaded': uploaded_count,
            'failed': failed_count,
            'batches': total_batches,
            'total_vectors_in_index': stats['total_vector_count']
        }
        
        logger.info(f"Upload complete. Uploaded: {uploaded_count}, Failed: {failed_count}, "
                   f"Total in index: {stats['total_vector_count']}")
        
        return result
    
    def process_and_index_document(self, chunks_with_embeddings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Complete pipeline to process and index a document
        
        Args:
            chunks_with_embeddings: Processed chunks with embeddings
            
        Returns:
            Dictionary with indexing results
        """
        if not chunks_with_embeddings:
            return {'error': 'No chunks provided'}
        
        try:
            # Ensure index exists
            if not self.index:
                self.create_index_if_not_exists()
            
            # Prepare vectors
            vectors = self.prepare_vectors_for_upload(chunks_with_embeddings)
            
            # Upload vectors
            upload_result = self.upload_vectors(vectors)
            
            # Add document info to result
            document_name = chunks_with_embeddings[0]['metadata'].get('document_name', 'unknown')
            result = {
                'document_name': document_name,
                'chunks_processed': len(chunks_with_embeddings),
                'vectors_prepared': len(vectors),
                **upload_result,
                'index_name': self.index_name,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully indexed document '{document_name}' with {len(vectors)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            return {'error': str(e)}
    
    def search_similar(self, 
                      query_embedding: List[float], 
                      top_k: int = 10, 
                      filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the index
        
        Args:
            query_embedding: Embedding vector to search for
            top_k: Number of similar vectors to return
            filter_dict: Metadata filters to apply
            
        Returns:
            List of similar vectors with metadata and scores
        """
        if not self.index:
            raise RuntimeError("Index not initialized")
        
        try:
            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            results = []
            for match in response['matches']:
                results.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match.get('metadata', {})
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            raise
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index"""
        if not self.index:
            return {'error': 'Index not initialized'}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                'index_name': self.index_name,
                'total_vector_count': stats['total_vector_count'],
                'dimension': self.embedding_dimension,
                'index_fullness': stats.get('index_fullness', 0),
                'namespaces': stats.get('namespaces', {})
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {'error': str(e)}
