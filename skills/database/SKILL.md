---
name: database
description: Design, query, migrate, or review application database access safely and efficiently. Use for schemas, repositories, ORM or SQL queries, transactions, indexes, data integrity, user-scoped resources, or persistence performance.
---

# Database Engineering

Keep data access explicit, constrained, and aligned with the application's existing database, query-builder, migration, and repository conventions.

## Establish The Data Contract

- Inspect the schema, migrations, nearby queries, and repository conventions before editing.
- Enforce required relationships, uniqueness, foreign keys, check constraints, and transaction boundaries in the database where the application relies on them.
- Select only the columns the next layer needs. Add or adjust indexes only for demonstrated query patterns, and preserve migration safety for existing data.
- Keep persistence implementation in repositories or the project's equivalent data-access layer; do not duplicate query logic across routes or services.

## Scope User Resources At The Query Boundary

When reading, changing, or deleting a user's resources, obtain the authenticated user ID directly from the already-validated session or JWT context at the query or repository boundary.

- Do not accept a `userId`, `ownerId`, or equivalent caller-supplied function parameter for that query—even if an upstream function validated it.
- Do not use a path, query, body, or client-supplied identifier as the ownership constraint.
- Combine the authenticated user ID with the requested resource identifier in the same query path. Return the project's normal not-found or authorization result when no owned row matches; do not perform an unscoped lookup followed by a separate ownership check.
- Apply the same rule to list filters, joins, updates, deletes, nested resources, and write-side parent lookups.

Use the authenticated context as the source of truth. Pass the context or an auth-aware repository dependency where the architecture requires it, rather than propagating its user ID as an ordinary parameter.

## Preserve Integrity And Performance

- Validate untrusted values at the application boundary; parameterize values rather than interpolating SQL.
- Use transactions for changes that must succeed or fail together, and check affected-row counts where absence matters.
- Avoid N+1 access by fetching related records in sets and mapping them locally.
- Handle concurrent writes with database constraints, suitable isolation, or explicit conflict handling instead of relying only on read-then-write application logic.

## Verify Data Behavior

- Reuse the repository's real database and authentication fixtures where available.
- Cover successful access, cross-user denial, missing owned resources, integrity failures, and transactional rollback when they apply.
- Run the narrowest relevant test or migration check, then the repository-required verification.
