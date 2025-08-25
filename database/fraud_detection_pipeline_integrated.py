"""
Fraud Detection Document Processing Pipeline with Integrated Embeddings

This module provides a complete pipeline for processing documents for fraud detection,
including parsing, normalization, chunking, metadata tagging, and vector database indexing
using Pinecone's integrated embeddings (no separate embedding generation needed).
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from document_parser import DocumentParser
from data_normalizer import DataNormalizer
from document_chunker import DocumentChunker
from metadata_tagger_2 import MetadataTagger  # Using version 2 with unknown risk levels
from vector_indexer_integrated import VectorIndexerIntegrated

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fraud_detection_pipeline_integrated.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FraudDetectionPipelineIntegrated:
    """Complete fraud detection document processing pipeline with integrated embeddings"""
    
    def __init__(self, 
                 documents_dir: str = "documents",
                 namespace: str = "fraud-detection"):
        """
        Initialize the fraud detection pipeline
        
        Args:
            documents_dir: Directory containing documents to process
            namespace: Pinecone namespace to store vectors in
        """
        self.documents_dir = Path(documents_dir)
        self.namespace = namespace
        
        # Initialize components
        self.parser = DocumentParser()
        self.normalizer = DataNormalizer()
        self.chunker = DocumentChunker()
        self.tagger = MetadataTagger()
        self.indexer = VectorIndexerIntegrated()
        
        logger.info("Fraud Detection Pipeline with Integrated Embeddings initialized")
    
    def process_single_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single document through the complete pipeline
        
        Args:
            file_path: Path to the document to process
            
        Returns:
            Dictionary with processing results
        """
        file_path = Path(file_path)
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Step 1: Parse document
            logger.info("Step 1: Parsing document...")
            parsed_doc = self.parser.parse_document(str(file_path))
            
            # Step 2: Normalize data
            logger.info("Step 2: Normalizing data...")
            normalized_doc = self.normalizer.normalize_document(parsed_doc)
            
            # Step 3: Chunk document
            logger.info("Step 3: Chunking document...")
            chunked_doc = self.chunker.chunk_document(normalized_doc)
            
            # Step 4: Tag metadata (sets risk_level to 'unknown')
            logger.info("Step 4: Tagging metadata...")
            tagged_doc = self.tagger.create_metadata(chunked_doc)
            
            # Step 5: Index in vector database (no separate embedding step needed)
            logger.info("Step 5: Indexing in vector database with integrated embeddings...")
            
            # Ensure index exists
            self.indexer.create_index_if_not_exists()
            
            # Process and index (Pinecone will generate embeddings automatically)
            indexing_result = self.indexer.process_and_index_document(
                tagged_doc['chunks_with_metadata'], 
                namespace=self.namespace
            )
            
            result = {
                'file_path': str(file_path),
                'document_name': file_path.name,
                'processing_status': 'success',
                'chunks_created': len(tagged_doc['chunks_with_metadata']),
                'indexing_result': indexing_result,
                'processing_summary': tagged_doc['processing_summary'],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully processed {file_path.name}: "
                       f"{result['chunks_created']} chunks indexed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return {
                'file_path': str(file_path),
                'document_name': file_path.name,
                'processing_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def process_directory(self, directory_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all supported documents in a directory
        
        Args:
            directory_path: Path to directory (uses self.documents_dir if None)
            
        Returns:
            Dictionary with overall processing results
        """
        if directory_path:
            directory = Path(directory_path)
        else:
            directory = self.documents_dir
        
        logger.info(f"Processing documents in directory: {directory}")
        
        if not directory.exists():
            error_msg = f"Directory {directory} does not exist"
            logger.error(error_msg)
            return {'error': error_msg}
        
        # Find all supported files
        supported_files = []
        for ext in self.parser.supported_formats:
            supported_files.extend(directory.glob(f"*{ext}"))
        
        if not supported_files:
            logger.warning(f"No supported files found in {directory}")
            return {
                'directory': str(directory),
                'total_files': 0,
                'processed_files': 0,
                'failed_files': 0,
                'results': []
            }
        
        logger.info(f"Found {len(supported_files)} supported files")
        
        # Process each file
        results = []
        successful_count = 0
        failed_count = 0
        
        for file_path in supported_files:
            logger.info(f"Processing file {len(results) + 1}/{len(supported_files)}: {file_path.name}")
            
            result = self.process_single_document(file_path)
            results.append(result)
            
            if result['processing_status'] == 'success':
                successful_count += 1
            else:
                failed_count += 1
        
        # Compile overall results
        overall_result = {
            'directory': str(directory),
            'total_files': len(supported_files),
            'processed_files': successful_count,
            'failed_files': failed_count,
            'namespace': self.namespace,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Get final index stats
        try:
            index_stats = self.indexer.get_index_stats()
            overall_result['final_index_stats'] = index_stats
        except Exception as e:
            logger.warning(f"Could not get final index stats: {str(e)}")
        
        logger.info(f"Directory processing complete. "
                   f"Processed: {successful_count}, Failed: {failed_count}")
        
        return overall_result
    
    def search_documents(self, 
                        query: str, 
                        top_k: int = 10, 
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search indexed documents using text query
        
        Args:
            query: Text query to search for
            top_k: Number of results to return
            filters: Metadata filters to apply
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for: '{query}' (top {top_k} results)")
        
        try:
            results = self.indexer.search_similar(
                query_text=query,
                top_k=top_k,
                namespace=self.namespace,
                filter_dict=filters
            )
            
            logger.info(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current status of the pipeline and index"""
        try:
            index_stats = self.indexer.get_index_stats()
            
            return {
                'pipeline_status': 'healthy',
                'index_stats': index_stats,
                'documents_directory': str(self.documents_dir),
                'namespace': self.namespace,
                'supported_formats': self.parser.supported_formats,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'pipeline_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

def main():
    """Main function to run the pipeline"""
    print("🚀 Fraud Detection Pipeline with Integrated Embeddings")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = FraudDetectionPipelineIntegrated()
    
    # Check pipeline status
    status = pipeline.get_pipeline_status()
    print(f"Pipeline Status: {status['pipeline_status']}")
    
    if status['pipeline_status'] == 'error':
        print(f"Error: {status['error']}")
        return
    
    # Process all documents in the documents directory
    print(f"\\nProcessing documents from: {pipeline.documents_dir}")
    results = pipeline.process_directory()
    
    # Print summary
    print(f"\\n📊 Processing Summary:")
    print(f"  Total files: {results['total_files']}")
    print(f"  Successfully processed: {results['processed_files']}")
    print(f"  Failed: {results['failed_files']}")
    
    if 'final_index_stats' in results:
        print(f"\\n📈 Final Index Stats:")
        stats = results['final_index_stats']
        print(f"  Total vectors: {stats['total_vector_count']}")
        print(f"  Index: {stats['index_name']}")
        print(f"  Embedding model: {stats['embedding_model']}")
    
    print(f"\\n✅ Pipeline completed! Check fraud_detection_pipeline_integrated.log for details.")

if __name__ == "__main__":
    main()
