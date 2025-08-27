import os
from typing import List, Dict, Any, Optional
import logging
import json
import time
from datetime import datetime
from dotenv import load_dotenv

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorIndexerIntegrated:
    """Handles indexing using Pinecone's integrated embeddings"""
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 index_host: Optional[str] = None,
                 embedding_model: str = "multilingual-e5-large"):
        """
        Initialize the vector indexer with integrated embeddings
        
        Args:
            api_key: Pinecone API key
            index_host: Pinecone index host URL
            embedding_model: Pinecone's embedding model to use
        """
        # Load environment variables
        load_dotenv()
        
        if Pinecone is None:
            raise ImportError(
                "Pinecone library not installed. Please install it with: pip install pinecone-client"
            )
        
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        self.index_host = index_host or os.getenv('PINECONE_INDEX_HOST')
        self.embedding_model = embedding_model
        self.detailed_logger = None  # Will be set by pipeline if available
        
        if not self.api_key:
            raise ValueError(
                "Pinecone API key not found. Please set PINECONE_API_KEY environment variable "
                "or pass it directly to the constructor."
            )
        
        if not self.index_host:
            raise ValueError(
                "Pinecone index host not found. Please set PINECONE_INDEX_HOST environment variable "
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
        
    def connect_to_index(self) -> None:
        """
        Connect to existing Pinecone index using host
        """
        try:
            # Connect to the index using host
            self.index = self.pc.Index(host=self.index_host)
            logger.info(f"Successfully connected to Pinecone index at host: {self.index_host}")
            
            # Get index stats
            stats = self.index.describe_index_stats()
            logger.info(f"Index stats - Total vectors: {stats['total_vector_count']}")
            
        except Exception as e:
            logger.error(f"Error connecting to index: {str(e)}")
            raise
    
    def set_detailed_logger(self, detailed_logger):
        """Set the detailed logger for enhanced logging"""
        self.detailed_logger = detailed_logger
    
    def prepare_records_for_upsert(self, chunks_with_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare records for upsert to Pinecone with integrated embeddings
        
        Args:
            chunks_with_metadata: List of chunks with text and metadata (no embeddings needed)
            
        Returns:
            List of records ready for Pinecone upsert_records
        """
        records = []
        vector_ids_path = os.path.join(os.path.dirname(__file__), 'vector_ids.txt')
        vector_ids_to_store = []
        
        for i, chunk in enumerate(chunks_with_metadata):
            # Create unique ID for the record
            document_name = chunk['metadata'].get('document_name', 'unknown')
            chunk_id = chunk['metadata'].get('chunk_id', i)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            record_id = f"{document_name}_{chunk_id}_{timestamp}_{i}"
            
            # Store record_id for logging to file
            vector_ids_to_store.append({
                'record_id': record_id,
                'document_name': document_name,
                'chunk_id': chunk_id,
                'timestamp': timestamp,
                'processed_at': datetime.now().isoformat()
            })
            
            # Prepare record for Pinecone with integrated embeddings
            record = {
                '_id': record_id,
                'text': chunk['text'],  # This will be embedded by Pinecone
                'document_name': chunk['metadata'].get('document_name', 'unknown'),
                'source': chunk['metadata'].get('source', 'unknown'),
                'risk_level': chunk['metadata'].get('risk_level', 'unknown'),
                'chunk_risk_level': chunk['metadata'].get('chunk_risk_level', 'unknown'),
                'chunk_id': chunk['metadata'].get('chunk_id', i),
                'chunk_size': chunk['metadata'].get('chunk_size', 0),
                'file_extension': chunk['metadata'].get('file_extension', ''),
                'processed_timestamp': chunk['metadata'].get('processed_timestamp', ''),
                'chunk_number': i + 1,
                'document_type': chunk['metadata'].get('source', 'unknown')
            }
            
            # Add probability scores if available
            if 'scam_probability' in chunk['metadata'] and chunk['metadata']['scam_probability'] is not None:
                record['scam_probability'] = float(chunk['metadata']['scam_probability'])
            if 'chunk_scam_probability' in chunk['metadata'] and chunk['metadata']['chunk_scam_probability'] is not None:
                record['chunk_scam_probability'] = float(chunk['metadata']['chunk_scam_probability'])
            
            # Add entity counts
            entities_found = chunk['metadata'].get('entities_found', {})
            for entity_type, count in entities_found.items():
                record[f'{entity_type}_count'] = int(count)
            
            # Add scam label information if available from CSV parsing
            if 'scam_labels' in chunk and chunk['scam_labels']:
                if i < len(chunk['scam_labels']):
                    record['ground_truth_label'] = chunk['scam_labels'][i]
            
            records.append(record)
        
        # Write record_ids to file for future reference
        try:
            with open(vector_ids_path, 'a', encoding='utf-8') as f:
                for record_info in vector_ids_to_store:
                    # Write as JSON for easy parsing later
                    f.write(json.dumps(record_info) + '\n')
            logger.info(f"Stored {len(vector_ids_to_store)} record IDs to {vector_ids_path}")
        except Exception as e:
            logger.warning(f"Failed to write record IDs to file: {str(e)}")
        
        logger.info(f"Prepared {len(records)} records for upsert")
        return records
    
    def upsert_records(self, records: List[Dict[str, Any]], namespace: str = "fraud-detection", batch_size: int = 90) -> Dict[str, Any]:
        """
        Upsert records to Pinecone index using integrated embeddings
        
        Args:
            records: List of records to upsert
            namespace: Namespace to upsert records to
            batch_size: Number of records to upsert in each batch (max 96 for Pinecone)
            
        Returns:
            Dictionary with upsert statistics
        """
        if not self.index:
            raise RuntimeError("Index not initialized. Call create_index_if_not_exists() first.")
        
        if not records:
            logger.warning("No records to upsert")
            return {'upserted': 0, 'failed': 0, 'batches': 0}
        
        total_batches = (len(records) + batch_size - 1) // batch_size
        upserted_count = 0
        failed_count = 0
        
        logger.info(f"Upserting {len(records)} records in {total_batches} batches to namespace '{namespace}'")
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                logger.info(f"Upserting batch {batch_num}/{total_batches} ({len(batch)} records)")
                
                # Upsert batch using integrated embeddings
                upsert_response = self.index.upsert_records(
                    namespace=namespace,
                    records=batch
                )
                
                upserted_count += len(batch)
                logger.info(f"Successfully upserted batch {batch_num}")
                
            except Exception as e:
                logger.error(f"Error upserting batch {batch_num}: {str(e)}")
                failed_count += len(batch)
        
        # Wait a moment for indexing to complete
        time.sleep(2)
        
        # Get updated stats
        stats = self.index.describe_index_stats()
        
        result = {
            'upserted': upserted_count,
            'failed': failed_count,
            'batches': total_batches,
            'total_vectors_in_index': stats['total_vector_count'],
            'namespace': namespace
        }
        
        logger.info(f"Upsert complete. Upserted: {upserted_count}, Failed: {failed_count}, "
                   f"Total in index: {stats['total_vector_count']}")
        
        return result
    
    def process_and_index_document(self, chunks_with_metadata: List[Dict[str, Any]], namespace: str = "fraud-detection") -> Dict[str, Any]:
        """
        Complete pipeline to process and index a document using integrated embeddings
        
        Args:
            chunks_with_metadata: Processed chunks with metadata (no embeddings needed)
            namespace: Namespace to store records in
            
        Returns:
            Dictionary with indexing results
        """
        if not chunks_with_metadata:
            return {'error': 'No chunks provided'}
        
        try:
            # Ensure connection to index
            if not self.index:
                self.connect_to_index()
            
            # Prepare records
            records = self.prepare_records_for_upsert(chunks_with_metadata)
            
            # Upsert records
            upsert_result = self.upsert_records(records, namespace)
            
            # Add document info to result
            document_name = chunks_with_metadata[0]['metadata'].get('document_name', 'unknown')
            result = {
                'document_name': document_name,
                'chunks_processed': len(chunks_with_metadata),
                'records_prepared': len(records),
                **upsert_result,
                'index_host': self.index_host,
                'embedding_model': self.embedding_model,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully indexed document '{document_name}' with {len(records)} chunks using integrated embeddings")
            return result
            
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            return {'error': str(e)}
    
    def search_similar(self, 
                      query_text: str, 
                      top_k: int = 10, 
                      namespace: str = "fraud-detection",
                      filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar records using text query (integrated embeddings)
        
        Args:
            query_text: Text query to search for
            top_k: Number of similar records to return
            namespace: Namespace to search in
            filter_dict: Metadata filters to apply
            
        Returns:
            List of similar records with metadata and scores
        """
        if not self.index:
            raise RuntimeError("Index not initialized")
        
        try:
            # Search using text query (Pinecone will handle embedding generation)
            response = self.index.query(
                query_text=query_text,  # Use query_text instead of vector
                top_k=top_k,
                namespace=namespace,
                include_metadata=True,
                filter=filter_dict
            )
            
            results = []
            for match in response['matches']:
                results.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match.get('metadata', {}),
                    'text': match.get('metadata', {}).get('chunk_text', '')
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
                'index_host': self.index_host,
                'total_vector_count': stats['total_vector_count'],
                'embedding_model': self.embedding_model,
                'index_fullness': stats.get('index_fullness', 0),
                'namespaces': stats.get('namespaces', {})
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {'error': str(e)}
