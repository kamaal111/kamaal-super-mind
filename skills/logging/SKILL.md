---
name: logging
description: Add or review application logging that records successes, failures, and workflow milestones so an execution can be followed up to its last successful step.
---

# Logging

- Log successful outcomes and every meaningful workflow milestone, as well
  as errors. Make it possible to tell how far an operation got before failing.
- Emit a milestone after its work succeeds. A started operation is not proof
  of completion; report success only after the promised effect is confirmed.
- Give each event a clear operation or stage, outcome, and enough safe context
  to connect events from the same execution, such as a request or job ID.
  On failure, include the failed stage and useful error details.
- Use the project's existing logger and conventions. Use `info` for successes
  and milestones, `warning` for handled degradation, `error` for failures,
  and `debug` for implementation details. Avoid repetitive per-item noise.
- Keep secrets and sensitive payloads out of logs; prefer safe IDs and counts.
- When adding or reviewing structured backend logs, read
  [references/structured-logging.md](references/structured-logging.md) for
  event fields, shared context propagation, and filtering guidance.
