# Testing Guide for assess_document() Function

This directory contains comprehensive test cases for the `assess_document()` function in `orchestrator.py`. The tests validate the fraud detection workflow, logging system, and performance metrics.

## 📍 Quick Start

### Step 1: Navigate to Project Root
```bash
cd /Users/chenxiangrui/Projects/SentinelAI
```

### Step 2: Run Quick Validation (Recommended First)
```bash
python test/worker/quick_test.py
```
This tests basic functionality and logging without external dependencies.

### Step 3: Run Full Test Suite
```bash
python test/worker/run_tests.py
```
This runs comprehensive tests with mocking for all workflow scenarios.

## 🧪 Test Files Overview

| File | Purpose | Dependencies |
|------|---------|--------------|
| `quick_test.py` | ✅ Basic validation, logging test | None (works always) |
| `run_tests.py` | 🔄 Full test suite with mocking | Python standard library |
| `test_assess_document.py` | 🐍 Pytest-compatible tests | pytest (optional) |
| `test_data.py` | 📊 Mock documents and responses | None |
| `test_utils.py` | 🛠️ Helper functions | None |
| `test_config.py` | ⚙️ Configuration and benchmarks | None |

## 🚀 Running Tests Step by Step

### Option 1: Quick Test (Always Works)
```bash
# From project root
python test/worker/quick_test.py
```

**What it tests:**
- ✅ File permissions
- ✅ Logging system functionality  
- ✅ Result structure validation
- ✅ Mock assessment logic

**Expected output:**
```
🚀 Quick Test Suite for assess_document Workflow
✅ File Permissions - PASSED
✅ Logging System - PASSED  
✅ Mock Assessment - PASSED
🎉 All quick tests passed!
```

### Option 2: Full Test Suite
```bash
# From project root
python test/worker/run_tests.py
```

**What it tests:**
- 🔍 High confidence scam detection
- ✅ High confidence legitimate detection
- 🤔 Uncertain case full analysis
- ⚠️ Error handling and fallbacks
- 📊 Performance benchmarks
- 📝 Complete logging system

**Expected output:**
```
🧪 Starting comprehensive assess_document workflow tests
✅ High Confidence Scam Detection - PASSED
✅ High Confidence Legitimate Detection - PASSED
✅ Uncertain Case Full Analysis - PASSED
✅ Error Handling - PASSED
✅ Logging System - PASSED
✅ Performance Benchmarks - PASSED
🎉 All tests passed!
```

### Option 3: With Pytest (If Available)
```bash
# Install pytest if needed
pip install pytest

# Run pytest tests
pytest test/worker/test_assess_document.py -v
```

## 📊 Test Scenarios Explained

### 1. High Confidence Scam Detection
**Purpose:** Test fast-path detection for obvious fraud

**Test Documents:**
- Nigerian prince emails
- Lottery scam notifications
- Phishing attempts

**Expected Results:**
- `is_scam: "scam"`
- `confidence_level > 0.85`
- `scam_probability > 80%`
- Fast processing (< 5 seconds)

**Example Mock:**
```python
{
    "content": "Dear friend, I have $10 million inheritance...",
    "expected_rag_response": {
        "average_confidence_level": 0.95,
        "average_scam_probability": 0.89
    }
}
```

### 2. High Confidence Legitimate Detection
**Purpose:** Test fast-path detection for legitimate documents

**Test Documents:**
- Business meeting emails
- Invoice notifications
- Newsletter subscriptions

**Expected Results:**
- `is_scam: "not_scam"`
- `confidence_level > 0.85`
- `scam_probability < 20%`
- Fast processing (< 5 seconds)

### 3. Uncertain Case Full Analysis
**Purpose:** Test complete LLM analysis pipeline

**Test Documents:**
- Promotional emails
- Tech support warnings
- Mixed-signal content

**Expected Results:**
- `is_scam: "suspicious"` (or other)
- Full tool execution
- LLM planner/analyst/supervisor involved
- More evidence gathered

### 4. Error Handling
**Purpose:** Test robustness when services fail

**Scenarios:**
- RAG service unavailable
- Extraction tool failures
- LLM rate limits
- Invalid document formats

**Expected Results:**
- Graceful fallback behavior
- Error logging captured
- Valid result still returned

## 📈 Performance Benchmarks

| Scenario | Max Time | Max Tools | Min Evidence |
|----------|----------|-----------|--------------|
| High Confidence | 5 seconds | 5 calls | 1 item |
| Full Analysis | 30 seconds | 15 calls | 3 items |
| Error Cases | 10 seconds | 3 calls | 1 item |

## 📝 Log Files Generated

Each test run creates log files in `test/worker/`:

### Human-Readable Logs (`.log`)
```
assessment_20250904_144035_abc123.log
```
Contains:
```
2025-09-04 14:40:35 | INFO | === WORKFLOW START ===
2025-09-04 14:40:35 | INFO | Step 1: document_processing
2025-09-04 14:40:36 | INFO | DECISION: high_confidence_scam
2025-09-04 14:40:36 | INFO | TOOL: rag-tools.call_rag - SUCCESS
2025-09-04 14:40:37 | INFO | === WORKFLOW COMPLETE ===
```

### Structured Data (`.json`)
```
assessment_20250904_144035_abc123.json
```
Contains complete workflow metadata, timings, and results.

## 🔧 Troubleshooting

### Common Issues

#### 1. Import Errors
```
❌ Cannot import orchestrator: No module named 'boto3'
```
**Solution:** This is expected if AWS dependencies aren't installed. Tests use mocking to work around this.

#### 2. Permission Errors
```
❌ File permission error: Permission denied
```
**Solution:** 
```bash
# Ensure directory exists and is writable
mkdir -p test/worker
chmod 755 test/worker
```

#### 3. Path Issues
```
❌ No module named 'worker.agents.orchestrator'
```
**Solution:** Always run from project root:
```bash
cd /Users/chenxiangrui/Projects/SentinelAI
python test/worker/quick_test.py
```

### Viewing Test Results

#### Check Log Files
```bash
# List generated log files
ls -la test/worker/assessment_*.log

# View latest log
cat test/worker/assessment_*.log | tail -20

# View JSON data
cat test/worker/assessment_*.json | python -m json.tool
```

#### Clean Up Test Files
```bash
# Remove old test logs
rm test/worker/assessment_*.log
rm test/worker/assessment_*.json
```

## 🎯 Test Validation

Tests validate that `assess_document()` returns proper structure:

```python
{
    "is_scam": "scam|not_scam|suspicious",          # Required
    "confidence_level": 0.0-1.0,                    # Required  
    "scam_probability": 0.0-100.0,                  # Required
    "explanation": "Detailed reasoning...",          # Required
    "tool_evidence": [...],                          # Optional
    "tool_errors": [...],                           # Optional
    "processing_metadata": {                         # Required
        "workflow_id": "abc123",
        "total_time": 1.25,
        "evidence_gathered": 3,
        "errors_encountered": 0,
        "timestamp": 1725451200.0
    }
}
```

## 📚 Understanding Test Output

### Successful Test Run
```
✅ File Permissions - PASSED
✅ Logging System - PASSED
✅ High Confidence Scam Detection - PASSED
✅ Performance Benchmarks - PASSED
🎉 All tests passed!
```

### Failed Test Example
```
❌ High Confidence Scam Detection - FAILED: 
   Expected is_scam='scam' but got 'suspicious'
```

### Performance Warning
```
⚠️ Execution time (6.2s) exceeds benchmark (5.0s)
```

## 🚀 Getting Started Checklist

1. **Navigate to project root**
   ```bash
   cd /Users/chenxiangrui/Projects/SentinelAI
   ```

2. **Run quick test first**
   ```bash
   python test/worker/quick_test.py
   ```

3. **Check for any failures** and fix path/permission issues

4. **Run full test suite**
   ```bash
   python test/worker/run_tests.py
   ```

5. **Examine log files** in `test/worker/` directory

6. **Review performance metrics** and adjust if needed

## 💡 Tips for Success

- **Always run from project root** to avoid import issues
- **Start with quick_test.py** to validate basic setup
- **Check log files** for detailed workflow information  
- **Use mocks when dependencies unavailable** (tests handle this)
- **Clean up old logs** to avoid confusion

This test suite ensures your `assess_document()` function works correctly across all fraud detection scenarios!
