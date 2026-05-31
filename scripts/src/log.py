from pathlib import Path

import src.file as file

def log(string: str) -> None:
    file.append(path=Path(".tdd/log.txt"), content=f"{string}\n")