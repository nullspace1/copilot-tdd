import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypeAlias, cast

AgentType: TypeAlias = Literal["requirements", "test", "implementation", "review", "explanation"]
Stage: TypeAlias = Literal["requirements", "test", "implementation", "review", "explanation", "end"]
Result: TypeAlias = Literal[
    "start",
    "read_feedback",
    "progress",
    "success",
    "return[requirements]",
    "return[test]",
    "return[implementation]",
    "return[review]",
    "return[explanation]",
]

AGENTS: list[AgentType] = ["requirements", "test", "implementation", "review", "explanation"]
CONFIG_PATH = Path(".tdd-config.json")
PROMPT_SPEC_RE = re.compile(r"@tdd-orchestrator\s+([a-zA-Z0-9-]+)")


class Metadata:
    @staticmethod
    def write(path: str | Path, data: dict[str, Any]) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    @staticmethod
    def read(path: str | Path) -> dict[str, Any]:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    @staticmethod
    def exists(path: str | Path) -> bool:
        return Path(path).exists()


class Text:
    @staticmethod
    def read(path: str | Path) -> str:
        return Path(path).read_text(encoding="utf-8")

    @staticmethod
    def write(path: str | Path, content: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")


@dataclass
class StatusData:
    stage: Stage
    result: Result
    revision: int

    def dump(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "revision": self.revision,
            "result": self.result,
        }

    def update(self, key: str, value: Any) -> "StatusData":
        setattr(self, key, value)
        return self


class Status:
    def __init__(self, spec: str) -> None:
        self.spec = spec
        self.status_file = Path("specs") / spec / "status.json"

        if not self.status_file.exists():
            Metadata.write(self.status_file, StatusData("requirements", "start", 1).dump())

    def read(self) -> StatusData:
        data = Metadata.read(self.status_file)
        return StatusData(**data)

    def write(self, status: StatusData) -> None:
        Metadata.write(self.status_file, status.dump())

    def update_stage(self, stage: Stage) -> None:
        self.write(self.read().update("stage", stage))

    def update_revision(self) -> None:
        status = self.read()
        status.revision += 1
        self.write(status)

    def update_result(self, result: Result) -> None:
        self.write(self.read().update("result", result))


class History:
    def __init__(self, spec: str) -> None:
        self.spec = spec
        self.history_folder = Path("specs") / spec / "history"
        self.history_folder.mkdir(parents=True, exist_ok=True)

    def write(self, revision: int, agent_files: dict[AgentType, str]) -> None:
        revision_folder = self.history_folder / f"revision-{revision}"
        revision_folder.mkdir(parents=True, exist_ok=True)

        for stage, content in agent_files.items():
            Text.write(revision_folder / f"{stage}.md", content)


class Feedback:
    def __init__(self, spec: str) -> None:
        self.spec = spec
        self.feedback_file = Path("specs") / spec / "feedback.md"

        if not self.feedback_file.exists():
            Text.write(self.feedback_file, "")


class Git:
    def run(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        return result.stdout.strip()

    def get_branch(self) -> str:
        return self.run("rev-parse", "--abbrev-ref", "HEAD")

    def create_branch(self, branch: str) -> None:
        self.run("switch", "-c", branch)

    def switch_branch(self, branch: str) -> None:
        self.run("switch", branch)

    def save_ref(self, ref: str, commit_hash: str) -> None:
        self.run("update-ref", ref, commit_hash)

    def reset_hard(self, ref: str) -> None:
        self.run("reset", "--hard", ref)

    def no_uncommitted_changes(self) -> bool:
        return self.run("status", "--porcelain") == ""

    def commit(self, message: str) -> str:
        self.run("add", ".")

        if self.run("diff", "--cached", "--name-only") != "":
            self.run("commit", "-m", message)

        return self.run("rev-parse", "HEAD")


class AgentDataManager:
    agents: list[AgentType] = AGENTS

    def __init__(self, spec: str) -> None:
        self.spec = spec
        self.git = Git()
        self.status = Status(spec)
        self.history = History(spec)
        self.feedback = Feedback(spec)

    def get_stage(self) -> Stage:
        return self.status.read().stage

    def get_result(self) -> Result:
        return self.status.read().result

    def not_started(self) -> bool:
        return self.get_stage() == "requirements" and self.get_result() == "start"

    def begin(self) -> None:
        if self.git.get_branch() != "main":
            raise RuntimeError("Not on main branch.")

        if not self.git.no_uncommitted_changes():
            raise RuntimeError("There are uncommitted changes.")

        self.git.create_branch(f"feat/{self.spec}")
        self.status.update_stage("requirements")
        self.status.update_result("progress")
        commit_hash = self.git.commit(f"tdd({self.spec}): start workflow")
        self.git.save_ref(f"refs/tdd/{self.spec}/start", commit_hash)

    def advance_stage(self) -> None:
        current_stage = self.get_stage()

        if current_stage == "end":
            return

        agent = cast(AgentType, current_stage)
        commit_hash = self.git.commit(f"tdd({self.spec}): {agent} completed")
        self.git.save_ref(f"refs/tdd/{self.spec}/{agent}", commit_hash)

        index = self.agents.index(agent)

        if index == len(self.agents) - 1:
            self.status.update_stage("end")
            self.status.update_result("success")
        else:
            self.status.update_stage(self.agents[index + 1])
            self.status.update_result("progress")

    def fetch_data(self, up_to_stage: AgentType) -> tuple[dict[AgentType, str], dict[AgentType, str], str, StatusData]:
        agent_files_to_save: dict[AgentType, str] = {}
        agent_files_to_discard: dict[AgentType, str] = {}

        split_index = self.agents.index(up_to_stage)

        for stage in self.agents[: split_index + 1]:
            agent_files_to_save[stage] = read_optional_text(Path("specs") / self.spec / f"{stage}.md")

        for stage in self.agents[split_index + 1 :]:
            agent_files_to_discard[stage] = read_optional_text(Path("specs") / self.spec / f"{stage}.md")

        feedback = Text.read(self.feedback.feedback_file)
        status = self.status.read()

        return agent_files_to_discard, agent_files_to_save, feedback, status

    def revert_to_stage(self, stage: AgentType) -> None:
        discard_agent_docs, saved_agent_docs, feedback, status = self.fetch_data(stage)

        revision_branch = f"feat/{self.spec}/revision/{status.revision}"
        self.git.create_branch(revision_branch)
        self.git.commit(f"tdd({self.spec}): preserve revision {status.revision}")

        self.git.switch_branch(f"feat/{self.spec}")
        self.git.reset_hard(f"refs/tdd/{self.spec}/{stage}")
        self.git.commit(f"tdd({self.spec}): reset to {stage}")

        self.history.write(status.revision, discard_agent_docs)

        for saved_stage, content in saved_agent_docs.items():
            Text.write(Path("specs") / self.spec / f"{saved_stage}.md", content)

        Text.write(self.feedback.feedback_file, feedback)

        self.status.update_stage(stage)
        self.status.update_revision()
        self.status.update_result("read_feedback")
        self.git.commit(f"tdd({self.spec}): return to {stage}")


def read_optional_text(path: Path) -> str:
    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8")


def load_stdin_json() -> dict[str, Any]:
    if sys.stdin.isatty():
        return {}

    raw = sys.stdin.read().strip()

    if raw == "":
        return {}

    return json.loads(raw)


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        save_config({})
        return {}

    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def parse_spec_from_prompt(prompt: str) -> str | None:
    match = PROMPT_SPEC_RE.search(prompt)

    if match is None:
        return None

    return match.group(1)


def resolve_spec(prompt: str, config: dict[str, Any]) -> str:
    prompt_spec = parse_spec_from_prompt(prompt)

    if prompt_spec is not None:
        save_config({"spec": prompt_spec})
        return prompt_spec

    config_spec = config.get("spec")

    if isinstance(config_spec, str) and config_spec != "":
        return config_spec

    raise RuntimeError("No spec folder provided.")


def verify_spec_exists(spec: str) -> None:
    if not (Path("specs") / spec).exists():
        raise RuntimeError(f"Spec folder does not exist: specs/{spec}")


def begin_agent(spec: str) -> dict[str, Any]:
    agent_data_manager = AgentDataManager(spec)

    if agent_data_manager.not_started():
        agent_data_manager.begin()

    return {
        "active_agent": agent_data_manager.get_stage(),
        "last_result": agent_data_manager.get_result(),
        "message": "Begin agent turn.",
    }


def end_subagent_turn(spec: str) -> dict[str, Any]:
    agent_data_manager = AgentDataManager(spec)
    result = agent_data_manager.get_result()

    if result.startswith("return["):
        target = cast(AgentType, result.removeprefix("return[").removesuffix("]"))
        agent_data_manager.revert_to_stage(target)

        return {
            "status": "return",
            "message": "Sub-agent requested return to an earlier stage. Stop immediately and notify user.",
        }

    agent_data_manager.advance_stage()

    return {
        "status": "success",
        "message": "Sub-agent successfully completed its turn.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("tddctl")
    parser.add_argument("command", choices=["begin", "subagent"])
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        hook_input = load_stdin_json()
        prompt = str(hook_input.get("prompt", ""))
        config = load_config()
        spec = resolve_spec(prompt, config)

        verify_spec_exists(spec)

        if args.command == "begin":
            result = begin_agent(spec)
        elif args.command == "subagent":
            result = end_subagent_turn(spec)
        else:
            raise RuntimeError(f"Unknown command {args.command}")

    except Exception as error:
        result = {
            "status": "error",
            "error": str(error),
            "message": "End immediately and notify user.",
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()