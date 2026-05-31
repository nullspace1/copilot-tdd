import json
from pathlib import Path
import re
from typing import Literal, TypedDict, cast

type Stage = Literal["requirements", "test", "implementation", "review", "explanation", "end"]
type Result = Literal["start", "read_feedback", "progress", "success", "return[requirements]", "return[test]", "return[implementation]", "return[review]", "return[explanation]"]


class StatusData(TypedDict):
    stage: Stage
    result: Result
    revision: int
    
def status(stage : Stage, result: Result, revision: int) -> StatusData:
    return {
        "stage": stage,
        "result": result,
        "revision": revision
    }
    
def current_status(spec: str) -> StatusData:
    status_file = Path("specs") / spec / "status.json"
    return json.loads(status_file.read_text())
    
def dump(status: StatusData) -> str:
    return json.dumps(status)
    
def initial_status(spec: str) -> StatusData:
    return status("requirements", "start", 1)

def status_ended(status: StatusData) -> bool:
    return status["stage"] == "end"

def check_return(status: StatusData) -> Stage | None:
    return_regex = r"return\[(.+)\]"
    match = re.search(return_regex, status["result"])
    if match:
        return cast(Stage, match.group(1))
    else:
        return None
    
def write_status(spec: str, status: StatusData) -> None:
    status_file = Path("specs") / spec / "status.json"
    status_file.write_text(dump(status))