---
name: java-best-practices
description: Write, edit, or refactor Java source with immutable data, pure transformations, explicit optional values, closed state or result hierarchies, and exhaustive case handling.
---

# Java Best Practices

Follow the repository's established Java style first. Use these rules where the local codebase has no stronger convention.

## Prefer Immutable Data And Pure Transformations

- Prefer immutable data and functions that return results rather than modifying arguments, instance fields, captured state, or static shared state. Keep I/O and intentional state changes in operations with an explicit owner and contract.
- Use records where supported and suitable, and `final` bindings where they clarify ownership. Neither records nor `final` make referenced objects deeply immutable; protect mutable components and do not modify nested caller-owned data.
- Prefer unmodifiable collection snapshots when ownership requires them, using APIs supported by the project's Java release. An unmodifiable view can still reflect changes to its backing collection, and shallow copies still share mutable elements.
- Local mutation of newly created, unshared values is acceptable when clearer or more efficient. Do not replace straightforward loops with streams solely for style, or mutate external state from stream callbacks.

## Collection Performance

- Prefer a single stream pipeline such as `items.stream().filter(predicate).map(mapper).toList()` over collecting filtered items and starting another traversal solely to map them, using terminal APIs supported by the project's Java release. Stateless intermediate stages are lazy and can be fused into one traversal; stateful stages such as `sorted` can require buffering.
- Keep stream callbacks pure and non-interfering. A straightforward loop with a locally owned result is also appropriate; streams are not inherently faster, and parallel streams need workload evidence rather than being a default optimization.

## Sealed Types And Exhaustive Handling

- Prefer compile-time guarantees over runtime exceptions for missing cases. Use an `enum` for a fixed set of simple values, and a `sealed interface` or abstract `sealed class` with explicit permitted subtypes for a closed domain whose variants carry different data or behavior.
- Keep leaf variants `final` (records are implicitly final), or continue sealing intermediate types. Use `non-sealed` only when an open extension point is intentional; it does not describe a finite set of leaf variants.
- Handle closed domains with exhaustive `switch` expressions that name every enum constant or permitted variant. Avoid `default`, catch-all supertype patterns, or final throwing branches that hide missing cases. Adding a variant should require updating consumers during compilation.
- Respect the project's configured Java release: sealed types are standard in Java 17; pattern matching for `switch` is standard in Java 21. Do not enable preview features or upgrade Java merely to apply this preference. On older targets, use supported enums, typed construction, or established visitor patterns where they provide the needed guarantee.
- Keep runtime validation for external data and represent expected failures explicitly. Sealing a hierarchy does not validate input or eliminate nullability; recompile affected consumers when the hierarchy changes so exhaustiveness is checked again.

Example for Java 21 or later:

```java
sealed interface ImportResult permits Imported, Rejected {}

record Imported(String profileName) implements ImportResult {}
record Rejected(String reason) implements ImportResult {}

final class ImportResultFormatter {
    static String message(ImportResult result) {
        return switch (result) {
            case Imported imported -> "Imported " + imported.profileName();
            case Rejected rejected -> "Import rejected: " + rejected.reason();
        };
    }
}
```

Adding another permitted variant makes this switch non-exhaustive when recompiled, rather than relying on an explicit runtime exception for an omitted case.

## Optional Values

- Represent an absent value with `Optional<T>`; do not assign raw `null` to a value.
- Use `Optional.empty()` when the value is absent and `Optional.of(value)` when it is known to be present.

Prefer:

```java
Optional<String> optionalConfig = Optional.empty();
```

Avoid:

```java
String optionalConfig = null;
```
