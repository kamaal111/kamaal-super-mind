---
name: plan-mode
description: Create implementation-ready plans that another agent can execute without the planner's conversational context. Use when planning a code, configuration, documentation, migration, or multi-step repository change, especially before handing implementation to another agent or team.
---

# Plan Mode

Produce a plan that is complete in the information an implementer needs and economical in everything else. Treat the plan as the handoff artifact, not a record of the investigation.

## Investigate Before Planning

1. Read the repository instructions and inspect the current implementation, callers, tests, configuration, and task-runner commands relevant to the request.
2. Identify the behavior owner and the observable contract: inputs, outputs, state changes, error behavior, compatibility requirements, and affected consumers.
3. Resolve material uncertainty through repository evidence. Record an assumption only when it remains necessary for implementation.
4. Do not write an implementation plan until each step can name its target and intended result.

## Write the Plan

Start with a one-sentence outcome. Then use the following sections when applicable:

- **Scope and decisions**: State the required behavior, explicit non-goals, and only unresolved assumptions that change implementation.
- **Implementation steps**: Order steps by dependency. For every step, name the file path and the specific symbol, route, schema, component, or configuration block to change. State the precise change, the resulting behavior, relevant data/control flow, compatibility or failure handling, and any required follow-on edits. Include rationale only when it selects between plausible implementations.
- **Validation**: Name the exact tests to add or change, their cases and assertions, relevant existing tests to run, required commands, and any manual checks. Cover success, failure, authorization/ownership, boundary, migration, or compatibility cases when they apply.
- **Handoff notes**: List only blockers, prerequisites, or decisions that the implementer cannot discover from the steps.

## Detail Standard

Make every detail actionable. An implementer who has not seen the planning conversation must be able to determine what to edit, how the behavior should work, and how to verify it.

- Include repository-derived paths and symbols instead of vague phrases such as "update the backend" or "add tests."
- Describe behavior, constraints, and interfaces rather than prescribing incidental syntax.
- Specify ordering when one change depends on another.
- Separate confirmed facts from assumptions and choices.
- Remove discovery narration, alternatives already rejected, generic best practices, and implementation trivia that neither changes a decision nor helps execute or validate a step.
- Do not pad a plan with boilerplate sections that are not relevant to the task.

Before delivering the plan, reread it as a fresh implementer. Tighten any step that needs missing context; remove any sentence that would not guide an implementation or verification decision.
