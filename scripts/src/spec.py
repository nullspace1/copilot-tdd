import json
from pathlib import Path
from typing import Any

from griffe import GitError

import src.file as file
import src.git as git
import src.status as status
from src import config

def create_spec(spec : str) -> None:
    
    file.opt_write(file.spec_path(spec,"requirements.md"), "")
    file.opt_write(file.spec_path(spec,"test_scenarios.md"), "")
    file.opt_write(file.spec_path(spec,"implementation.md"), "")
    file.opt_write(file.spec_path(spec,"review.md"), "")
    file.opt_write(file.spec_path(spec,"feedback.md"), "")
    file.opt_write(file.spec_path(spec,"status.json"), status.dump(status.initial_status(spec)))
    
    if (git.uncommitted_changes()):
        raise GitError("There are uncommitted changes."
                       "Please commit them before creating a new spec.")
    
    if (git.current_branch() != "master"):
        raise GitError("Not on main branch.")
    
    if (git.branch_exists(f"tdd/{spec}")):
        git.delete_branch(f"tdd/{spec}")
    git.create_branch(f"tdd/{spec}")
    git.add(".")
    git.save_ref(f"refs/tdd/{spec}/start", git.commit(f"tdd({spec}) : start workflow"))
    
def spec_from_config() -> str:
    tdd_config : config.Config = config.get()
    return tdd_config["spec"]

def write_spec_to_config(spec : str) -> None:
    tdd_config : config.Config = {"spec": spec}
    config.save(tdd_config)