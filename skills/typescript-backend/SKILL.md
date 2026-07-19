---
name: typescript-backend
description: Implement, maintain, or refactor secure TypeScript backend services. Use when changing routes, request or response schemas, middleware, services, repositories, authentication, persistence, structured logging, data-validation boundaries, or server integration tests.
---

# TypeScript Backend Best Practices

Keep backend changes aligned with layered API design, runtime validation, structured logging, and integration-focused verification. Reuse nearby patterns before introducing a parallel server shape.

## Start With The Feature Slice

- Read the nearest route or feature module before editing. Keep work within the existing slice when the repository organizes code by feature.
- Prefer the repository task runner and verification commands to ad hoc command chains.
- Do not start a development server directly unless the repository explicitly requires it.

## Guard Every Boundary

- Validate external and unknown input with runtime schemas at the boundary.
- Avoid casts, suppression comments, and lint bypasses. Repair the type flow or validate the value instead.
- Reuse shared constants, schemas, and helpers when they fit.
- Fail clearly when required dependency data is missing or unusable. Do not keep a misleading success payload alive with placeholders or undocumented nullability.
- Treat ownership as a boundary condition. Enforce it in the query or repository call rather than trusting a client-supplied identifier.

## Preserve Layering

- Keep route contracts, request definitions, and validation close to the edge.
- Keep request and response schemas explicit and reusable. Read validated data from the framework's validated request surface instead of parsing it again downstream.
- Type handler context so validated input flows without casts where the framework supports it.
- Delegate business orchestration to services and persistence concerns to repositories or equivalent data-access layers.
- Treat non-trivial response mapping as another validation boundary before returning it.

## Define Contracts Deliberately

- Document endpoints with the project's contract system, such as OpenAPI, when one exists.
- Define headers, path parameters, query, body, responses, and status codes in the contract layer when supported.
- Name schemas explicitly and reuse fragments for existing shapes.
- When the contract system generates OpenAPI from schemas, document every externally surfaced field with a description and representative example, and register each reusable root schema with a stable name, title, description, and object-level example. Treat schema documentation as part of the API contract, not optional polish.
- Use strict parsing for values that must be correct; use safe parsing only when a graceful validation branch is intentional.
- Validate response mapping especially when combining data from multiple sources.

## Middleware And Authentication

- Prefer context-injected dependencies over global singletons.
- Reuse shared authentication helpers after middleware guarantees the necessary identity.
- Keep middleware responsibilities narrow and separate app-owned state from generated or vendor-owned authentication code.
- Enrich request logging context as route and authenticated-user information becomes known.

## Persistence And Performance

- Select only the fields the next layer needs and derive repository-local input or output types from the persistence layer when possible.
- Check write results explicitly and raise clear domain failures when required rows are missing.
- Collect equivalent bulk writes before one set-based insert or update.
- Avoid N+1 reads: fetch related records in sets and resolve them from a map.
- Resolve an ownership-sensitive parent before child lookups by a client-provided identifier. Filter or join on the authenticated ownership boundary in the same query path.

## Structured Logging

- Use the shared logger rather than `console.*` when the project has structured logging.
- Emit a human-readable message plus flat, consistent machine fields: event, request identifier, method, path, route, status, duration, authenticated user when known, and safe business context.
- Keep equivalent event names and fields consistent so one user flow can be correlated across logs.
- Never log secrets, tokens, cookies, raw request bodies, or sensitive payload dumps.
- Update tests when observable logging behavior changes.

## Test And Verify

- Reuse existing app, auth, database, and request fixtures. Prefer integration coverage for routes, middleware, authentication, and persistence unless the change is truly isolated.
- Assert status, response shape, side effects, persisted state, logs when relevant, and cross-user access denial for ownership-sensitive changes.
- Use production schemas to parse test responses when it keeps the contract honest.
- Run narrow compile, lint, typecheck, or test commands while iterating, then the repository-required aggregate verification last.

## Completion Report

State the layers followed, routes/services/repositories/middleware touched, verification commands run, and whether the final aggregate verification passed or was skipped.

## Project-Derived Examples

For concrete Hono, Zod, OpenAPI, Pino-style logging, and integration-test patterns,
read [references/hono-zod-openapi.md](references/hono-zod-openapi.md). Treat it as
an optional framework reference; the workflow above remains framework-neutral.
