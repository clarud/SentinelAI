"""
Fraud Detection CSV Row Processing Pipeline with Integrated Embeddings

This module provides a specialized pipeline for processing CSV files where each row
represents a separate document for fraud detection analysis.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from document_parser import DocumentParser
from data_normalizer import DataNormalizer
from metadata_tagger_2 import MetadataTagger
from vector_indexer_integrated import VectorIndexerIntegrated

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('csv_row_pipeline_integrated.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CSVRowPipelineIntegrated:
    """Specialized pipeline for processing CSV files where each row is a separate document"""
    
    def __init__(self, 
                 documents_dir: str = "documents",
                 namespace: str = "fraud-detection-csv"):
        """
        Initialize the CSV row processing pipeline
        
        Args:
            documents_dir: Directory containing CSV files to process
            namespace: Pinecone namespace to store vectors in
        """
        self.documents_dir = Path(documents_dir)
        self.namespace = namespace
        
        # Initialize components
        self.parser = DocumentParser()
        self.normalizer = DataNormalizer()
        self.tagger = MetadataTagger()
        self.indexer = VectorIndexerIntegrated()
        
        logger.info("CSV Row Pipeline with Integrated Embeddings initialized")
    
    def process_single_csv_row(self, 
                              row_document: Dict[str, Any], 
                              csv_filename: str,
                              file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single CSV row as an individual document
        
        Args:
            row_document: Individual row data with content and metadata
            csv_filename: Name of the source CSV file
            file_info: File information metadata
            
        Returns:
            Dictionary with processed row ready for indexing
        """
        try:
            # Create a document structure for this row
            row_doc = {
                'content': row_document['content'],
                'metadata': row_document['metadata'],
                'file_info': {
                    **file_info,
                    'filename': f"{csv_filename}_row_{row_document['row_index']}",
                    'source_csv': csv_filename,
                    'row_index': row_document['row_index']
                }
            }
            
            # Step 1: Normalize the row data
            normalized_row = self.normalizer.normalize_document(row_doc)
            
            # Step 2: Create "chunks" (for CSV rows, each row is typically one chunk)
            chunked_row = {
                'chunks': [{
                    'chunk_id': f"row_{row_document['row_index']}",
                    'text': normalized_row['content'],
                    'chunk_size': len(normalized_row['content']),
                    'start_position': 0,
                    'end_position': len(normalized_row['content']),
                    'chunking_method': 'csv_row'
                }],
                'chunk_count': 1,
                'total_characters': len(normalized_row['content']),
                'original_document': normalized_row
            }
            
            # Step 3: Tag metadata
            tagged_row = self.tagger.create_metadata(chunked_row)
            
            return {
                'chunks_with_metadata': tagged_row['chunks_with_metadata'],
                'processing_status': 'success',
                'row_index': row_document['row_index']
            }
            
        except Exception as e:
            logger.error(f"Error processing row {row_document['row_index']}: {str(e)}")
            return {
                'processing_status': 'error',
                'error': str(e),
                'row_index': row_document['row_index']
            }
    
    def process_csv_file(self, file_path: str, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a CSV file where each row becomes a separate document
        
        Args:
            file_path: Path to the CSV file
            max_rows: Maximum number of rows to process (for testing/limiting)
            
        Returns:
            Dictionary with processing results
        """
        file_path = Path(file_path)
        logger.info(f"Processing CSV file: {file_path}")
        
        try:
            # Step 1: Parse CSV file into individual row documents
            logger.info("Step 1: Parsing CSV into individual row documents...")
            parsed_csv = self.parser.parse_document(str(file_path))
            
            if parsed_csv.get('content_type') != 'csv_rows':
                # Fall back to regular document processing for non-CSV files
                logger.warning(f"File {file_path} is not a CSV or doesn't contain row data")
                return {'error': 'Not a valid CSV file for row processing'}
            
            row_documents = parsed_csv['row_documents']
            total_rows = len(row_documents)
            
            # Limit rows if specified
            if max_rows and max_rows < total_rows:
                row_documents = row_documents[:max_rows]
                logger.info(f"Processing first {max_rows} rows out of {total_rows}")
            
            logger.info(f"Found {len(row_documents)} rows to process")
            
            # Step 2: Process each row individually
            processed_rows = []
            successful_rows = 0
            failed_rows = 0
            
            file_info = {
                'filename': file_path.name,
                'filepath': str(file_path),
                'file_size': file_path.stat().st_size,
                'file_extension': '.csv',
                'creation_time': file_path.stat().st_ctime,
                'modification_time': file_path.stat().st_mtime
            }
            
            for i, row_doc in enumerate(row_documents):
                if i % 100 == 0:  # Log progress every 100 rows
                    logger.info(f"Processing row {i+1}/{len(row_documents)}")
                
                processed_row = self.process_single_csv_row(row_doc, file_path.stem, file_info)
                processed_rows.append(processed_row)
                
                if processed_row['processing_status'] == 'success':
                    successful_rows += 1
                else:
                    failed_rows += 1
            
            # Step 3: Collect all successful rows for indexing
            all_chunks_for_indexing = []
            for processed_row in processed_rows:
                if processed_row['processing_status'] == 'success':
                    all_chunks_for_indexing.extend(processed_row['chunks_with_metadata'])
            
            # Step 4: Index all chunks in the vector database
            logger.info(f"Step 4: Indexing {len(all_chunks_for_indexing)} rows in vector database...")
            
            # Ensure connection to index
            self.indexer.connect_to_index()
            
            # Index all rows
            indexing_result = self.indexer.process_and_index_document(
                all_chunks_for_indexing, 
                namespace=self.namespace
            )
            
            result = {
                'file_path': str(file_path),
                'csv_filename': file_path.name,
                'processing_status': 'success',
                'total_rows_in_file': total_rows,
                'rows_processed': len(row_documents),
                'successful_rows': successful_rows,
                'failed_rows': failed_rows,
                'indexing_result': indexing_result,
                'file_metadata': parsed_csv['file_metadata'],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully processed CSV {file_path.name}: "
                       f"{successful_rows} rows indexed, {failed_rows} failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {str(e)}")
            return {
                'file_path': str(file_path),
                'csv_filename': file_path.name,
                'processing_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def process_csv_directory(self, directory_path: Optional[str] = None, max_rows_per_file: Optional[int] = None) -> Dict[str, Any]:
        """
        Process all CSV files in a directory
        
        Args:
            directory_path: Path to directory (uses self.documents_dir if None)
            max_rows_per_file: Maximum rows to process per CSV file
            
        Returns:
            Dictionary with overall processing results
        """
        if directory_path:
            directory = Path(directory_path)
        else:
            directory = self.documents_dir
        
        logger.info(f"Processing CSV files in directory: {directory}")
        
        if not directory.exists():
            error_msg = f"Directory {directory} does not exist"
            logger.error(error_msg)
            return {'error': error_msg}
        
        # Find all CSV files
        csv_files = list(directory.glob("*.csv"))
        
        if not csv_files:
            logger.warning(f"No CSV files found in {directory}")
            return {
                'directory': str(directory),
                'total_files': 0,
                'processed_files': 0,
                'failed_files': 0,
                'results': []
            }
        
        logger.info(f"Found {len(csv_files)} CSV files")
        
        # Process each CSV file
        results = []
        successful_files = 0
        failed_files = 0
        total_rows_processed = 0
        
        for i, csv_file in enumerate(csv_files):
            logger.info(f"Processing CSV file {i+1}/{len(csv_files)}: {csv_file.name}")
            
            result = self.process_csv_file(csv_file, max_rows_per_file)
            results.append(result)
            
            if result['processing_status'] == 'success':
                successful_files += 1
                total_rows_processed += result.get('successful_rows', 0)
            else:
                failed_files += 1
        
        # Compile overall results
        overall_result = {
            'directory': str(directory),
            'total_csv_files': len(csv_files),
            'processed_files': successful_files,
            'failed_files': failed_files,
            'total_rows_processed': total_rows_processed,
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
        
        logger.info(f"CSV directory processing complete. "
                   f"Files processed: {successful_files}, Failed: {failed_files}, "
                   f"Total rows: {total_rows_processed}")
        
        return overall_result
    
    def search_csv_rows(self, 
                       query: str, 
                       top_k: int = 10, 
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search indexed CSV rows using text query
        
        Args:
            query: Text query to search for
            top_k: Number of results to return
            filters: Metadata filters to apply
            
        Returns:
            List of search results
        """
        logger.info(f"Searching CSV rows for: '{query}' (top {top_k} results)")
        
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
            logger.error(f"Error searching CSV rows: {str(e)}")
            return []

def main():
    """Main function to run the CSV row pipeline"""
    print("🚀 CSV Row Processing Pipeline with Integrated Embeddings")
    print("=" * 70)
    
    # Initialize pipeline
    pipeline = CSVRowPipelineIntegrated()
    
    # Process all CSV files in the documents directory
    print(f"\\nProcessing CSV files from: {pipeline.documents_dir}")
    print("Note: Each CSV row will be treated as a separate document")
    
    # For testing, limit to 1000 rows per file
    results = pipeline.process_csv_directory(max_rows_per_file=1000)
    
    # Print summary
    print(f"\\n📊 Processing Summary:")
    print(f"  Total CSV files: {results['total_csv_files']}")
    print(f"  Successfully processed: {results['processed_files']}")
    print(f"  Failed: {results['failed_files']}")
    print(f"  Total rows processed: {results['total_rows_processed']}")
    
    if 'final_index_stats' in results:
        print(f"\\n📈 Final Index Stats:")
        stats = results['final_index_stats']
        print(f"  Total vectors: {stats['total_vector_count']}")
        print(f"  Index: {stats['index_name']}")
        print(f"  Embedding model: {stats['embedding_model']}")
    
    print(f"\\n✅ CSV pipeline completed! Check csv_row_pipeline_integrated.log for details.")
    
    # Example search
    if results['total_rows_processed'] > 0:
        print(f"\\n🔍 Example search:")
        search_results = pipeline.search_csv_rows("urgent payment", top_k=3)
        for i, result in enumerate(search_results[:3]):
            print(f"  {i+1}. Score: {result['score']:.3f} - {result['text'][:100]}...")

if __name__ == "__main__":
    main()
