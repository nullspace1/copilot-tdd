
from typing import TypedDict

import scripts.src.file as file
import scripts.src.status as status


class TDDIteration(TypedDict):
    
    requirements_file: str | None
    test_scenarios_file: str | None
    implementation_file: str | None
    review_file: str | None

class TDDState(TypedDict):
    
    iteration: TDDIteration
    revision: int
    
    history: list[TDDIteration]
    
   
def copy_history_files(spec: str, revision: int) -> list[TDDIteration]:
    
    history : list[TDDIteration] = []
    
    for i in range(revision - 1):
        
        history.append(
            {
                "requirements_file": file.read_optional(file.spec_path(spec, f"history/revision-{i + 1}/requirements.md")),
                "test_scenarios_file": file.read_optional(file.spec_path(spec, f"history/revision-{i + 1}/test_scenarios.md")),
                "implementation_file": file.read_optional(file.spec_path(spec, f"history/revision-{i + 1}/implementation.md")),
                "review_file": file.read_optional(file.spec_path(spec, f"history/revision-{i + 1}/review.md"))
            }
        )
        
    return history

def copy_tdd_state(spec: str) -> TDDState:
    
    revision_number = status.current_status(spec)
    
    return {
        "iteration": {
            "requirements_file": file.read_optional(file.spec_path(spec, "requirements.md")),
            "test_scenarios_file": file.read_optional(file.spec_path(spec, "test_scenarios.md")),
            "implementation_file": file.read_optional(file.spec_path(spec, "implementation.md")),
            "review_file": file.read_optional(file.spec_path(spec, "review.md"))
        },
        "revision": revision_number["revision"],
        "history": copy_history_files(spec, revision_number["revision"])
    }
    
def paste_tdd_state(spec: str, state: TDDState) -> None:
    
    file.write_if_content(file.spec_path(spec, "requirements.md"), state["iteration"]["requirements_file"])
    file.write_if_content(file.spec_path(spec, "test_scenarios.md"), state["iteration"]["test_scenarios_file"])
    file.write_if_content(file.spec_path(spec, "implementation.md"), state["iteration"]["implementation_file"])
    file.write_if_content(file.spec_path(spec, "review.md"), state["iteration"]["review_file"])
    
    for i in range(len(state["history"])):
        file.write_if_content(file.spec_path(spec, f"history/revision-{i + 1}/requirements.md"), state["history"][i]["requirements_file"])
        file.write_if_content(file.spec_path(spec, f"history/revision-{i + 1}/test_scenarios.md"), state["history"][i]["test_scenarios_file"])
        file.write_if_content(file.spec_path(spec, f"history/revision-{i + 1}/implementation.md"), state["history"][i]["implementation_file"])
        file.write_if_content(file.spec_path(spec, f"history/revision-{i + 1}/review.md"), state["history"][i]["review_file"])
        
        
        
def add_feedback_from(spec: str, stage: str, state: TDDState) -> None:
    
    file.write(file.spec_path(spec, "feedback.md"), state["iteration"][f"{stage}_file"])