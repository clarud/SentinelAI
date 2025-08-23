# Fraud Detection Document Processing System

This system provides a complete pipeline for processing documents (PDFs, CSVs, text files) for fraud detection, including document parsing, data normalization, chunking, metadata tagging, embedding generation, and vector database indexing.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=fraud-detection-docs
```

### 3. Add Documents

Place your documents (PDF, CSV, TXT files) in the `documents/` folder.

## Usage

### Basic Usage

Run the complete pipeline on all documents in the documents folder:

```bash
python fraud_detection_pipeline.py
```

### Programmatic Usage

```python
from fraud_detection_pipeline import FraudDetectionPipeline

# Initialize pipeline
pipeline = FraudDetectionPipeline()

# Process a single document
result = pipeline.process_single_document('documents/suspicious_email.pdf')

# Process all documents in a directory
results = pipeline.process_directory('documents/')

# Check pipeline status
status = pipeline.get_pipeline_status()
```

## Pipeline Components

### 1. Document Parser (`document_parser.py`)
- Parses PDF, CSV, and TXT files
- Extracts text content and metadata
- Handles file format detection

### 2. Data Normalizer (`data_normalizer.py`)
- Cleans and normalizes extracted text
- Extracts entities (emails, phone numbers, URLs)
- Detects suspicious patterns and fraud indicators

### 3. Document Chunker (`document_chunker.py`)
- Splits documents into manageable chunks
- Supports semantic and overlapping chunking methods
- Configurable chunk size and overlap

### 4. Metadata Tagger (`metadata_tagger.py`)
- Tags documents with metadata fields:
  - `source`: Document source type (pdf, email, csv, etc.)
  - `document_name`: Original filename
  - `risk_level`: Fraud risk assessment (scam/not_scam/unknown)
  - `scam_probability`: Probability score (0-1)
- Analyzes content for fraud indicators

### 5. Embedding Generator (`embedding_generator.py`)
- Generates embeddings using OpenAI's text-embedding-3-small model
- Processes chunks in batches for efficiency
- Handles API rate limiting and errors

### 6. Vector Indexer (`vector_indexer.py`)
- Indexes embeddings into Pinecone vector database
- Creates and manages Pinecone indexes
- Supports similarity search and filtering

## File Structure

```
database/
├── documents/                    # Place your documents here
├── document_parser.py           # Document parsing
├── data_normalizer.py          # Data cleaning and normalization
├── document_chunker.py         # Text chunking
├── metadata_tagger.py          # Metadata generation
├── embedding_generator.py      # OpenAI embeddings
├── vector_indexer.py          # Pinecone vector database
├── fraud_detection_pipeline.py # Main pipeline
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Metadata Fields

Each processed document chunk includes the following metadata:

- **source**: Document source type (pdf, email_pdf, csv_data, etc.)
- **document_name**: Original filename
- **risk_level**: Overall document risk (scam/not_scam/unknown)
- **scam_probability**: Probability score (0.0-1.0)
- **chunk_risk_level**: Individual chunk risk assessment
- **chunk_scam_probability**: Individual chunk probability score
- **processed_timestamp**: When the document was processed
- **file_size**: Original file size in bytes
- **chunk_count**: Total number of chunks
- **entities_found**: Count of extracted entities (emails, phones, URLs)

## Risk Assessment

The system uses multiple factors to assess fraud risk:

### High-Risk Indicators (Score: 3.0 each)
- "urgent payment", "wire transfer", "bitcoin"
- "nigerian prince", "lottery winner", "inheritance"
- "suspended account", "verify immediately"

### Medium-Risk Indicators (Score: 1.5 each)
- "payment required", "update information"
- "security alert", "unusual activity"
- "investment opportunity", "guaranteed profit"

### Low-Risk Indicators (Score: -0.5 each)
- "newsletter", "subscription", "receipt"
- "confirmation", "welcome", "thank you"

### Additional Factors
- Excessive capitalization or punctuation
- Multiple suspicious URLs or email addresses
- Financial terms and urgency language

## Example Output

```python
{
    "file_path": "documents/suspicious_email.pdf",
    "success": True,
    "steps_completed": ["parsing", "normalization", "chunking", "metadata_tagging", "embedding_generation", "vector_indexing"],
    "document_metadata": {
        "source": "email_pdf",
        "document_name": "suspicious_email.pdf",
        "risk_level": "scam",
        "scam_probability": 0.847,
        "chunk_count": 3
    },
    "processing_summary": {
        "total_chunks": 3,
        "high_risk_chunks": 2,
        "medium_risk_chunks": 1,
        "low_risk_chunks": 0
    },
    "indexing_result": {
        "uploaded": 3,
        "total_vectors_in_index": 157
    }
}
```

## Troubleshooting

### Common Issues

1. **Import errors for OpenAI/Pinecone**: Install the required packages with `pip install -r requirements.txt`

2. **API key errors**: Make sure your `.env` file is configured with valid API keys

3. **Empty documents folder**: Add some PDF, CSV, or TXT files to the `documents/` folder

4. **Pinecone index errors**: The system will automatically create a Pinecone index if it doesn't exist

### Logs

The system creates detailed logs in `fraud_detection_pipeline.log` for debugging purposes.

## Extending the System

### Adding New File Types
Extend the `DocumentParser` class to support additional file formats.

### Custom Risk Assessment
Modify the `MetadataTagger` class to implement custom fraud detection logic.

### Different Embedding Models
Update the `EmbeddingGenerator` class to use different embedding models or providers.

### Alternative Vector Databases
Implement a new indexer class following the same interface as `VectorIndexer`.
