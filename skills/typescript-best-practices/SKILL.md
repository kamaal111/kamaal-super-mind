---
name: typescript-best-practices
description: Write, edit, or refactor clear, resilient TypeScript source. Use when implementing TypeScript applications, libraries, models, services, clients, utilities, runtime schemas, type definitions, error handling, logging, or tests.
---

# TypeScript Best Practices

Follow the repository's established TypeScript style first. Use these rules where the local codebase has no stronger convention.

## Prefer Pure Transformations

- Prefer pure functions that return new values. Treat parameters and nested data as read-only; do not mutate caller-owned objects or arrays, or write to captured, global, or shared state from transformation logic.
- Use `readonly` properties and `ReadonlyArray<T>` or `readonly T[]` for input contracts where appropriate. `const` prevents rebinding but does not make an object immutable; `Readonly<T>` is shallow, so model nested read-only data deliberately.
- Use non-mutating collection operations or copy before sorting or updating, respecting the configured runtime target. A shallow copy still shares nested objects; do not mutate them through the copy.
- Keep side effects in explicit orchestration or state-owner operations. Local mutation of newly created, unshared values is acceptable when clearer or more efficient; do not force loops into `reduce` or introduce FP abstractions solely for style.

## Collection Performance

- Array `filter` and `map` are eager: `items.filter(predicate).map(mapper)` traverses the filtered items again and allocates an intermediate array. Prefer a clear `for...of` loop that tests each item and appends the transformed matches to a locally owned result when that intermediate array has no independent use.
- Keep inputs read-only and callbacks pure; combining passes interleaves filtering and mapping, so preserve observable behavior. Do not force an elaborate `reduce` or allocate a temporary array per item merely to express the operation as a chain. Use lazy iterator APIs only when supported by the configured runtime, and materialize the result at the boundary that needs it.

## Preserve Runtime And Static Type Flow

- Treat external and unknown values as `unknown` until validated with the project's runtime-validation mechanism. Static types do not validate untrusted data at runtime.
- Avoid casts, non-null assertions, suppression comments, and lint bypasses. Repair the type flow, narrow the value, or validate it instead.
- Define reusable schemas or type guards at the boundary. Infer or derive TypeScript types from that single source of truth where the chosen tooling supports it.
- Prefer explicit return types at exported or otherwise meaningful boundaries when they clarify the contract; let local implementation details infer naturally.

## Export Only What Is Needed

- Keep every declaration module-private by default. Add `export` only when another file actually imports it today.
- Do not export helpers, types, constants, or schemas "just in case," for symmetry, or so tests can reach them. An unused export hides what callers depend on and makes the API harder to refactor.
- Test through the module's existing exported surface rather than exporting internals for the test's convenience.
- Before exporting, or when refactoring, search for importers. Remove `export` from anything no other file uses, and delete anything with no users.
- Keep a package's public entry point (`index.ts`, `exports` in `package.json`) limited to what external consumers need; do not re-export entire modules with `export *`.

## Model Absence And Failure Deliberately

- Represent expected absence and failure in the type system instead of returning misleading placeholder values.
- Narrow optional values at the point their presence becomes required. Do not defer an unsafe assumption to a distant caller.
- Use discriminated unions for finite state or result domains when callers need to handle each case explicitly.

## Compile-Time Checks And Exhaustive Mapping

- Prefer enforcing invariants through types and compiler checks over runtime exceptions for omissions the compiler can detect. Do not use casts, non-null assertions, or a throwing catch-all to avoid implementing a complete mapping.
- For a closed union or discriminated union, handle every member explicitly in a `switch` and check that the remainder is `never`. A plain `default: throw new Error(...)` does not enforce exhaustiveness; an existing `assertNever` helper must accept `never`, without assertions or `any` bypassing the check.
- For direct value mappings, use `SCREAMING_SNAKE_CASE` constant names and preserve literal keys and values with `as const`. When the map owns the domain, derive types from it instead of maintaining parallel unions. Do not add `satisfies` mechanically; prefer a direct type annotation when a value needs to conform to an existing contract. A const assertion preserves literal information; do not use type assertions to bypass validation.
- If both conversion directions are required, derive the reverse map's type from the forward constant using a mapped type with key remapping, then annotate the reverse constant with that type so missing keys and mismatched pairs fail typechecking. A true inverse requires unique forward values; represent many-to-one mappings deliberately instead of arbitrarily choosing a reverse value.
- When domain types exist independently, such as generated API enums, retain completeness checks against those types through exhaustive switches or explicitly typed coverage checks. A map inferred in isolation cannot detect new upstream members; checking its reverse alone does not prove coverage of an independent domain.
- Keep runtime validation at external boundaries: TypeScript types are erased, so a compile-time exhaustive check does not validate JSON, JavaScript callers, or other unknown data.

Example where the forward map is the source of truth:

```typescript
const PUBLIC_CURRENCY_BY_GENERATED = {
  eur: "EUR",
  usd: "USD",
} as const;

type PublicCurrencyByGenerated = typeof PUBLIC_CURRENCY_BY_GENERATED;
type GeneratedCurrencyByPublic = {
  [Key in keyof PublicCurrencyByGenerated as PublicCurrencyByGenerated[Key]]: Key;
};

const GENERATED_CURRENCY_BY_PUBLIC: GeneratedCurrencyByPublic = {
  EUR: "eur",
  USD: "usd",
};
```

The derived type requires `EUR: "eur"` and `USD: "usd"`; swapping those values or omitting a key fails typechecking. Adding a new pair to the forward map requires updating the reverse map. Run the project's typecheck command; transpilation alone may not check exhaustiveness.

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
