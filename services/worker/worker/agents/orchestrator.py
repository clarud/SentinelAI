import json, time, sys, os, boto3
from dotenv import load_dotenv
from typing import Dict, Any, List

current_file = os.path.abspath(__file__)
project_root = current_file
while True:
    project_root = os.path.dirname(project_root)
    if os.path.isdir(os.path.join(project_root, 'services')):
        break

# Add project root to sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from services.worker.worker.agents.config import TOOL_MAX_CALLS, TOOL_TIME_BUDGET
from services.worker.worker.agents.prompts import PLANNER_SYS, ANALYST_SYS, SUPERVISOR_SYS, CLASSIFY_INTENT_SYS, KNOWLEDGE_SYS, SCENARIO_SYS, ADVISOR_SYS, ROUTER_SYS
from services.worker.worker.agents.schemas import RiskAssessment
from services.worker.worker.agents.assessment_logger import get_assessment_logger, reset_assessment_logger
from services.worker.worker.tools.selector import process_document, choose_tools, not_scam_executer, scam_executer
from services.worker.worker.tools.mcp_client import call_tool

load_dotenv()

def _chat_json(system: str, user_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Call LLM and parse JSON safely with logging."""
    logger = get_assessment_logger()
    
    try:
        logger.logger.info(f"BEDROCK CALL START: system_prompt_length={len(system)}, user_input_keys={list(user_obj.keys())}")
        
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        response = client.converse(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=[
                {"role": "user", "content": [{"text": json.dumps(user_obj)}]}
            ],
            system=[{"text": system}],
            inferenceConfig={
                "maxTokens": 500,  # Increased from 200
                "temperature": 0.3  # Reduced for more consistent output
            }
        )
        
        text = response['output']['message']['content'][0]['text']
        logger.logger.info(f"BEDROCK CALL SUCCESS: response_length={len(text)}")
        logger.logger.debug(f"BEDROCK RAW RESPONSE: {text[:500]}{'...' if len(text) > 500 else ''}")
        
        try:
            parsed = json.loads(text)
            logger.logger.info(f"BEDROCK JSON PARSE SUCCESS: keys={list(parsed.keys()) if isinstance(parsed, dict) else 'not_dict'}")
            return parsed
        except json.JSONDecodeError as e:
            logger.logger.error(f"BEDROCK JSON PARSE FAILED: {e} | Raw text: {text[:200]}...")
            return {}
            
    except Exception as e:
        logger.logger.error(f"BEDROCK CALL FAILED: {type(e).__name__}: {str(e)}")
        return {}

def _truncate_plan(plan: Dict[str, Any], budget_left: int, whitelist: List[str]) -> List[Dict[str, Any]]:
    calls = plan.get("calls", [])
    pruned = []
    for c in calls:
        name = f"{c.get('server','')}.{c.get('tool','')}"
        if name in whitelist:
            pruned.append(c)
            if len(pruned) >= budget_left:
                break
    return pruned

def _execute_calls(calls: List[Dict[str, Any]], evidence: List[Dict[str, Any]], errors: List[Dict[str, Any]], t0: float):
    """Execute tool calls and collect evidence/errors."""
    logger = get_assessment_logger()
    
    for c in calls:
        tool_start_time = time.time()
        server = c.get("server", "unknown")
        tool = c.get("tool", "unknown") 
        args = c.get("args", {})
        
        try:
            out = call_tool(server, tool, **args)
            execution_time = time.time() - tool_start_time
            evidence.append({"tool": f"{server}.{tool}", "output": out})
            logger.log_tool_call(server, tool, args, output=out)
            logger.log_performance_metric(f"tool_{server}_{tool}_duration", execution_time, "seconds")
        except Exception as e:
            execution_time = time.time() - tool_start_time
            error_msg = str(e)
            errors.append({"tool": f"{server}.{tool}", "error": error_msg})
            logger.log_tool_call(server, tool, args, error=error_msg)
            logger.log_performance_metric(f"tool_{server}_{tool}_duration", execution_time, "seconds")

def assess_document(document: Any) -> Dict[str, Any]:
    """
    Agentic fraud detection workflow where ROUTER agent decides which agents to call.
    """
    # Initialize logging for this assessment
    reset_assessment_logger()
    logger = get_assessment_logger()
    logger.log_workflow_start(document)
    
    # Log the input document text/content for debugging
    document_content = str(document)
    logger.logger.info(f"INPUT DOCUMENT: {document_content[:500]}{'...' if len(document_content) > 500 else ''}")
    logger.log_performance_metric("input_document_length", len(document_content), "characters")
    
    evidence: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    t0 = time.time()

    # Step 1: Document Processing (Always Required)
    step1_idx = logger.log_step_start("document_processing", "Process document and extract text content")
    process_step = process_document(document)
    _execute_calls(process_step, evidence, errors, t0)
    processed_document = evidence[0]["output"] if evidence else str(document)
    
    logger.logger.info(f"PROCESSED DOCUMENT TEXT: {str(processed_document)[:1000]}{'...' if len(str(processed_document)) > 1000 else ''}")
    logger.log_performance_metric("processed_document_length", len(str(processed_document)), "characters")
    logger.log_step_end(step1_idx, {"processed_length": len(str(processed_document))})

    # Step 2: RAG Analysis (Always Required)
    step2_idx = logger.log_step_start("rag_analysis", "Retrieve similar documents from database")
    must_steps = choose_tools(processed_document)[:TOOL_MAX_CALLS]
    _execute_calls(must_steps, evidence, errors, t0)
    budget_left = max(0, TOOL_MAX_CALLS - len(evidence))
    
    # Extract RAG results
    rag_results = {}
    for ev in evidence:
        if ev.get("tool") == "rag-tools.call_rag":
            logger.logger.info(f"RAG TOOL RESULT: {ev.get('output', 'No output')}")
            if isinstance(ev.get("output"), dict):
                rag_results = ev["output"]
                break
    
    # Set defaults if no RAG results
    average_confidence_level = rag_results.get("average_confidence_level", 0.5)
    average_scam_probability = rag_results.get("average_scam_probability", 50.0)
    
    logger.logger.info(f"EXTRACTED SCORES: confidence_level={average_confidence_level}, scam_probability={average_scam_probability}")
    logger.log_step_end(step2_idx, {"tools_executed": len(must_steps), "budget_remaining": budget_left})

    # Step 3: ROUTER Agent Decides Next Steps
    step3_idx = logger.log_step_start("router_decision", "ROUTER agent decides workflow path")
    router_input = {
        "document": processed_document,
        "rag_results": {
            "confidence_level": average_confidence_level,
            "scam_probability": average_scam_probability,
            "detailed_results": rag_results
        },
        "available_agents": ["PLANNER", "ANALYST", "SUPERVISOR", "EXECUTER"],
        "budget_left": budget_left,
        "time_left": max(0, TOOL_TIME_BUDGET - (time.time() - t0))
    }
    
    # Call ROUTER agent
    routing_decision = {}
    for attempt in range(2):
        routing_decision = _chat_json(ROUTER_SYS, router_input)
        if routing_decision and "route" in routing_decision:
            break
        logger.logger.warning(f"ROUTER attempt {attempt + 1} returned empty/invalid response")
    
    # Fallback routing if ROUTER fails
    if not routing_decision or "route" not in routing_decision:
        logger.logger.error("ROUTER failed - using fallback logic")
        if average_confidence_level > 0.9 and average_scam_probability > 80:
            routing_decision = {
                "route": "fast_scam",
                "reasoning": "Fallback: High confidence scam",
                "agents_to_call": ["EXECUTER"],
                "final_classification": "scam",
                "skip_to_execution": True
            }
        elif average_confidence_level > 0.9 and average_scam_probability < 20:
            routing_decision = {
                "route": "fast_legitimate",
                "reasoning": "Fallback: High confidence legitimate",
                "agents_to_call": ["EXECUTER"],
                "final_classification": "not_scam",
                "skip_to_execution": True
            }
        else:
            routing_decision = {
                "route": "full_analysis",
                "reasoning": "Fallback: Uncertain case requires full analysis",
                "agents_to_call": ["PLANNER", "ANALYST", "SUPERVISOR", "EXECUTER"],
                "final_classification": None,
                "skip_to_execution": False
            }
    
    logger.log_data("router_decision", routing_decision)
    logger.logger.info(f"ROUTER DECISION: {routing_decision['route']} - {routing_decision['reasoning']}")
    logger.log_step_end(step3_idx, {"route": routing_decision["route"], "agents_planned": len(routing_decision["agents_to_call"])})

    # Step 4: Execute Agents Based on Router Decision
    final = None
    agents_to_call = routing_decision.get("agents_to_call", [])
    
    # Handle fast-path execution
    if routing_decision.get("skip_to_execution", False):
        classification = routing_decision.get("final_classification")
        if classification:
            step4_idx = logger.log_step_start("fast_path_classification", f"Fast-path {classification} classification")
            final = RiskAssessment(
                is_scam=classification,
                confidence_level=average_confidence_level,
                scam_probability=average_scam_probability,
                explanation=f"Fast-path classification: {routing_decision['reasoning']}",
                text=processed_document
            ).model_dump()
            logger.log_data("fast_path_assessment", final)
            logger.log_step_end(step4_idx, {"classification": classification})
    
    # Handle full analysis path
    else:
        # PLANNER Agent
        if "PLANNER" in agents_to_call and budget_left > 0 and time.time() - t0 < TOOL_TIME_BUDGET:
            step_planner_idx = logger.log_step_start("planner_agent", "PLANNER agent plans additional tools")
            planner_input = {
                "document": {
                    "text": processed_document,
                    "confidence_level": average_confidence_level,
                    "scam_probability": average_scam_probability
                },
                "catalog": [
                    "extraction-tools.extract_link",
                    "extraction-tools.extract_number", 
                    "extraction-tools.extract_organisation"
                ],
                "max_calls": budget_left,
                "hints": {"MUST_already_done": [f"{s['server']}.{s['tool']}" for s in must_steps]}
            }
            
            plan = {}
            for attempt in range(2):
                plan = _chat_json(PLANNER_SYS, planner_input)
                if plan and "calls" in plan:
                    break
                logger.logger.warning(f"PLANNER attempt {attempt + 1} returned empty/invalid response")
            
            logger.log_data("planner_result", plan)
            logger.log_step_end(step_planner_idx, {"tools_planned": len(plan.get("calls", []))})
            
            # Execute planned tools
            step_tools_idx = logger.log_step_start("planned_tools", "Execute tools planned by PLANNER")
            opt_calls = _truncate_plan(plan, budget_left, whitelist=[
                "extraction-tools.extract_link",
                "extraction-tools.extract_number",
                "extraction-tools.extract_organisation"
            ])
            _execute_calls(opt_calls, evidence, errors, t0)
            
            for ev in evidence:
                if ev.get("tool", "").startswith("extraction-tools."):
                    logger.logger.info(f"EXTRACTION TOOL RESULT - {ev.get('tool', 'unknown')}: {ev.get('output', 'No output')}")
            
            logger.log_step_end(step_tools_idx, {"tools_executed": len(opt_calls)})
        
        # ANALYST Agent
        if "ANALYST" in agents_to_call:
            step_analyst_idx = logger.log_step_start("analyst_agent", "ANALYST agent analyzes evidence")
            analyst_input = {
                "document": {
                    "text": processed_document,
                    "confidence_level": average_confidence_level,
                    "scam_probability": average_scam_probability
                },
                "evidence": evidence[:10]  # Limit evidence to prevent token overflow
            }
            
            risk = {}
            for attempt in range(2):
                risk = _chat_json(ANALYST_SYS, analyst_input)
                if risk and any(key in risk for key in ["confidence", "scam_probability", "reasoning"]):
                    break
                logger.logger.warning(f"ANALYST attempt {attempt + 1} returned empty/invalid response")
            
            logger.log_data("analyst_result", risk)
            logger.logger.info(f"ANALYST RESPONSE: {risk}")
            logger.log_step_end(step_analyst_idx, {"analysis_generated": bool(risk)})
        
        # SUPERVISOR Agent
        if "SUPERVISOR" in agents_to_call:
            step_supervisor_idx = logger.log_step_start("supervisor_agent", "SUPERVISOR agent makes final decision")
            supervisor_input = {
                "risk": risk if 'risk' in locals() else {},
                "document_summary": processed_document[:500]
            }
            
            supervised = {}
            for attempt in range(2):
                supervised = _chat_json(SUPERVISOR_SYS, supervisor_input)
                if supervised and any(key in supervised for key in ["is_scam", "confidence_level", "scam_probability"]):
                    break
                logger.logger.warning(f"SUPERVISOR attempt {attempt + 1} returned empty/invalid response")
            
            logger.log_data("supervisor_result", supervised)
            logger.logger.info(f"SUPERVISOR RESPONSE: {supervised}")
            
            # Validate and create final assessment
            try:
                # Add processed_document text to supervised result
                supervised["text"] = processed_document
                final = RiskAssessment(**supervised).model_dump()
                logger.log_step_end(step_supervisor_idx, {"validation": "success"})
            except Exception as e:
                logger.logger.error(f"SUPERVISOR validation failed: {e}")
                
                # Enhanced fallback using available data
                confidence = supervised.get("confidence_level", risk.get("confidence", average_confidence_level))
                scam_prob = supervised.get("scam_probability", risk.get("scam_probability", average_scam_probability))
                
                is_scam = "suspicious"
                if scam_prob > 70:
                    is_scam = "scam"
                elif scam_prob < 30:
                    is_scam = "not_scam"
                
                final = RiskAssessment(
                    is_scam=is_scam,
                    confidence_level=float(confidence),
                    scam_probability=float(scam_prob),
                    explanation=f"Assessment based on analysis with {len(evidence)} evidence sources. Router route: {routing_decision['route']}",
                    text=processed_document
                ).model_dump()
                logger.log_step_end(step_supervisor_idx, {"validation": "fallback", "error": str(e)})
    
    # Add raw email dict to final output if available
    final["email"] = document if isinstance(document, dict) else None
    
    # Step 5: EXECUTER Agent (Always Called)
    if "EXECUTER" in agents_to_call and final:
        step_executer_idx = logger.log_step_start("executer_agent", "EXECUTER agent performs final actions")
        executer_steps = []
        
        if final.get("is_scam") == "not_scam":
            executer_steps = not_scam_executer(final)
        elif final.get("is_scam") == "scam":
            executer_steps = scam_executer(document, final)
        
        if executer_steps:
            logger.log_data("executer_tools", {"steps": executer_steps, "count": len(executer_steps)})
            _execute_calls(executer_steps, evidence, errors, t0)
            logger.log_data("executer_results", {
                "evidence_count": len(evidence),
                "error_count": len(errors),
                "evidence": evidence[-3:] if evidence else [],
                "errors": errors[-3:] if errors else []
            })
            final["tool_evidence"] = evidence
            if errors:
                final["tool_errors"] = errors
        
        logger.log_step_end(step_executer_idx, {"executer_steps": len(executer_steps)})

    # Step 6: Complete Workflow
    step_final_idx = logger.log_step_start("completion", "Finalize assessment and prepare response")
    total_time = time.time() - t0
    
    # Ensure we have a final result
    if not final:
        logger.logger.error("No final assessment generated - creating fallback")
        final = RiskAssessment(
            is_scam="suspicious",
            confidence_level=average_confidence_level,
            scam_probability=average_scam_probability,
            explanation=f"Fallback assessment due to workflow error. Router route: {routing_decision.get('route', 'unknown')}",
            text=processed_document
        ).model_dump()
    
    workflow_data = logger.complete_workflow(
        document_id=final.get("document_id", "unknown"),
        final_result=final,
        total_processing_time=total_time,
        evidence_count=len(evidence),
        error_count=len(errors)
    )
    
    # Add workflow metadata
    final["processing_metadata"] = {
        "total_time": total_time,
        "workflow_id": logger.workflow_id,
        "evidence_gathered": len(evidence),
        "errors_encountered": len(errors),
        "timestamp": time.time(),
        "router_route": routing_decision.get("route", "unknown"),
        "agents_called": agents_to_call
    }
    
    logger.log_step_end(step_final_idx, {"total_time": total_time, "workflow_complete": True})
    
    # Log final assessment
    logger.log_data("final_risk_assessment", {
        "assessment": final,
        "classification": final.get("is_scam", "unknown"),
        "confidence": final.get("confidence_level", 0),
        "scam_probability": final.get("scam_probability", 0),
        "explanation_length": len(final.get("explanation", "")),
        "has_tool_evidence": "tool_evidence" in final,
        "evidence_count": len(final.get("tool_evidence", [])),
        "has_errors": "tool_errors" in final,
        "error_count": len(final.get("tool_errors", [])),
        "router_route": routing_decision.get("route", "unknown")
    })

    return final

def classify_intent(user_input: str) -> str:
    """
    Classify user intent using the LLM.
    
    Returns: 
        str: The classified intent of the user input. ("qa", "scenario", "advisor")
    """
    system_prompt = CLASSIFY_INTENT_SYS
    resp = _chat_json(system_prompt, {"text": user_input})
    return resp.get("intent", "qa").strip().lower()  # Default to "qa" if no intent found

def chatbot_response(conversation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate chatbot response and update conversation history.
    
    Args:
        conversation: {
            "context": str,
            "current_input": str,
            "history": [
                {"role": "user", "content": str},
                {"role": "assistant", "content": str},
                ...
            ]
        }
    
    Returns:
        Updated conversation dict with new response appended to history
        
        Example return:
        {
            "response": "Phishing is a type of cyber attack where criminals impersonate legitimate organizations to steal sensitive information like passwords, credit card numbers, or personal data. They typically use fake emails, websites, or messages that look authentic to trick victims into providing their information.",
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hello! I'm here to help you with fraud detection and cybersecurity questions. How can I assist you today?"},
                {"role": "user", "content": "What is phishing?"},
                {"role": "assistant", "content": "Phishing is a type of cyber attack where criminals impersonate legitimate organizations to steal sensitive information like passwords, credit card numbers, or personal data. They typically use fake emails, websites, or messages that look authentic to trick victims into providing their information."}
            ],
            "intent": "qa"
        }
    """
    user_input = conversation.get("current_input", "")
    history = conversation.get("history", [])
    context = conversation.get("context", "")
    
    # Step 1: classify intent
    intent = classify_intent(user_input)  # "qa", "scenario", "advisor"

    # Step 2: select sub-agent system prompt
    if intent == "qa":
        sys_prompt = KNOWLEDGE_SYS
    elif intent == "scenario":
        sys_prompt = SCENARIO_SYS
    elif intent == "advisor":
        sys_prompt = ADVISOR_SYS
    else:
        sys_prompt = KNOWLEDGE_SYS  # Default fallback

    # Step 3: prepare input with conversation history
    chat_input = {
        "current_message": user_input,
        "conversation_history": history,
        "user_context": context
    }
    
    # Step 4: call LLM
    resp = _chat_json(sys_prompt, chat_input)
    response_content = resp.get("response", "I'm sorry, I couldn't process your request.")
    
    # Step 5: update conversation history
    updated_history = history.copy()
    updated_history.append({"role": "user", "content": user_input})
    updated_history.append({"role": "assistant", "content": response_content})
    
    return {
        "response": response_content,
        "history": updated_history,
        "intent": intent
    }