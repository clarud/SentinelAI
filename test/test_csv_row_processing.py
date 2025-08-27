"""
Test CSV Row Processing Pipeline

This script tests the new CSV row processing functionality where each CSV row
becomes a separate document with its own embedding.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.document_parser import DocumentParser
from database.csv_row_pipeline_integrated import CSVRowPipelineIntegrated

def test_csv_parsing():
    """Test CSV parsing to see individual rows"""
    print("🧪 Testing CSV Row Parsing")
    print("=" * 40)
    
    parser = DocumentParser()
    
    # Test with a small CSV file
    csv_files = [
        "database/documents/Ling.csv",
        "database/documents/Nigerian_Fraud.csv"
    ]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            print(f"\nTesting: {csv_file}")
            try:
                result = parser.parse_document(csv_file)
                
                if result.get('content_type') == 'csv_rows':
                    print(f"✅ Successfully parsed as individual rows")
                    print(f"   Total rows: {result['total_rows']}")
                    print(f"   Columns: {result['file_metadata']['columns']}")
                    
                    # Show first few rows
                    for i, row_doc in enumerate(result['row_documents'][:3]):
                        print(f"   Row {i}: {row_doc['content'][:100]}...")
                        if 'ground_truth_label' in row_doc['metadata']:
                            print(f"           Label: {row_doc['metadata']['ground_truth_label']}")
                else:
                    print(f"❌ Not parsed as CSV rows: {result.get('content_type')}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"⚠️  File not found: {csv_file}")

def test_csv_pipeline():
    """Test the complete CSV row pipeline"""
    print("\n🔄 Testing CSV Row Pipeline")
    print("=" * 40)
    
    try:
        # Initialize pipeline
        pipeline = CSVRowPipelineIntegrated(namespace="test-csv-rows")
        
        # Test with a small CSV file (limit to 5 rows for testing)
        csv_file = "database/documents/Ling.csv"
        
        if os.path.exists(csv_file):
            print(f"\nProcessing: {csv_file} (first 5 rows)")
            result = pipeline.process_csv_file(csv_file, max_rows=5)
            
            if result['processing_status'] == 'success':
                print(f"✅ Successfully processed CSV")
                print(f"   Rows processed: {result['successful_rows']}")
                print(f"   Failed rows: {result['failed_rows']}")
                print(f"   Indexing result: {result['indexing_result']}")
            else:
                print(f"❌ Processing failed: {result.get('error')}")
        else:
            print(f"⚠️  Test file not found: {csv_file}")
            
    except Exception as e:
        print(f"❌ Pipeline error: {e}")

if __name__ == "__main__":
    test_csv_parsing()
    test_csv_pipeline()
