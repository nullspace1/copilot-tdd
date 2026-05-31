import json
from pathlib import Path
from typing import TypedDict, cast

import src.file as file

class Config(TypedDict):
    spec: str

def get() -> Config:
    return cast(Config, json.loads(file.read(Path(".tdd/config.json"))))

def save(config: Config) -> None:
    if not Path(".tdd").exists():
        Path(".tdd").mkdir()
        with open(".tdd/config.json", "w") as f:
            f.write(json.dumps(config, indent=2))
    