from pathlib import Path


def write(path: Path, content: str) -> None:
    with path.open("w") as f:
        f.write(content)
        
    
def append(path: Path, content: str) -> None:
    with path.open("a") as f:
        f.write(content)
    
    
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
        
    return path.read_text(encoding="utf-8")

def opt_write(path: Path, content: str) -> None:
    if not path.exists():
        write(path, content)
        
def write_if_content(path: Path, content: str | None) -> None:
    if content:
        write(path, content)
        
def spec_path(spec: str, filename: str) -> Path:
    return Path("specs") / spec / filename


