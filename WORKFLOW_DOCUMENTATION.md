# SentinelAI: assess_document Workflow Documentation

## Overview

The `assess_document` function is the core of SentinelAI's agentic fraud detection system. It uses a multi-agent architecture where a **ROUTER agent** dynamically decides which agents to call based on initial analysis confidence levels, making it truly adaptive rather than following a rigid sequential workflow.

## System Architecture

```
📄 Document Input
    ↓
🔄 Document Processing (Always)
    ↓  
🔍 RAG Analysis (Always)
    ↓
🧠 ROUTER Decision (4 possible routes)
    ↓
📊 Agent Execution (Dynamic based on route)
    ↓
⚡ Final Actions & Response
```

## Workflow Steps

### Step 1: Document Processing (Always Required)
- **Purpose**: Convert input document into standardized format
- **Tools Used**: `data-processor.process_email` (for email dicts) or `data-processor.process_pdf` (for PDFs)
- **Output**: Processed document text for analysis
- **Logging**: Document length, processing time

### Step 2: RAG Analysis (Always Required)  
- **Purpose**: Retrieve similar documents from vector database to establish baseline confidence
- **Tools Used**: `rag-tools.call_rag`
- **Output**: 
  - `average_confidence_level` (0.0-1.0)
  - `average_scam_probability` (0.0-100.0)
- **Logging**: RAG scores, tool execution time

### Step 3: ROUTER Decision (The Agentic Brain)
- **Purpose**: Analyze RAG results and decide optimal workflow path
- **Agent**: ROUTER agent (LLM-based decision maker)
- **Input**: Processed document, RAG results, available agents, time/budget constraints
- **Output**: Route decision with reasoning

## Route Types & Decision Logic

### 🚀 Route 1: `fast_scam`
**Trigger Conditions:**
- `confidence_level > 0.9` AND `scam_probability > 80`

**Workflow:**
```
Document → Processing → RAG → ROUTER → EXECUTER (scam actions)
```

**Agents Called:** `["EXECUTER"]`

**Actions:**
- Skip analysis (high confidence = no need for deep investigation)  
- Classify as `"scam"` immediately
- Execute scam-specific actions:
  - `gmail-tools.classify_email`
  - `gmail-tools.send_report_to_drive`  
  - `rag-tools.store_rag`

**Use Case:** Clear phishing emails with high database similarity to known scams

---

### ✅ Route 2: `fast_legitimate`  
**Trigger Conditions:**
- `confidence_level > 0.9` AND `scam_probability < 20`

**Workflow:**
```
Document → Processing → RAG → ROUTER → EXECUTER (legitimate actions)
```

**Agents Called:** `["EXECUTER"]`

**Actions:**
- Skip analysis (high confidence = no need for investigation)
- Classify as `"not_scam"` immediately  
- Execute legitimate-specific actions:
  - `gmail-tools.send_report_to_drive`
  - `rag-tools.store_rag`

**Use Case:** Obviously legitimate emails with high similarity to known good communications

---

### 🔍 Route 3: `full_analysis`
**Trigger Conditions:**  
- `confidence_level 0.5-0.9` OR `scam_probability 20-80`

**Workflow:**
```
Document → Processing → RAG → ROUTER → PLANNER → ANALYST → SUPERVISOR → EXECUTER
```

**Agents Called:** `["PLANNER", "ANALYST", "SUPERVISOR", "EXECUTER"]`

**Detailed Flow:**

1. **PLANNER Agent**
   - Decides which extraction tools to use
   - Available tools: `extract_link`, `extract_number`, `extract_organisation`
   - Output: Tool execution plan

2. **Tool Execution** 
   - Executes PLANNER's chosen tools
   - Gathers additional evidence (links, organizations, numbers)

3. **ANALYST Agent**
   - Interprets all tool outputs and evidence
   - Calculates `scam_probability` and `confidence_level`
   - Does NOT make final classification

4. **SUPERVISOR Agent** 
   - Makes final classification decision
   - Uses ANALYST results to determine `is_scam`
   - Provides detailed explanation

5. **EXECUTER Agent**
   - Performs appropriate actions based on classification
   - Different actions for scam vs legitimate

**Use Case:** Moderate uncertainty cases requiring structured analysis

---

### 🕵️ Route 4: `deep_analysis`
**Trigger Conditions:**
- `confidence_level < 0.5` (High uncertainty)

**Workflow:**
```
Document → Processing → RAG → ROUTER → PLANNER → ANALYST → SUPERVISOR → EXECUTER
```

**Agents Called:** `["PLANNER", "ANALYST", "SUPERVISOR", "EXECUTER"]`

**Key Differences from `full_analysis`:**
- Same agent flow but with "extra caution" mode
- More thorough logging and evidence collection
- Enhanced fallback mechanisms
- Stricter validation of agent outputs

**Use Case:** Completely unknown document types or low database similarity

## Agent Responsibilities

### 🧠 ROUTER Agent (Orchestration Brain)
- **Role**: Dynamic workflow orchestrator  
- **Decision Factors**: RAG confidence, time budget, tool budget
- **Output**: Route selection with reasoning
- **Fallback**: Rules-based routing if LLM fails

### 📋 PLANNER Agent  
- **Role**: Tool selection strategist
- **Input**: Document content, available extraction tools
- **Output**: Ordered list of tools to execute
- **Strategy**: Focuses on evidence gathering (links, orgs, numbers)

### 📊 ANALYST Agent
- **Role**: Evidence interpreter
- **Input**: All tool outputs and document content  
- **Output**: Risk metrics (`scam_probability`, `confidence_level`)
- **Note**: Does NOT make final classification

### ⚖️ SUPERVISOR Agent
- **Role**: Final decision maker
- **Input**: ANALYST's risk assessment + document summary
- **Output**: Final classification (`scam`/`not_scam`) with explanation
- **Validation**: Uses RiskAssessment schema

### ⚡ EXECUTER Agent  
- **Role**: Action performer
- **Actions for Scams**:
  - Email classification
  - Report generation  
  - Database storage
- **Actions for Legitimate**:
  - Report generation
  - Database storage

## Error Handling & Fallbacks

### ROUTER Failures
- **Primary**: LLM-based intelligent routing
- **Fallback**: Rules-based routing using confidence thresholds
- **Last Resort**: Default to `full_analysis`

### Agent Failures
- **Retry Logic**: 2 attempts per agent with different prompts
- **JSON Parsing**: Robust error handling for malformed responses
- **Validation**: Pydantic schema validation with fallback construction

### Tool Failures  
- **Timeout Handling**: Respects `TOOL_TIME_BUDGET`
- **Budget Limits**: Respects `TOOL_MAX_CALLS`
- **Error Logging**: Comprehensive error tracking

## Performance Characteristics

### Route Performance Comparison
- **fast_scam**: ~5-10 seconds (minimal processing)
- **fast_legitimate**: ~5-10 seconds (minimal processing)  
- **full_analysis**: ~20-40 seconds (full agent pipeline)
- **deep_analysis**: ~30-50 seconds (enhanced analysis)

### Resource Usage
- **Tool Budget**: Maximum 4 tool calls per assessment
- **Time Budget**: 60 seconds maximum per assessment  
- **Token Limits**: Evidence truncated to prevent LLM overflow

## Logging & Monitoring

### Comprehensive Tracking
- **Workflow ID**: Unique identifier per assessment
- **Step-by-Step**: Each agent and tool execution logged
- **Performance Metrics**: Timing for all operations
- **Decision Trail**: ROUTER reasoning and agent outputs
- **Evidence Chain**: All tool results and transformations

### Log Files Generated
- **assessment_YYYYMMDD_HHMMSS_WORKFLOWID.log**: Detailed execution log
- **assessment_YYYYMMDD_HHMMSS_WORKFLOWID.json**: Structured workflow data

## Output Format

### Standard Response
```json
{
  "is_scam": "scam" | "not_scam" | "suspicious",
  "confidence_level": 0.95,
  "scam_probability": 87.5,
  "explanation": "User-friendly explanation of the decision",
  "tool_evidence": [
    {"tool": "rag-tools.call_rag", "output": {...}},
    {"tool": "extraction-tools.extract_link", "output": {...}}
  ],
  "processing_metadata": {
    "total_time": 25.3,
    "workflow_id": "a1b2c3d4", 
    "evidence_gathered": 4,
    "errors_encountered": 0,
    "router_route": "full_analysis",
    "agents_called": ["PLANNER", "ANALYST", "SUPERVISOR", "EXECUTER"]
  }
}
```

## Example Workflows

### Example 1: Obvious Phishing (fast_scam)
```
Input: Urgent bank phishing email
RAG: confidence=0.95, scam_probability=95
ROUTER: "fast_scam" - skip analysis
EXECUTER: Classify as scam, report, store
Result: ~8 seconds, scam classification
```

### Example 2: GitHub Notification (fast_legitimate)  
```
Input: Legitimate GitHub security alert
RAG: confidence=0.92, scam_probability=8  
ROUTER: "fast_legitimate" - skip analysis
EXECUTER: Report as legitimate, store
Result: ~6 seconds, not_scam classification
```

### Example 3: Suspicious Business Email (full_analysis)
```
Input: Ambiguous business communication
RAG: confidence=0.7, scam_probability=45
ROUTER: "full_analysis" - need investigation  
PLANNER: Plan link + organization extraction
ANALYST: Analyze extracted evidence
SUPERVISOR: Make final decision based on analysis
EXECUTER: Take appropriate action
Result: ~28 seconds, detailed analysis
```

### Example 4: Unknown Document Type (deep_analysis)
```
Input: Never-seen-before document format
RAG: confidence=0.1, scam_probability=0
ROUTER: "deep_analysis" - high uncertainty
PLANNER: Comprehensive tool selection
ANALYST: Detailed evidence interpretation  
SUPERVISOR: Cautious decision making
EXECUTER: Conservative actions
Result: ~35 seconds, thorough investigation
```

## Key Agentic Features

### 🧠 **Intelligence**: ROUTER makes decisions based on evidence, not rules
### 🔄 **Adaptability**: Different documents take different paths automatically  
### ⚡ **Efficiency**: High-confidence cases skip unnecessary analysis
### 🛡️ **Reliability**: Multiple fallback mechanisms ensure robustness
### 📊 **Transparency**: Complete decision trail for auditability
### 🎯 **Precision**: Specialized actions based on classification results

---

This workflow represents a truly **agentic system** where intelligent agents make dynamic decisions about which other agents to call, rather than following a rigid sequential pipeline. The ROUTER agent acts as the orchestrating intelligence, optimizing both accuracy and efficiency based on real-time confidence assessments.
