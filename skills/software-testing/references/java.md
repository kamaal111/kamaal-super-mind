# Java Testing

## Assertion Messages

When writing or updating JUnit assertions, include a descriptive assertion message that states the behavior or invariant under test. The message should tell the reader which scenario broke without requiring them to reconstruct the test.

```java
assertNotEquals(
    createdVersion.getContent(),
    latestAfterVersionCreate.getContent(),
    "Creating a new form version should change the latest form content.");
```

Do not restate the assertion mechanics, for example: `"Expected values to be different."`
