# services/worker/worker/agents/config.py
import os
from dotenv import load_dotenv
load_dotenv()

# Tooling budgets
TOOL_MAX_CALLS   = int(os.getenv("TOOL_MAX_CALLS", "5"))
TOOL_TIME_BUDGET = float(os.getenv("TOOL_TIME_BUDGET_S", "6.0"))