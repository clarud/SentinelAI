"""
Comprehensive logging system for document assessment workflow.
Tracks every step of the assess_document process for debugging and monitoring.
"""
import json
import time
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

class AssessmentLogger:
    """Comprehensive logger for document assessment workflow."""
    
    def __init__(self, log_dir: str = "test/worker"):
        self.workflow_id = str(uuid.uuid4())[:8]
        self.start_time = time.time()
        self.log_dir = log_dir
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup file logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"assessment_{timestamp}_{self.workflow_id}.log")
        self.json_file = os.path.join(log_dir, f"assessment_{timestamp}_{self.workflow_id}.json")
        
        # Configure logger
        self.logger = logging.getLogger(f"assessment_{self.workflow_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Workflow data for JSON export
        self.workflow_data = {
            "workflow_id": self.workflow_id,
            "start_time": self.start_time,
            "start_timestamp": datetime.now().isoformat(),
            "steps": [],
            "decisions": [],
            "tool_calls": [],
            "performance_metrics": {},
            "errors": [],
            "final_result": None
        }
        
        self.step_counter = 0
    
    def log_workflow_start(self, document: Any):
        """Log the start of a document assessment workflow."""
        doc_info = {
            "type": type(document).__name__,
            "length": len(str(document)) if document else 0
        }
        
        self.logger.info(f"=== WORKFLOW START ===")
        self.logger.info(f"Workflow ID: {self.workflow_id}")
        self.logger.info(f"Document: {doc_info}")
        
        self.workflow_data["document_info"] = doc_info
    
    def log_step_start(self, step_name: str, description: str) -> int:
        """Log the start of a workflow step."""
        self.step_counter += 1
        step_id = self.step_counter
        
        step_data = {
            "step_id": step_id,
            "step_name": step_name,
            "description": description,
            "start_time": time.time(),
            "start_timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Step {step_id}: {step_name} - {description}")
        self.workflow_data["steps"].append(step_data)
        
        return step_id
    
    def log_step_end(self, step_id: int, metadata: Dict[str, Any] = None):
        """Log the end of a workflow step."""
        end_time = time.time()
        
        # Find the step in workflow_data
        for step in self.workflow_data["steps"]:
            if step["step_id"] == step_id:
                duration = end_time - step["start_time"]
                step["end_time"] = end_time
                step["end_timestamp"] = datetime.now().isoformat()
                step["duration"] = duration
                step["metadata"] = metadata or {}
                
                self.logger.info(f"Step {step_id} completed in {duration:.3f}s")
                if metadata:
                    self.logger.debug(f"Step {step_id} metadata: {metadata}")
                break
    
    def log_decision_point(self, decision_name: str, condition: str, result: bool, metadata: Dict[str, Any] = None):
        """Log a decision point in the workflow."""
        decision_data = {
            "decision_name": decision_name,
            "condition": condition,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        result_str = "TRUE" if result else "FALSE"
        self.logger.info(f"DECISION: {decision_name} | Condition: {condition} | Result: {result_str}")
        
        if metadata:
            self.logger.debug(f"Decision metadata: {metadata}")
        
        self.workflow_data["decisions"].append(decision_data)
    
    def log_tool_call(self, server: str, tool: str, args: Dict[str, Any], output: Any = None, error: str = None):
        """Log a tool call execution."""
        tool_data = {
            "server": server,
            "tool": tool,
            "args": args,
            "timestamp": datetime.now().isoformat(),
            "success": error is None
        }
        
        if output is not None:
            tool_data["output"] = output
            self.logger.info(f"TOOL: {server}.{tool} - SUCCESS")
            self.logger.debug(f"Tool output: {output}")
        
        if error:
            tool_data["error"] = error
            self.logger.error(f"TOOL: {server}.{tool} - ERROR: {error}")
        
        self.workflow_data["tool_calls"].append(tool_data)
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = ""):
        """Log a performance metric."""
        self.workflow_data["performance_metrics"][metric_name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.debug(f"METRIC: {metric_name} = {value} {unit}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log an error."""
        error_data = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.error(f"ERROR: {error_type} - {error_message}")
        if context:
            self.logger.debug(f"Error context: {context}")
        
        self.workflow_data["errors"].append(error_data)
    
    def complete_workflow(self, document_id: str, final_result: Dict[str, Any], 
                         total_processing_time: float, evidence_count: int, error_count: int) -> Dict[str, Any]:
        """Complete the workflow and export final data."""
        end_time = time.time()
        
        self.workflow_data.update({
            "document_id": document_id,
            "final_result": final_result,
            "end_time": end_time,
            "end_timestamp": datetime.now().isoformat(),
            "total_processing_time": total_processing_time,
            "evidence_count": evidence_count,
            "error_count": error_count,
            "workflow_duration": end_time - self.start_time
        })
        
        self.logger.info(f"=== WORKFLOW COMPLETE ===")
        self.logger.info(f"Total time: {total_processing_time:.3f}s")
        self.logger.info(f"Evidence gathered: {evidence_count}")
        self.logger.info(f"Errors encountered: {error_count}")
        self.logger.info(f"Final result: {final_result.get('is_scam', 'unknown')}")
        
        # Export workflow data to JSON
        try:
            with open(self.json_file, 'w') as f:
                json.dump(self.workflow_data, f, indent=2, default=str)
            self.logger.info(f"Workflow data exported to: {self.json_file}")
        except Exception as e:
            self.logger.error(f"Failed to export workflow data: {e}")
        
        return self.workflow_data
    
    def log_data(self, label: str, data: dict):
        """Log arbitrary structured data for debugging and workflow tracking."""
        self.logger.info(f"DATA: {label} - {data}")
        # Optionally, store in workflow_data for later export
        if "extra_data" not in self.workflow_data:
            self.workflow_data["extra_data"] = []
        self.workflow_data["extra_data"].append({label: data})


# Global logger instance
_current_logger: Optional[AssessmentLogger] = None

def get_assessment_logger() -> AssessmentLogger:
    """Get the current assessment logger instance."""
    global _current_logger
    if _current_logger is None:
        _current_logger = AssessmentLogger()
    return _current_logger

def reset_assessment_logger(log_dir: str = "test/worker") -> AssessmentLogger:
    """Reset the assessment logger for a new workflow."""
    global _current_logger
    _current_logger = AssessmentLogger(log_dir)
    return _current_logger

