import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from database.document_parser import DocumentParser

# Initialize the parser
parser = DocumentParser()

# Directory containing CSV files
csv_dir = os.path.join(os.path.dirname(__file__), '..', 'database', 'documents')

print("Enhanced CSV Parsing - Scam Label Detection")
print("=" * 50)

for filename in os.listdir(csv_dir):
    if filename.lower().endswith('.csv'):
        file_path = os.path.join(csv_dir, filename)
        try:
            # First check file size
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            print(f"\nFile: {filename} ({file_size:.1f} MB)")
            
            if file_size > 50:  # Skip files larger than 50MB
                print("  ⚠️  Skipping large file (>50MB)")
                continue
            
            # Load just a sample for large files
            if file_size > 10:
                df_sample = pd.read_csv(file_path, nrows=1000)
                print(f"  📊 Analyzing sample (first 1000 rows)")
            else:
                df_sample = pd.read_csv(file_path)
                print(f"  📊 Analyzing full file")
            
            print(f"  Rows: {len(df_sample)}")
            print(f"  Columns: {list(df_sample.columns)}")
            
            # Check for scam labels using our detection method
            scam_info = parser._detect_scam_label_columns(df_sample)
            if scam_info['has_scam_labels']:
                print(f"  ✓ Scam labels detected in column(s): {scam_info['scam_columns']}")
                print(f"    Distribution: {scam_info['scam_distribution']}")
            else:
                print("  ✗ No scam label columns detected")
                
        except Exception as e:
            print(f"  ❌ Error processing {filename}: {e}")

print("\n" + "=" * 50)
print("Enhanced parsing complete!")
