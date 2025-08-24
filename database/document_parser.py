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
        """Parse CSV file and convert to text content"""
        try:
            df = pd.read_csv(file_path)
            
            # Convert DataFrame to text representation
            text_content = df.to_string(index=False)
            
            # Detect scam label columns
            scam_label_info = self._detect_scam_label_columns(df)
            
            # Extract basic metadata
            metadata = {
                'columns': list(df.columns),
                'row_count': len(df),
                'column_count': len(df.columns),
                'data_types': df.dtypes.to_dict(),
                'scam_label_info': scam_label_info
            }
            
            return {
                'content': text_content,
                'metadata': metadata,
                'dataframe': df,  # Keep original DataFrame for potential future use
                'scam_labels': scam_label_info.get('labels', []) if scam_label_info['has_scam_labels'] else None
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
        Detect columns that contain scam labels (0/1 values)
        
        Args:
            df: Pandas DataFrame to analyze
            
        Returns:
            Dictionary with scam label information
        """
        # Possible column names that might contain scam labels
        scam_column_names = ['class', 'label', 'target', 'scam', 'fraud', 'is_scam', 
                            'is_fraud', 'spam', 'malicious', 'phishing', 'classification']
        
        scam_info = {
            'has_scam_labels': False,
            'scam_columns': [],
            'labels': [],
            'scam_distribution': {}
        }
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Check if column name suggests it's a label column
            is_potential_label_col = any(name in col_lower for name in scam_column_names)
            
            # Check if column contains only 0s and 1s (or mostly 0s and 1s)
            unique_values = df[col].dropna().unique()
            contains_binary = all(str(val).strip() in ['0', '1', '0.0', '1.0'] for val in unique_values)
            
            if is_potential_label_col and contains_binary:
                scam_info['has_scam_labels'] = True
                scam_info['scam_columns'].append(col)
                
                # Convert labels to readable format
                labels = []
                for _, row in df.iterrows():
                    value = str(row[col]).strip()
                    if value in ['1', '1.0']:
                        labels.append('scam')
                    elif value in ['0', '0.0']:
                        labels.append('not_scam')
                    else:
                        labels.append('unknown')
                
                scam_info['labels'] = labels
                
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
                
                logger.info(f"Detected scam label column '{col}': {scam_count} scam, {not_scam_count} not_scam")
                break  # Use the first matching column
        
        return scam_info
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if file format is supported"""
        return Path(file_path).suffix.lower() in self.supported_formats
