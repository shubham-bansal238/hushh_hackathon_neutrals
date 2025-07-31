import json
from typing import Dict, Any

def build_usage_prompt(instruction: str, context: dict) -> str:
    """
    Builds a general-purpose prompt for LLMs given an instruction and context dict.
    """
    return f"""
{instruction}

Context:
{json.dumps(context, indent=2)}
"""
