import json
import re
import sys
from typing import Any

NEW_SPEC_REGEX = re.compile(r"tdd-+([a-zA-Z0-9-]+)")


def load_prompt() -> str:
    if sys.stdin.isatty():
        return ""

    raw = sys.stdin.read().strip()

    if raw == "":
        return ""

    return json.loads(raw)["prompt"]


def new_spec(prompt: str) -> bool:
    match = NEW_SPEC_REGEX.search(prompt)
    return match is not None