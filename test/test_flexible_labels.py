import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.document_parser import DocumentParser

# Create test dataframes with different label formats
test_cases = [
    # Binary numeric
    pd.DataFrame({
        'text': ['email content 1', 'email content 2', 'email content 3'],
        'label': [0, 1, 0]
    }),
    
    # Text labels - scam/not_scam
    pd.DataFrame({
        'content': ['suspicious email', 'normal email', 'phishing attempt'],
        'classification': ['scam', 'not_scam', 'scam']
    }),
    
    # Text labels - real/fake
    pd.DataFrame({
        'message': ['legitimate message', 'fraudulent message', 'normal message'],
        'type': ['real', 'fake', 'real']
    }),
    
    # Text labels - spam/ham
    pd.DataFrame({
        'email_text': ['offer money now', 'meeting tomorrow', 'click here win'],
        'category': ['spam', 'ham', 'spam']
    }),
    
    # Mixed case and variations
    pd.DataFrame({
        'document': ['doc1', 'doc2', 'doc3', 'doc4'],
        'fraud': ['YES', 'no', 'True', 'FALSE']
    })
]

parser = DocumentParser()

print("Testing Enhanced Scam Label Detection")
print("=" * 50)

for i, df in enumerate(test_cases, 1):
    print(f"\nTest Case {i}:")
    print(f"Columns: {list(df.columns)}")
    print(f"Sample values: {df.iloc[:, -1].tolist()}")  # Last column values
    
    result = parser._detect_scam_label_columns(df)
    
    if result['has_scam_labels']:
        print(f"✓ Labels detected in column: {result['scam_columns'][0]}")
        print(f"  Format: {result['detected_format']}")
        print(f"  Distribution: {result['scam_distribution']}")
        print(f"  Converted labels: {result['labels']}")
    else:
        print("✗ No scam labels detected")

print("\n" + "=" * 50)
print("Enhanced detection complete!")
