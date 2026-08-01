---
name: backend
description: Implement, maintain, or refactor secure backend services in any language or framework. Use for routes, API contracts, middleware, authentication, business services, repositories, persistence, logging, validation boundaries, performance, or server integration tests.
---

# Backend Engineering

Keep backend changes aligned with layered API design, explicit contracts, boundary validation, structured logging, and integration-focused verification. Reuse nearby patterns before introducing a parallel server shape.

## Start With The Feature Slice

- Read the nearest route or feature module before editing. Keep work within the existing slice when the repository organizes code by feature.
- Prefer the repository task runner and verification commands to ad hoc command chains.
- Do not start a development server directly unless the repository explicitly requires it.

## Guard Every Boundary

- Validate external and unknown input at the boundary using the project's runtime-validation mechanism.
- Fail clearly when required dependency data is missing or unusable. Do not keep a misleading success payload alive with placeholders or undocumented nullability.
- Treat ownership as a boundary condition. Enforce it in the query or repository call rather than trusting a client-supplied identifier.

## Preserve Layering

- Keep route contracts, request definitions, and validation close to the edge.
- Delegate business orchestration to services and persistence concerns to repositories or equivalent data-access layers.
- Treat non-trivial response mapping as another validation boundary before returning it.
- Prefer context-injected dependencies over global singletons.

## Define Contracts Deliberately

- Document endpoints with the project's contract system, such as OpenAPI, when one exists.
- Define headers, path parameters, query, body, responses, and status codes in the contract layer when supported.
- Name schemas explicitly and reuse fragments for existing shapes.
- Use strict validation for values that must be correct; use non-throwing validation only when a graceful error branch is intentional.
- Validate response mapping, especially when combining data from multiple sources.

For framework-agnostic contract, response-validation, logging, and integration-test
patterns, read [references/api-contract-patterns.md](references/api-contract-patterns.md).
Map the concepts to the repository's chosen framework and libraries.

## Middleware, Authentication, And Logging

- Reuse shared authentication helpers after middleware guarantees the necessary identity.
- Keep middleware responsibilities narrow and separate app-owned state from generated or vendor-owned authentication code.
- Enrich request logging context as route and authenticated-user information becomes known.
- Use the shared structured logger when one exists. Emit a readable message plus flat, consistent machine fields for the event, request identifier, method, path, route, status, duration, authenticated user when known, and safe business context.
- Never log secrets, tokens, cookies, raw request bodies, or sensitive payload dumps.

## Persistence And Performance

- Select only the fields the next layer needs.
- Check write results explicitly and raise clear domain failures when required rows are missing.
- Collect equivalent bulk writes before one set-based insert or update.
- Avoid N+1 reads: fetch related records in sets and resolve them from a map.
- Resolve an ownership-sensitive parent before child lookups by a client-provided identifier. Filter or join on the authenticated ownership boundary in the same query path.

## Test And Verify

- Reuse existing app, auth, database, and request fixtures. Prefer integration coverage for routes, middleware, authentication, and persistence unless the change is truly isolated.
- Assert status, response shape, side effects, persisted state, logs when relevant, and cross-user access denial for ownership-sensitive changes.
- Run narrow verification while iterating, then the repository-required aggregate verification last.

## Completion Report

State the layers followed, routes/services/repositories/middleware touched, verification commands run, and whether the final aggregate verification passed or was skipped.
