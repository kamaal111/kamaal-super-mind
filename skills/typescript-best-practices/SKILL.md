---
name: typescript-best-practices
description: Write, edit, or refactor clear, resilient TypeScript source. Use when implementing TypeScript applications, libraries, models, services, clients, utilities, runtime schemas, type definitions, error handling, logging, or tests.
---

# TypeScript Best Practices

Follow the repository's established TypeScript style first. Use these rules where the local codebase has no stronger convention.

## Preserve Runtime And Static Type Flow

- Treat external and unknown values as `unknown` until validated with the project's runtime-validation mechanism. Static types do not validate untrusted data at runtime.
- Avoid casts, non-null assertions, suppression comments, and lint bypasses. Repair the type flow, narrow the value, or validate it instead.
- Define reusable schemas or type guards at the boundary. Infer or derive TypeScript types from that single source of truth where the chosen tooling supports it.
- Prefer explicit return types at exported or otherwise meaningful boundaries when they clarify the contract; let local implementation details infer naturally.

## Model Absence And Failure Deliberately

- Represent expected absence and failure in the type system instead of returning misleading placeholder values.
- Narrow optional values at the point their presence becomes required. Do not defer an unsafe assumption to a distant caller.
- Use discriminated unions for finite state or result domains when callers need to handle each case explicitly.
- Use `never`-checked exhaustive branches when a union represents closed application state.

## Keep Types Maintainable

- Prefer `type` for object shapes, unions, and transformations; use `interface` when declaration merging or an extensible public object contract is intentional. Follow local convention when one exists.
- Derive types from authoritative data, schemas, or persistence declarations rather than maintaining parallel copies.
- Keep generics constrained and named for the role they play. Do not add generic abstraction when a concrete type is clearer.
- Avoid `any`. Use `unknown`, a precise union, or a generic constraint and then narrow deliberately.

## Function Parameters

- When a function accepts more than three parameters, collapse them into a single options object parameter instead of a long positional list.
- Define a named `type` for the object shape so callers and readers have one authoritative contract, and destructure it in the function signature.

Prefer:

```typescript
type CreateUserParams = {
  email: string;
  displayName: string;
  role: UserRole;
  isActive: boolean;
};

function createUser({ email, displayName, role, isActive }: CreateUserParams): User {
  // ...
}
```

Avoid:

```typescript
function createUser(
  email: string,
  displayName: string,
  role: UserRole,
  isActive: boolean,
): User {
  // ...
}
```

## Test The Contract

- Compile and typecheck while iterating; do not treat a passing runtime test as proof that public type contracts remain sound.
- Exercise invalid and boundary input in tests when runtime validation or narrowing is part of the behavior.
- Use production schemas to parse test fixtures or responses when it keeps the runtime and static contract honest.
