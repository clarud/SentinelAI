# Test Cases for assess_document() Function

This directory contains test cases for the `assess_document()` function in `orchestrator.py`. 

## � Quick Start

```bash
# 1. Navigate to project root
cd /Users/chenxiangrui/Projects/SentinelAI

# 2. Run quick test (always works)
python test/worker/quick_test.py

# 3. Run full test suite (comprehensive)
python test/worker/run_tests.py
```

## 📁 Test Files

- **`quick_test.py`** ✅ - Basic validation (no dependencies)
- **`run_tests.py`** 🔄 - Full test suite with mocking  
- **`test_assess_document.py`** 🐍 - Pytest-compatible tests
- **`test_data.py`** 📊 - Mock documents and responses
- **`test_utils.py`** 🛠️ - Helper functions
- **`test_config.py`** ⚙️ - Configuration and benchmarks

## 🧪 What Gets Tested

1. **High Confidence Scam Detection** - Fast path for obvious fraud
2. **High Confidence Legitimate** - Fast path for legitimate docs  
3. **Uncertain Case Analysis** - Full LLM pipeline
4. **Error Handling** - Service failures and fallbacks
5. **Performance Testing** - Timing and resource usage
6. **Logging System** - Complete workflow tracking

## 📝 Log Files

Each test creates log files in `test/worker/`:
- `assessment_YYYYMMDD_HHMMSS_<id>.log` - Human readable
- `assessment_YYYYMMDD_HHMMSS_<id>.json` - Structured data

## 🔧 Troubleshooting

### Import Errors
```
❌ No module named 'boto3'
```
**Expected** - Tests use mocking to work without dependencies.

### Path Issues  
```
❌ No module named 'worker.agents.orchestrator'
```
**Solution:** Run from project root directory.

### Quick Validation
```bash
# Check if everything is working
python test/worker/quick_test.py
```

## 📊 Expected Results

Tests validate `assess_document()` returns:
```python
{
    "is_scam": "scam|not_scam|suspicious",
    "confidence_level": 0.0-1.0,
    "scam_probability": 0.0-100.0, 
    "explanation": "...",
    "processing_metadata": {
        "workflow_id": "...",
        "total_time": 1.25,
        "evidence_gathered": 3,
        "errors_encountered": 0
    }
}
```

---
📖 **For detailed instructions, see [TESTING_README.md](TESTING_README.md)**

### 3. Uncertain Case Analysis
- **Purpose**: Test full LLM analysis pipeline
- **Examples**: Promotional emails, tech support warnings
- **Expected**: Full tool execution, LLM analysis, detailed evidence

### 4. Error Handling
- **Purpose**: Test robustness when services fail
- **Scenarios**: RAG service down, extraction failures, LLM rate limits
- **Expected**: Graceful fallbacks, error logging, valid results

### 5. Performance Testing
- **Purpose**: Ensure processing stays within acceptable bounds  
- **Metrics**: Processing time, tool call counts, memory usage
- **Benchmarks**: < 5s for fast path, < 30s for full analysis

### 6. Logging System
- **Purpose**: Verify comprehensive workflow logging
- **Outputs**: `.log` files for human reading, `.json` files for analysis
- **Content**: Step tracking, decision points, tool calls, performance metrics

## 📊 Test Data Structure

### Sample Documents
```python
# High confidence scam
{
    "type": "email",
    "subject": "URGENT: Claim Your Inheritance", 
    "content": "Dear friend, I have $10 million for you..."
}

# High confidence legitimate  
{
    "type": "email",
    "subject": "Q3 Financial Review Meeting",
    "content": "Hi Sarah, let's schedule our quarterly review..."
}

# Uncertain case
{
    "type": "email", 
    "subject": "Limited Time Offer!",
    "content": "Flash sale! 70% off everything. Click here now!"
}
```

### Expected Results
```python
{
    "is_scam": "scam|not_scam|suspicious",
    "confidence_level": 0.0-1.0,
    "scam_probability": 0.0-100.0,
    "explanation": "Detailed reasoning",
    "processing_metadata": {
        "workflow_id": "abc123",
        "total_time": 1.25,
        "evidence_gathered": 3,
        "errors_encountered": 0
    }
}
```

## 🎯 Validation Checks

### Result Structure Validation
- ✅ Required fields present (`is_scam`, `confidence_level`, etc.)
- ✅ Valid value ranges (confidence 0-1, probability 0-100)
- ✅ Correct data types for all fields
- ✅ Processing metadata completeness

### Performance Validation  
- ✅ Processing time within benchmarks
- ✅ Tool call counts reasonable
- ✅ Memory usage acceptable
- ✅ No resource leaks

### Logging Validation
- ✅ Log files created in correct location
- ✅ JSON workflow data exported properly
- ✅ All workflow steps tracked
- ✅ Decision points logged with reasoning

## 🔧 Mocking Strategy

### External Dependencies Mocked
- **`call_tool()`** - MCP tool execution
- **`_chat_json()`** - LLM API calls  
- **`process_document()`** - Document processing
- **`choose_tools()`** - Tool selection
- **Executer functions** - Final action execution

### Mock Responses Configured
- **Text extraction**: Realistic content based on document type
- **RAG responses**: Confidence/probability scores for different scenarios
- **Tool outputs**: Links, numbers, organizations extracted  
- **LLM responses**: Planner, analyst, supervisor outputs

## 📈 Performance Benchmarks

| Metric | Fast Path | Full Analysis | Error Cases |
|--------|-----------|---------------|-------------|
| Max Time | 5 seconds | 30 seconds | 10 seconds |
| Max Tools | 5 calls | 15 calls | 3 calls |
| Min Evidence | 1 item | 3 items | 1 item |
| Memory | < 50MB | < 100MB | < 25MB |

## 🗂️ Log File Outputs

### Human-Readable Logs (`*.log`)
```
2025-09-04 12:00:00 | INFO | === WORKFLOW START ===
2025-09-04 12:00:01 | INFO | Step 1: document_processing - Process document
2025-09-04 12:00:02 | INFO | TOOL: data-processor.extract_text - SUCCESS  
2025-09-04 12:00:03 | INFO | Step 1 completed in 1.250s
```

### Structured Workflow Data (`*.json`)
```json
{
  "workflow_id": "abc12345",
  "start_time": 1725451200.0,
  "steps": [
    {
      "step_id": 1,
      "step_name": "document_processing", 
      "duration": 1.25,
      "metadata": {"processed_length": 1024}
    }
  ],
  "decisions": [
    {
      "decision_name": "high_confidence_scam",
      "condition": "confidence=0.95, scam_prob=0.89", 
      "result": true
    }
  ],
  "final_result": {...}
}
```

## 🚦 Running Your First Test

1. **Start with quick test**:
   ```bash
   python test/worker/quick_test.py
   ```

2. **Check the output** for any failures

3. **Look at generated logs** in `test/worker/`

4. **Run full test suite** if quick test passes:
   ```bash
   python test/worker/run_tests.py
   ```

5. **Review detailed results** and performance metrics

## 🐛 Troubleshooting

### Import Errors
- Ensure you're running from the project root directory
- Check that `services/worker` path is correct in sys.path
- Verify Python environment has required packages

### Test Failures
- Check mock configurations in `test_data.py`
- Verify expected results match actual code behavior
- Review log files for detailed error information

### Permission Issues
- Ensure `test/worker` directory is writable
- Check file permissions for log file creation
- Verify disk space availability

## 📝 Adding New Tests

1. **Add test data** to `test_data.py`
2. **Configure mocks** in `test_utils.py`  
3. **Define scenarios** in `test_config.py`
4. **Implement test** in `test_assess_document.py` or `run_tests.py`
5. **Update benchmarks** if needed

This comprehensive test suite ensures your fraud detection pipeline works correctly across all scenarios and provides detailed logging for debugging and monitoring.
