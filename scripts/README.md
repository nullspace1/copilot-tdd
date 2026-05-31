# TDD Agent Scripts

These two scripts drive the spec-driven TDD workflow. They are invoked automatically by Claude's hooks defined in `hooks/tdd.json`.

---

## Overview

| Script | Hook | Trigger |
|---|---|---|
| `tdd-new.py` | `SessionStart` | Every time a new Claude session starts |
| `tdd-agent.py` | `SubagentStop` | Every time a sub-agent turn ends |

Both scripts read their input from stdin as a JSON object with a `prompt` key, and write their output back to stdout using the `hookSpecificOutput` format that Claude hooks expect.

---

## `tdd-new.py` — Session Start Handler

**Triggered by:** `SessionStart`

This script is the entry point for the TDD workflow. It decides whether to create a new spec or resume an existing one.

### Flow

```
SessionStart
    │
    ▼
Read prompt from stdin
    │
    ├─── Prompt matches "tdd-<spec-name>" pattern?
    │         │
    │         YES
    │         │
    │         ▼
    │    Create spec files under specs/<spec-name>/
    │    (requirements.md, test_scenarios.md, implementation.md,
    │     review.md, feedback.md, status.json)
    │         │
    │         ▼
    │    Check git state:
    │    - Must be on master branch
    │    - Must have no uncommitted changes
    │         │
    │         ▼
    │    Create branch: tdd/<spec-name>
    │    Commit and save ref: refs/tdd/<spec-name>/start
    │         │
    │         ▼
    │    Save spec name to .tdd/config.json
    │         │
    │         ▼
    │    Output: { status: "new spec", message: ... }
    │
    └─── Prompt does NOT match pattern
              │
              ▼
         Load active spec from .tdd/config.json
         Load current status from specs/<spec>/status.json
              │
              ├─── Status stage == "end"?
              │         │
              │         YES → Output: { status: "success", ... }
              │
              └─── Output: { status: <stage>, result: <result>,
                             revision: <n>, ... }
```

### Error Handling

If a `GitError` occurs during spec creation (e.g. dirty working tree, wrong branch), the script outputs an error prompt instructing Claude to notify the user and guide git state recovery. No spec is saved to config.

---

## `tdd-agent.py` — Sub-agent Stop Handler

**Triggered by:** `SubagentStop`

This script runs after every sub-agent turn. Its job is to detect whether a `return[<stage>]` result was written to `status.json` and, if so, execute a git-based rollback to the target stage while preserving history and feedback.

### Flow

```
SubagentStop
    │
    ▼
Load active spec from .tdd/config.json
Load current status from specs/<spec>/status.json
    │
    ├─── status.result matches "return[<stage>]"?
    │         │
    │         YES — Rollback sequence:
    │         │
    │         ▼
    │    Snapshot current TDD state (all iteration files + full history)
    │         │
    │         ▼
    │    Create preservation branch:
    │    feat/<spec>-revision-<n>
    │    Commit: "tdd(<spec>): preserve revision <n>"
    │         │
    │         ▼
    │    Switch back to feat/<spec>
    │    Hard reset to: refs/tdd/<spec>/<target-stage>
    │    Commit: "tdd(<spec>): return to <stage>"
    │         │
    │         ▼
    │    Restore snapshotted files onto working tree
    │    Write producing stage's file as new feedback.md
    │         │
    │         ▼
    │    Increment revision number
    │    Set stage = <target-stage>
    │    Set result = "read_feedback"
    │    Write updated status.json
    │         │
    │         ▼
    │    Output: { status: "return to", message: ... }
    │
    └─── No return — agent turn completed normally
              │
              ▼
         Output: { status: "finished",
                   message: "Your turn as <stage> is over." }
```

### Error Handling

Any `GitError` during the rollback sequence is caught, its `stderr` is printed, and the function returns early without modifying status. This leaves the repo in its pre-rollback state for manual inspection.

---

## Status Lifecycle

Each spec tracks its progress in `specs/<spec>/status.json`:

```json
{
  "stage": "requirements" | "test" | "implementation" | "review" | "explanation" | "end",
  "result": "start" | "progress" | "read_feedback" | "success"
           | "return[requirements]" | "return[test]"
           | "return[implementation]" | "return[review]" | "return[explanation]",
  "revision": 1
}
```

Stages advance linearly: `requirements → test → implementation → review → explanation → end`.

A `return[<stage>]` result triggers the rollback in `tdd-agent.py`, resetting back to any earlier stage and incrementing the revision counter.

---

## Git Ref Layout

| Ref | Purpose |
|---|---|
| `refs/tdd/<spec>/start` | Initial commit when the spec was created |
| `refs/tdd/<spec>/<stage>` | Saved commit after each stage completes |
| `feat/<spec>` | Active working branch for the spec |
| `feat/<spec>-revision-<n>` | Preservation branch created before each rollback |

---

## Source Modules (`src/`)

| Module | Responsibility |
|---|---|
| `git.py` | Thin wrappers around `git` CLI commands; raises `GitError` on failure |
| `file.py` | Path-safe read/write helpers for spec files |
| `parse.py` | Reads the prompt from stdin; detects new-spec patterns |
| `print.py` | Formats output in the `hookSpecificOutput` structure Claude expects |
| `spec.py` | Creates spec directory scaffolding and manages `.tdd/config.json` |
| `status.py` | Reads, writes, and inspects `status.json` for any spec |
| `config.py` | Loads and saves `.tdd/config.json` (tracks the active spec name) |
| `tdd_state.py` | Snapshots and restores all iteration files across revisions |
