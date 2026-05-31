import json
from os import mkdir
import re
import sys

NEW_SPEC_REGEX = re.compile(r"tdd-+([a-zA-Z0-9-]+)")


def load_prompt() -> str:
    if sys.stdin.isatty():
        return ""

    raw = sys.stdin.read().strip()

    if raw == "":
        return ""

    message = json.loads(raw)["prompt"]

    return message


def is_new_spec(prompt: str) -> bool:
    match = NEW_SPEC_REGEX.search(prompt)
    return match is not None

def parse_spec(prompt: str) -> str:
    return prompt.split("tdd-")[-1].strip()