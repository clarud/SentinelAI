# services/worker/worker/agents/config.py
import os
from dotenv import load_dotenv
load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMP  = float(os.getenv("LLM_TEMPERATURE", "0.2"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Tooling budgets
TOOL_MAX_CALLS   = int(os.getenv("TOOL_MAX_CALLS", "5"))
TOOL_TIME_BUDGET = float(os.getenv("TOOL_TIME_BUDGET_S", "6.0"))

