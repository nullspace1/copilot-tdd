import json
from typing import Any


def print_prompt(data : dict[str, Any]) -> None:
    data = { 
        "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": json.dumps(data)
        }
    }
    print(json.dumps(data))