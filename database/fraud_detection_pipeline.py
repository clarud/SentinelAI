"""
Fraud Detection Document Processing Pipeline

This module provides a complete pipeline for processing documents for fraud detection,
including parsing, normalization, chunking, metadata tagging, embedding generation,
and vector database indexing.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from document_parser import DocumentParser
from data_normalizer import DataNormalizer
from document_chunker import DocumentChunker
from metadata_tagger import MetadataTagger
from embedding_generator import EmbeddingGenerator
from vector_indexer import VectorIndexer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fraud_detection_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FraudDetectionPipeline:
    """Complete pipeline for processing documents for fraud detection"""
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 openai_api_key: Optional[str] = None,
                 pinecone_api_key: Optional[str] = None,
                 pinecone_environment: Optional[str] = None,
                 pinecone_index_name: Optional[str] = None):
        """
        Initialize the fraud detection pipeline
        
        Args:
            chunk_size: Maximum size of text chunks
            chunk_overlap: Overlap between chunks
            openai_api_key: OpenAI API key for embeddings
            pinecone_api_key: Pinecone API key for vector database
            pinecone_environment: Pinecone environment
            pinecone_index_name: Pinecone index name
        """
        
        # Initialize components
        self.parser = DocumentParser()
        self.normalizer = DataNormalizer()
        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.tagger = MetadataTagger()
        
        # Initialize embedding generator (may raise error if OpenAI not available)
        try:
            self.embedding_generator = EmbeddingGenerator(api_key=openai_api_key)
        except Exception as e:
            logger.warning(f"Could not initialize embedding generator: {str(e)}")
            self.embedding_generator = None
        
        # Initialize vector indexer (may raise error if Pinecone not available)
        try:
            self.vector_indexer = VectorIndexer(
                api_key=pinecone_api_key,
                environment=pinecone_environment,
                index_name=pinecone_index_name
            )
        except Exception as e:
            logger.warning(f"Could not initialize vector indexer: {str(e)}")
            self.vector_indexer = None
        
        logger.info("Fraud detection pipeline initialized")
    
    def process_single_document(self, file_path: str, chunking_method: str = "semantic") -> Dict[str, Any]:
        """
        Process a single document through the complete pipeline
        
        Args:
            file_path: Path to the document to process
            chunking_method: Method for chunking ('semantic' or 'overlapping')
            
        Returns:
            Dictionary containing processing results and any errors
        """
        result = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'steps_completed': [],
            'errors': []
        }
        
        try:
            # Step 1: Parse document
            logger.info(f"Step 1: Parsing document {file_path}")
            parsed_doc = self.parser.parse_document(file_path)
            result['steps_completed'].append('parsing')
            logger.info("Document parsing completed")
            
            # Step 2: Normalize data
            logger.info("Step 2: Normalizing data")
            normalized_doc = self.normalizer.normalize_document(parsed_doc)
            result['steps_completed'].append('normalization')
            logger.info("Data normalization completed")
            
            # Step 3: Chunk document
            logger.info("Step 3: Chunking document")
            chunked_doc = self.chunker.chunk_document(normalized_doc, method=chunking_method)
            result['steps_completed'].append('chunking')
            logger.info(f"Document chunking completed: {chunked_doc['chunk_count']} chunks")
            
            # Step 4: Generate metadata
            logger.info("Step 4: Generating metadata")
            tagged_doc = self.tagger.create_metadata(chunked_doc)
            result['steps_completed'].append('metadata_tagging')
            result['document_metadata'] = tagged_doc['document_metadata']
            result['processing_summary'] = tagged_doc['processing_summary']
            logger.info("Metadata generation completed")
            
            # Step 5: Generate embeddings (if available)
            if self.embedding_generator:
                logger.info("Step 5: Generating embeddings")
                chunks_with_embeddings = self.embedding_generator.process_chunks_with_embeddings(
                    tagged_doc['chunks_with_metadata']
                )
                result['steps_completed'].append('embedding_generation')
                logger.info("Embedding generation completed")
            else:
                logger.warning("Embedding generator not available, skipping embedding generation")
                chunks_with_embeddings = tagged_doc['chunks_with_metadata']
                result['errors'].append("Embedding generator not available")
            
            # Step 6: Index to vector database (if available)
            if self.vector_indexer and 'embedding_generation' in result['steps_completed']:
                logger.info("Step 6: Indexing to vector database")
                indexing_result = self.vector_indexer.process_and_index_document(chunks_with_embeddings)
                result['steps_completed'].append('vector_indexing')
                result['indexing_result'] = indexing_result
                logger.info("Vector indexing completed")
            else:
                if not self.vector_indexer:
                    logger.warning("Vector indexer not available, skipping vector indexing")
                    result['errors'].append("Vector indexer not available")
                else:
                    logger.warning("Embeddings not generated, skipping vector indexing")
                    result['errors'].append("Embeddings not available for indexing")
            
            result['success'] = True
            logger.info(f"Document processing completed successfully: {file_path}")
            
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            result['success'] = False
        
        return result
    
    def process_directory(self, directory_path: str, chunking_method: str = "semantic") -> Dict[str, Any]:
        """
        Process all supported documents in a directory
        
        Args:
            directory_path: Path to directory containing documents
            chunking_method: Method for chunking documents
            
        Returns:
            Dictionary containing results for all processed documents
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            return {'error': f"Directory not found: {directory_path}"}
        
        logger.info(f"Processing directory: {directory_path}")
        
        # Find all supported files
        supported_files = []
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and self.parser.is_supported_format(str(file_path)):
                supported_files.append(file_path)
        
        if not supported_files:
            return {'error': 'No supported files found in directory'}
        
        logger.info(f"Found {len(supported_files)} supported files")
        
        results = {
            'directory_path': str(directory_path),
            'total_files': len(supported_files),
            'processed_files': [],
            'successful_files': 0,
            'failed_files': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        # Process each file
        for file_path in supported_files:
            logger.info(f"Processing file: {file_path}")
            file_result = self.process_single_document(str(file_path), chunking_method)
            results['processed_files'].append(file_result)
            
            if file_result['success']:
                results['successful_files'] += 1
            else:
                results['failed_files'] += 1
        
        logger.info(f"Directory processing completed. Success: {results['successful_files']}, "
                   f"Failed: {results['failed_files']}")
        
        return results
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get status of all pipeline components"""
        status = {
            'parser': 'available',
            'normalizer': 'available',
            'chunker': 'available',
            'metadata_tagger': 'available',
            'embedding_generator': 'not_available',
            'vector_indexer': 'not_available'
        }
        
        if self.embedding_generator:
            status['embedding_generator'] = 'available'
            status['embedding_info'] = self.embedding_generator.get_embedding_info()
        
        if self.vector_indexer:
            status['vector_indexer'] = 'available'
            status['index_stats'] = self.vector_indexer.get_index_stats()
        
        return status


def main():
    """Example usage of the fraud detection pipeline"""
    
    # Initialize pipeline
    pipeline = FraudDetectionPipeline()
    
    # Check pipeline status
    status = pipeline.get_pipeline_status()
    print("Pipeline Status:")
    for component, stat in status.items():
        print(f"  {component}: {stat}")
    
    # Process documents directory
    documents_dir = os.path.join(os.path.dirname(__file__), 'documents')
    
    if os.path.exists(documents_dir):
        print(f"\nProcessing documents in: {documents_dir}")
        results = pipeline.process_directory(documents_dir)
        
        if 'error' in results:
            print(f"Error: {results['error']}")
        else:
            print(f"Processed {results['total_files']} files")
            print(f"Successful: {results['successful_files']}")
            print(f"Failed: {results['failed_files']}")
    else:
        print(f"Documents directory not found: {documents_dir}")
        print("Please add documents to the 'documents' folder and run again.")


if __name__ == "__main__":
    main()
