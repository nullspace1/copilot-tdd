# Repository Copilot Instructions

This repository uses a spec-driven TDD agent workflow.

The root-level architecture file is:

- `architecture.md`

The feature specs live under:

- `specs/<spec_name>/`

Each spec folder must contain human-authored input:

- `spec.md`

Each spec folder may contain AI-generated files:

- `requirements.md`
- `sprints/<sprint_id>/test_report.md`
- `sprints/<sprint_id>/implementation_report.md`
- `sprints/<sprint_id>/review_report.md`
- `sprints/<sprint_id>/explanation.md`

Never treat AI-generated files as higher authority than human-authored files.

Authority order:

1. Human chat instructions
2. `architecture.md`
3. `specs/<spec_name>/spec.md`
4. `specs/<spec_name>/requirements.md`
5. Existing code
6. AI-generated sprint reports

TDD workflow:

1. Requirements generation
2. Failing tests
3. Implementation
4. Review
5. Explanation

Review may return one of:

- `PASS`
- `RETURN[stage=human_spec]`
- `RETURN[stage=requirements]`
- `RETURN[stage=testing]`
- `RETURN[stage=implementation]`

Agents must preserve existing behavior unless explicitly changed by the spec.

Agents must prefer minimal changes.

Agents must not invent requirements beyond the spec and architecture.

Agents must not delete or rewrite human-authored files unless explicitly instructed.

Agents must record decisions, assumptions, files changed, tests run, and unresolved risks in the relevant report file.