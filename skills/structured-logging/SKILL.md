---
name: structured-logging
description: Design, add, or review structured logging for backend services that makes production behavior easy to understand and filter. Use when instrumenting server requests, jobs, consumers, persistence, dependencies, errors, or observability; when diagnosing missing or unexpected events; or when replacing ad hoc server logs. Do not use for webpages or mobile apps.
---

# Structured Logging

Apply this skill only to backend services. Do not use it to instrument webpages, browser clients, or mobile apps. Treat server logs as a queryable record of what happened, not a debugging diary. Make it possible to answer, from the logs alone: what was attempted, which entity or correlation was involved, what outcome occurred, and why.

## Propagate Log Context Automatically

Create a structured log context at the service boundary for each request, job, consumer message, or workflow. Put the common fields in it once: service identity, environment/version, correlation IDs, safe entity IDs already known at the boundary, and stable routing or operation fields.

Pass or bind that context through the whole call chain. Every logging call must read the current context and merge it automatically with the event-specific fields; do not make each caller manually repeat common fields. Extend the context immutably or with scoped child contexts as new facts become known, such as `user_id`, `order_id`, `attempt`, or dependency name. Ensure asynchronous work carries the correct context explicitly rather than relying on ambient state that can leak across requests.

Use the shared logger/context API as the single owner of field propagation. This keeps field names and values consistent, means every event is filterable by the same identifiers, and prevents a lower layer from accidentally dropping the execution story.

## Establish The Event Contract

1. Identify the unit whose story a person needs to follow: a request, user action, job, message, sync, or external call.
2. Define a stable `event` name that combines the domain and completed action or outcome, such as `checkout.completed`, `card.sync_failed`, or `session.refresh_completed`. Do not put variable data in the event name.
3. Attach fields as typed key-value data. Include a concise, human-readable `message` in every event, then add the structured fields needed to filter and explain it. Prefer stable `snake_case` keys and the same key for the same concept everywhere.
4. Include the correlation and entity identifiers that let an investigator move through the workflow: for example `request_id`, `trace_id`, `operation_id`, `job_id`, `user_id`, `order_id`, and `attempt`.
5. Record an explicit terminal `outcome`: `success`, `failure`, `rejected`, `cancelled`, `skipped`, or another domain-specific state. Include `duration_ms` where work takes time.

Build one context-rich completion event for each important unit of work. Enrich the scoped context during processing and emit it even when the unit throws or returns early. Add lifecycle events only when they answer a distinct question—for example a queued job never began, a retry is scheduled, or a long-running operation needs live progress.

```text
event=card.sync_completed message="Card sync completed" outcome=success
operation_id=op_… user_id=user_… source=remote_api
received_count=48 saved_count=48 skipped_count=0 duration_ms=183
```

This single event must make both success and absence legible: filter `event = card.sync_completed` to see completed work; compare `received_count` and `saved_count`, or query `outcome != success`, to see why an expected result did not occur.

## Capture Useful Context

Add fields that distinguish materially different paths, not just fields that happen to be nearby.

- Identify the operation, actor or safe entity ID, inputs category, dependency, response/status, retry count, feature/configuration variant, and version when they affect behavior.
- Record counts, flags, durations, state transitions, and normalized error codes as separate values. Preserve numbers and booleans as their native types.
- Emit errors with `error_type`, stable `error_code` when available, `error_message`, and `is_retryable`. Include the underlying error safely without replacing the operation context.
- Use levels consistently: `error` for failed work requiring attention, `warning` for a handled but surprising/degraded path, `info` for important boundary or terminal outcomes, and `debug` for optional diagnostic detail.

Favor high-cardinality identifiers in logs when they enable incident investigation. Do not treat a metrics system's cardinality limits as a reason to omit useful log fields.

## Make Filtering Predictable

Use a small shared vocabulary rather than inventing names at every call site.

| Need | Preferred fields |
| --- | --- |
| Find one execution | `request_id`, `trace_id`, `operation_id`, `job_id` |
| Find affected data | domain IDs such as `user_id`, `card_id`, `order_id` |
| Understand result | `event`, `outcome`, `status_code`, `error_code`, `duration_ms` |
| Explain a divergent path | `attempt`, `reason`, `source`, `state_before`, `state_after`, `feature_flag` |
| Locate the running software | `service`, `component`, `environment`, `version` |

Keep values normalized (`success`, not a mixture of `ok`, `done`, and `Success`). Add a field instead of interpolating it into a message. Avoid logging the same failure at every layer; give the authoritative boundary the complete event and let lower layers add only non-duplicative diagnostic context.

## Preserve Privacy And Signal

Never log credentials, tokens, cookies, authorization headers, payment data, raw sensitive payloads, or unnecessary personal content. Prefer opaque IDs, categories, counts, and allowlisted fields. Redact at the shared logging boundary when possible.

Do not emit a line for every implementation detail. Excess volume and repetitive messages hide the important record, increase cost, and make absence impossible to interpret. If sampling is necessary, retain all failures, slow operations, retries, and rollout/debug cohorts; sample only ordinary successful outcomes and record the sampling decision when it affects interpretation.

## Implement And Review

Before editing, inspect the project's logger, existing field conventions, log pipeline, and sensitive-data policy. Extend the shared logger or workflow boundary rather than creating competing formats.

For each changed workflow, trace all exits—success, expected rejection, handled degradation, cancellation, and thrown error. Ensure each has a terminal event with the same correlation fields and a truthful outcome. Log an expected absence explicitly when it changes the user's story, for example `cache.lookup_completed outcome=miss` or `export.completed outcome=success exported_count=0`.

Review the result as an investigator:

1. Filter by a known identifier and reconstruct one execution without reading source.
2. Filter by the event and outcome to distinguish success, failure, and expected absence.
3. Filter/group by `error_code`, dependency, version, or feature flag to explain a pattern.
4. Verify that a success record proves the promised effect, rather than merely proving that a function started.

Keep the required `message` short, stable, and human-readable; put variable and explanatory data in fields. Match the project's logging API rather than forcing a particular JSON or telemetry library—structured events and deliberate context matter more than the transport.
