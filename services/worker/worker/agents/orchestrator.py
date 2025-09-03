import json, time, os, boto3
from dotenv import load_dotenv
from typing import Dict, Any, List
from .config import TOOL_MAX_CALLS, TOOL_TIME_BUDGET
from .prompts import PLANNER_SYS, ANALYST_SYS, SUPERVISOR_SYS, CLASSIFY_INTENT_SYS, KNOWLEDGE_SYS, SCENARIO_SYS, ADVISOR_SYS
from .schemas import RiskAssessment
from worker.tools.selector import process_document, choose_tools, not_scam_executer, scam_executer         # deterministic MUST steps
from worker.tools.mcp_client import call_tool           # MCP dispatcher

load_dotenv()

def _chat_json(system: str, user_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Call LLM and parse JSON safely."""
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    response = client.converse(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        messages=[
            {"role": "user", "content": [{"text": json.dumps(user_obj)}]}
        ],
        system=[{"text": system}],
        inferenceConfig={
            "maxTokens": 200,
            "temperature": 0.7
        }
    )
    text = response['output']['message']['content'][0]['text']
    try:
        return json.loads(text)
    except Exception:
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
    for c in calls:
        if time.time() - t0 > TOOL_TIME_BUDGET: break
        try:
            out = call_tool(c["server"], c["tool"], **(c.get("args") or {}))
            evidence.append({"tool": f"{c['server']}.{c['tool']}", "output": out})
        except Exception as e:
            errors.append({"tool": f"{c.get('server')}.{c.get('tool')}", "error": str(e)})

def assess_document(document: Any) -> Dict[str, Any]:
    """
    Multi-agent:
      1) Deterministic MUST tools
      2) Planner proposes extra tools (bounded)
      3) Execute plan (Tooler = Python)
      4) Analyst fuses evidence
      5) Supervisor validates JSON
    Returns dict matching RiskAssessment model.
    """
    evidence: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    # 1) MUST tools (deterministic)
    process_step = process_document(document)
    t0 = time.time()
    _execute_calls(process_step, evidence, errors, t0)
    processed_document = evidence[0]["output"] if evidence else ""      # processed_document is a string text

    must_steps = choose_tools(processed_document)[:TOOL_MAX_CALLS]

    _execute_calls(must_steps, evidence, errors, t0)    # we execute call_rag and obtain {average_confidence_level, average_scam_probability}
    budget_left = max(0, TOOL_MAX_CALLS - len(evidence))

    # Extract average scores from call_rag results if available
    average_confidence_level = 0.0
    average_scam_probability = 0.0
    
    for ev in evidence:
        if ev.get("tool") == "rag-tools.call_rag" and isinstance(ev.get("output"), dict):
            average_confidence_level = ev["output"].get("average_confidence_level", 0.0)
            average_scam_probability = ev["output"].get("average_scam_probability", 0.0)
            break
    
    if average_confidence_level <= 0.9:
        # 2) Planner proposes optional tools (bounded)
        if budget_left > 0 and time.time() - t0 < TOOL_TIME_BUDGET:
            planner_in = {
                "document": {
                    "text": processed_document,
                    "confidence_level": average_confidence_level,
                    "scam_probability": average_scam_probability
                },
                "catalog": [
                    "extraction-tools.extract_link", "extraction-tools.extract_number", "extraction-tools.extract_organisation"
                ],   # add in other mcp-server tools from extraction-tools
                "max_calls": budget_left,
                "hints": {"MUST_already_done": [f"{s['server']}.{s['tool']}" for s in must_steps]},
            }
            plan = _chat_json(PLANNER_SYS, planner_in)
            opt_calls = _truncate_plan(plan, budget_left, whitelist=[
                "extraction-tools.extract_link", "extraction-tools.extract_number", "extraction-tools.extract_organisation"
            ]) 
            _execute_calls(opt_calls, evidence, errors, t0)

        # 3) Analyst fuses evidence
        analyst_in = {
            "document": {
                    "text": processed_document,
                    "confidence_level": average_confidence_level,
                    "scam_probability": average_scam_probability
                },
            "evidence": evidence
        }
        risk = _chat_json(ANALYST_SYS, analyst_in) or {}

        # 4) Supervisor validates & fixes JSON; apply rubric mapping
        supervised = _chat_json(SUPERVISOR_SYS, {"risk": risk})
        try:
            final = RiskAssessment(**supervised).model_dump()
        except Exception:
            # fallback minimal sane output
            final = RiskAssessment(verdict="suspicious", confidence=0.6, score=60,
                                factors=["fallback"], highlights=[]).model_dump()

    # If we skipped steps 2, 3 and 4 due to high confidence_level from extracted documents in database
    if average_confidence_level > 0.9 and average_scam_probability > 0.8:
        # High confidence, high scam probability - likely fraud
        final = RiskAssessment(
            is_scam="scam",
            confidence_level=average_confidence_level,
            scam_probability=average_scam_probability,
            explanation="High confidence fraud detection based on similar documents in database with strong scam indicators."
        ).model_dump()
    elif average_confidence_level > 0.9 and average_scam_probability < 0.2:
        # High confidence, low scam probability - likely legitimate
        final = RiskAssessment(
            is_scam="not_scam",
            confidence_level=average_confidence_level,
            scam_probability=average_scam_probability,
            explanation="High confidence legitimate detection based on similar documents in database with strong legitimacy indicators."
        ).model_dump()
    else:
        pass
    
    # 5) Executer carries out actions based on whether scam_label is 'scam' or 'not_scam'
    executer_steps = []
    if final.get("is_scam") == "not_scam":
        executer_steps = not_scam_executer()[:TOOL_MAX_CALLS]
    elif final.get("is_scam") == "scam":
        executer_steps = scam_executer()[:TOOL_MAX_CALLS]
    
    if executer_steps:
        _execute_calls(executer_steps, evidence, errors, t0)
        final["tool_evidence"] = evidence
        if errors: 
            final["tool_errors"] = errors

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
        "conversation_history": history
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
