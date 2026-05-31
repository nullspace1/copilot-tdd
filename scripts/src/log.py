from pathlib import Path

from scripts.src.file import write


def log(string: str) -> None:
    write(path=Path(".tdd/log.txt"), content=f"{string}\n")