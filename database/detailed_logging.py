"""
Detailed logging utility for tracking CSV processing issues
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List

class DetailedLogger:
    """Enhanced logger for tracking CSV processing with detailed statistics"""
    
    def __init__(self, log_name: str = "csv_processing"):
        # Create logs directory
        self.logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Create timestamped log files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.main_log = os.path.join(self.logs_dir, f"{log_name}_{timestamp}.log")
        self.stats_log = os.path.join(self.logs_dir, f"{log_name}_stats_{timestamp}.json")
        self.failures_log = os.path.join(self.logs_dir, f"{log_name}_failures_{timestamp}.log")
        
        # Setup main logger
        self.logger = logging.getLogger(f"{log_name}_detailed")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(self.main_log, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for important info only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Initialize tracking stats
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'files_processed': [],
            'total_rows_parsed': 0,
            'total_rows_processed': 0,
            'total_rows_indexed': 0,
            'total_rows_failed': 0,
            'failures_by_stage': {
                'parsing': 0,
                'normalization': 0,
                'metadata_tagging': 0,
                'indexing_preparation': 0,
                'pinecone_upsert': 0
            },
            'pinecone_operations': {
                'batches_attempted': 0,
                'batches_successful': 0,
                'batches_failed': 0,
                'vectors_attempted': 0,
                'vectors_successful': 0,
                'vectors_failed': 0
            }
        }
        
        self.logger.info(f"Detailed logging initialized. Logs saved to:")
        self.logger.info(f"  Main log: {self.main_log}")
        self.logger.info(f"  Stats: {self.stats_log}")
        self.logger.info(f"  Failures: {self.failures_log}")
    
    def log_file_start(self, filename: str, total_rows: int):
        """Log start of file processing"""
        file_info = {
            'filename': filename,
            'start_time': datetime.now().isoformat(),
            'total_rows': total_rows,
            'rows_processed': 0,
            'rows_indexed': 0,
            'rows_failed': 0,
            'status': 'processing'
        }
        self.stats['files_processed'].append(file_info)
        self.stats['total_rows_parsed'] += total_rows
        self.logger.info(f"Starting processing file: {filename} ({total_rows} rows)")
    
    def log_row_failure(self, filename: str, row_index: int, stage: str, error: str):
        """Log individual row failure"""
        self.stats['failures_by_stage'][stage] += 1
        self.stats['total_rows_failed'] += 1
        
        failure_info = {
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'row_index': row_index,
            'stage': stage,
            'error': str(error)
        }
        
        # Log to failures file
        with open(self.failures_log, 'a', encoding='utf-8') as f:
            f.write(f"{json.dumps(failure_info)}\\n")
        
        self.logger.debug(f"Row {row_index} failed at {stage}: {error}")
    
    def log_row_success(self, filename: str, row_index: int):
        """Log successful row processing"""
        self.stats['total_rows_processed'] += 1
        self.logger.debug(f"Row {row_index} processed successfully")
    
    def log_pinecone_batch_start(self, batch_num: int, batch_size: int):
        """Log start of Pinecone batch operation"""
        self.stats['pinecone_operations']['batches_attempted'] += 1
        self.stats['pinecone_operations']['vectors_attempted'] += batch_size
        self.logger.info(f"Starting Pinecone batch {batch_num} with {batch_size} vectors")
    
    def log_pinecone_batch_success(self, batch_num: int, vectors_upserted: int):
        """Log successful Pinecone batch operation"""
        self.stats['pinecone_operations']['batches_successful'] += 1
        self.stats['pinecone_operations']['vectors_successful'] += vectors_upserted
        self.stats['total_rows_indexed'] += vectors_upserted
        self.logger.info(f"Batch {batch_num} successful: {vectors_upserted} vectors upserted")
    
    def log_pinecone_batch_failure(self, batch_num: int, batch_size: int, error: str):
        """Log failed Pinecone batch operation"""
        self.stats['pinecone_operations']['batches_failed'] += 1
        self.stats['pinecone_operations']['vectors_failed'] += batch_size
        
        failure_info = {
            'timestamp': datetime.now().isoformat(),
            'batch_num': batch_num,
            'batch_size': batch_size,
            'error': str(error)
        }
        
        with open(self.failures_log, 'a', encoding='utf-8') as f:
            f.write(f"BATCH_FAILURE: {json.dumps(failure_info)}\\n")
        
        self.logger.error(f"Batch {batch_num} failed ({batch_size} vectors): {error}")
    
    def log_file_complete(self, filename: str, rows_processed: int, rows_indexed: int, rows_failed: int):
        """Log completion of file processing"""
        for file_info in self.stats['files_processed']:
            if file_info['filename'] == filename:
                file_info['end_time'] = datetime.now().isoformat()
                file_info['rows_processed'] = rows_processed
                file_info['rows_indexed'] = rows_indexed
                file_info['rows_failed'] = rows_failed
                file_info['status'] = 'completed'
                break
        
        self.logger.info(f"File {filename} completed: {rows_processed} processed, {rows_indexed} indexed, {rows_failed} failed")
    
    def save_final_stats(self):
        """Save final statistics"""
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['success_rate'] = (self.stats['total_rows_indexed'] / self.stats['total_rows_parsed'] * 100) if self.stats['total_rows_parsed'] > 0 else 0
        
        try:
            with open(self.stats_log, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Final statistics saved to: {self.stats_log}")
        except Exception as e:
            self.logger.error(f"Error saving statistics: {e}")
    
    def print_summary(self):
        """Print final summary"""
        print(f"\\n📊 DETAILED PROCESSING SUMMARY:")
        print(f"  Files processed: {len(self.stats['files_processed'])}")
        print(f"  Total rows parsed: {self.stats['total_rows_parsed']}")
        print(f"  Total rows processed: {self.stats['total_rows_processed']}")
        print(f"  Total rows indexed: {self.stats['total_rows_indexed']}")
        print(f"  Total rows failed: {self.stats['total_rows_failed']}")
        print(f"  Success rate: {self.stats.get('success_rate', 0):.1f}%")
        
        print(f"\\n❌ FAILURES BY STAGE:")
        for stage, count in self.stats['failures_by_stage'].items():
            if count > 0:
                print(f"  {stage}: {count}")
        
        print(f"\\n🔄 PINECONE OPERATIONS:")
        ops = self.stats['pinecone_operations']
        print(f"  Batches attempted: {ops['batches_attempted']}")
        print(f"  Batches successful: {ops['batches_successful']}")
        print(f"  Batches failed: {ops['batches_failed']}")
        print(f"  Vectors attempted: {ops['vectors_attempted']}")
        print(f"  Vectors successful: {ops['vectors_successful']}")
        print(f"  Vectors failed: {ops['vectors_failed']}")
        
        print(f"\\n📁 LOG FILES:")
        print(f"  Main log: {self.main_log}")
        print(f"  Statistics: {self.stats_log}")
        print(f"  Failures: {self.failures_log}")
