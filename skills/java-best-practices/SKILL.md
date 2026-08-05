---
name: java-best-practices
description: Use when writing, editing, or refactoring Java source that represents absent or nullable values.
---

# Java Best Practices

Follow the repository's established Java style first. Use this rule where the local codebase has no stronger convention.

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
