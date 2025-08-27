import os
import pandas as pd
import PyPDF2
import io
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentParser:
    """Handles parsing of various document formats (PDF, CSV, TXT)"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.csv', '.txt']
    
    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF file and extract text content"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text() + "\n"
                
                # Extract metadata
                metadata = {}
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                        'modification_date': str(pdf_reader.metadata.get('/ModDate', ''))
                    }
                
                return {
                    'content': text_content.strip(),
                    'metadata': metadata,
                    'page_count': len(pdf_reader.pages)
                }
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise
    
    def parse_csv(self, file_path: str) -> Dict[str, Any]:
        """Parse CSV file and treat each row as a separate document"""
        try:
            # Try to read CSV with different parameters to handle malformed data
            try:
                df = pd.read_csv(file_path)
            except pd.errors.ParserError:
                # Try with different options for malformed CSV
                logger.warning(f"CSV parsing failed, trying with error handling for {file_path}")
                df = pd.read_csv(file_path, on_bad_lines='skip', engine='python')
            except Exception as e:
                # Try with even more lenient parsing
                logger.warning(f"Standard CSV parsing failed, using very lenient parsing for {file_path}")
                df = pd.read_csv(file_path, on_bad_lines='skip', engine='python', quoting=1, skipinitialspace=True)
            
            if df.empty:
                logger.warning(f"CSV file {file_path} is empty or could not be parsed")
                return {
                    'content_type': 'csv_rows',
                    'total_rows': 0,
                    'file_metadata': {},
                    'row_documents': []
                }
            
            # Detect scam label columns
            scam_label_info = self._detect_scam_label_columns(df)
            
            # Extract basic metadata about the CSV file
            file_metadata = {
                'columns': list(df.columns),
                'row_count': len(df),
                'column_count': len(df.columns),
                'data_types': df.dtypes.to_dict(),
                'scam_label_info': scam_label_info
            }
            
            # Convert each row to a separate document
            row_documents = []
            scam_labels = scam_label_info.get('labels', []) if scam_label_info['has_scam_labels'] else []
            
            for idx, row in df.iterrows():
                # Create text content for this row
                row_text_parts = []
                for col in df.columns:
                    value = str(row[col]) if pd.notna(row[col]) else ""
                    if value.strip():  # Only include non-empty values
                        row_text_parts.append(f"{col}: {value}")
                
                row_text = " | ".join(row_text_parts)
                
                # Skip completely empty rows
                if not row_text.strip():
                    logger.warning(f"Skipping empty row {idx} in CSV {file_path}")
                    continue
                
                # Create metadata for this specific row
                row_metadata = {
                    'row_index': int(idx),
                    'csv_columns': list(df.columns),
                    'csv_file_info': file_metadata
                }
                
                # Add ground truth label if available
                if scam_labels and idx < len(scam_labels):
                    row_metadata['ground_truth_label'] = scam_labels[idx]
                
                # Add individual column values to metadata
                for col in df.columns:
                    safe_col_name = col.replace(' ', '_').replace('-', '_').lower()
                    row_metadata[f'col_{safe_col_name}'] = str(row[col]) if pd.notna(row[col]) else ""
                
                row_documents.append({
                    'content': row_text,
                    'metadata': row_metadata,
                    'row_index': int(idx)
                })
            
            return {
                'content_type': 'csv_rows',
                'total_rows': len(row_documents),
                'file_metadata': file_metadata,
                'row_documents': row_documents,
                'dataframe': df  # Keep original DataFrame for reference
            }
            
        except Exception as e:
            logger.error(f"Error parsing CSV {file_path}: {str(e)}")
            raise
    
    def parse_txt(self, file_path: str) -> Dict[str, Any]:
        """Parse plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Basic text statistics as metadata
            metadata = {
                'character_count': len(content),
                'word_count': len(content.split()),
                'line_count': len(content.splitlines())
            }
            
            return {
                'content': content.strip(),
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Error parsing TXT {file_path}: {str(e)}")
            raise
    
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """Main method to parse any supported document format"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        logger.info(f"Parsing document: {file_path}")
        
        if file_extension == '.pdf':
            result = self.parse_pdf(str(file_path))
        elif file_extension == '.csv':
            result = self.parse_csv(str(file_path))
        elif file_extension == '.txt':
            result = self.parse_txt(str(file_path))
        
        # Add file information to result
        result['file_info'] = {
            'filename': file_path.name,
            'filepath': str(file_path),
            'file_size': file_path.stat().st_size,
            'file_extension': file_extension,
            'creation_time': file_path.stat().st_ctime,
            'modification_time': file_path.stat().st_mtime
        }
        
        return result
    
    def _detect_scam_label_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect columns that contain scam labels with flexible value formats
        
        Args:
            df: Pandas DataFrame to analyze
            
        Returns:
            Dictionary with scam label information
        """
        # Possible column names that might contain scam labels
        scam_column_names = ['class', 'label', 'target', 'scam', 'fraud', 'is_scam', 
                            'is_fraud', 'spam', 'malicious', 'phishing', 'classification',
                            'fraudulent', 'type', 'category', 'status', 'result']
        
        # Define mappings for different label formats
        scam_mappings = {
            # Binary numeric
            '1': 'scam', '1.0': 'scam', 1: 'scam', 1.0: 'scam',
            '0': 'not_scam', '0.0': 'not_scam', 0: 'not_scam', 0.0: 'not_scam',
            
            # Text labels (case insensitive)
            'scam': 'scam', 'fraud': 'scam', 'fraudulent': 'scam', 'malicious': 'scam',
            'spam': 'scam', 'phishing': 'scam', 'fake': 'scam', 'bad': 'scam',
            'suspicious': 'scam', 'positive': 'scam', 'yes': 'scam', 'true': 'scam',
            
            'not_scam': 'not_scam', 'legitimate': 'not_scam', 'legit': 'not_scam',
            'real': 'not_scam', 'good': 'not_scam', 'safe': 'not_scam', 'ham': 'not_scam',
            'normal': 'not_scam', 'clean': 'not_scam', 'negative': 'not_scam',
            'no': 'not_scam', 'false': 'not_scam', 'valid': 'not_scam'
        }
        
        scam_info = {
            'has_scam_labels': False,
            'scam_columns': [],
            'labels': [],
            'scam_distribution': {},
            'detected_format': None,
            'original_values': []
        }
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Check if column name suggests it's a label column
            is_potential_label_col = any(name in col_lower for name in scam_column_names)
            
            if is_potential_label_col:
                # Get unique values in the column
                unique_values = df[col].dropna().unique()
                
                # Convert to strings for consistent processing
                unique_str_values = [str(val).strip().lower() for val in unique_values]
                
                # Check if we can map most/all unique values
                mappable_count = 0
                for val in unique_str_values:
                    if val in scam_mappings:
                        mappable_count += 1
                
                # If we can map at least 80% of unique values, consider it a label column
                mapping_ratio = mappable_count / len(unique_str_values) if unique_str_values else 0
                
                if mapping_ratio >= 0.8:
                    scam_info['has_scam_labels'] = True
                    scam_info['scam_columns'].append(col)
                    
                    # Convert labels to readable format
                    labels = []
                    original_values = []
                    
                    for _, row in df.iterrows():
                        original_value = row[col]
                        original_values.append(original_value)
                        
                        # Handle NaN/None values
                        if pd.isna(original_value):
                            labels.append('unknown')
                            continue
                        
                        value_str = str(original_value).strip().lower()
                        
                        if value_str in scam_mappings:
                            labels.append(scam_mappings[value_str])
                        else:
                            labels.append('unknown')
                    
                    scam_info['labels'] = labels
                    scam_info['original_values'] = original_values
                    
                    # Determine the detected format
                    if all(str(val).strip() in ['0', '1', '0.0', '1.0'] for val in unique_values):
                        scam_info['detected_format'] = 'binary_numeric'
                    elif all(isinstance(val, (int, float)) for val in unique_values):
                        scam_info['detected_format'] = 'numeric'
                    else:
                        scam_info['detected_format'] = 'text'
                    
                    # Calculate distribution
                    scam_count = labels.count('scam')
                    not_scam_count = labels.count('not_scam')
                    unknown_count = labels.count('unknown')
                    
                    scam_info['scam_distribution'] = {
                        'scam': scam_count,
                        'not_scam': not_scam_count,
                        'unknown': unknown_count,
                        'total': len(labels)
                    }
                    
                    logger.info(f"Detected scam label column '{col}' (format: {scam_info['detected_format']}): "
                               f"{scam_count} scam, {not_scam_count} not_scam, {unknown_count} unknown")
                    logger.info(f"Original unique values: {list(unique_values)}")
                    break  # Use the first matching column
        
        return scam_info
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if file format is supported"""
        return Path(file_path).suffix.lower() in self.supported_formats
