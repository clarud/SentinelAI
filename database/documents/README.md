# Place your documents here for fraud detection processing

This folder is where you should place documents that you want to process through the fraud detection pipeline.

## Supported File Types

- **PDF files** (.pdf): Email PDFs, invoices, reports, forms
- **CSV files** (.csv): Data exports, transaction logs, contact lists  
- **Text files** (.txt): Email messages, chat logs, transcripts

## Example Files to Test

You can test the system with various types of documents:

### Suspicious Documents
- Phishing emails saved as PDF
- Scam letters or messages
- Fraudulent invoices or receipts
- Suspicious investment opportunities

### Legitimate Documents  
- Normal business emails
- Legitimate invoices and receipts
- Company newsletters
- Official notifications

## Processing

Once you've added documents to this folder, run:

```bash
python fraud_detection_pipeline.py
```

The system will:
1. Parse each document
2. Normalize and clean the text
3. Split into chunks
4. Analyze for fraud indicators
5. Generate embeddings
6. Index to the vector database

Results will be logged and saved to the vector database for similarity search and analysis.
