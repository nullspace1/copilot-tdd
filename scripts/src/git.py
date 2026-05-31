import subprocess
import src.log as log


class GitError(Exception):
    def __init__(self, stderr: str):
        super().__init__(stderr)
        self.stderr = stderr

def git(*args: str) -> str:
    
    result = subprocess.run(
            ["git", *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    
    log.log("git " + " ".join(args) + "\n ---" + result.stdout)
    
    if result.returncode != 0:
        raise GitError(result.stderr)
    
    return result.stdout

def switch_branch(branch: str) -> str:
    return git("switch", branch)

def delete_branch(branch : str) -> str:
    return git("branch", "-D", branch)
    
def create_branch(branch: str) -> str:
    return git("switch", "-c", branch)
    
def branch_exists(branch: str) -> bool:
    try:
        git("rev-parse", "--verify", branch)
        return True
    except GitError:
        return False
    
def commit(message: str) -> str:
    git("commit", "-m", message)
    return git("rev-parse", "HEAD")

def reset_hard(ref: str) -> str:
    return git("reset", "--hard", ref)
    
def uncommitted_changes() -> bool:
    return git("diff-index", "--quiet", "HEAD") != ""

def current_branch() -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD")

def add(path: str) -> str:
    return git("add", path)

def save_ref(ref: str, commit_hash: str) -> str:
    return git("update-ref", ref, commit_hash)