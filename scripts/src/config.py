import json
from pathlib import Path
from typing import TypedDict, cast

import scripts.src.file as file

class Config(TypedDict):
    spec: str

def get() -> Config:
    return cast(Config, json.loads(file.read(Path(".tdd/config.json"))))

def save(config: Config) -> None:
    Path(".tdd/config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    