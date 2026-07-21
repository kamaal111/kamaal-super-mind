---
name: swift-best-practices
description: Write, edit, or refactor clear and resilient Swift source. Use when implementing Swift application, library, model, service, client, error-handling, logging, or shared-utility code.
---

# Swift Best Practices

Follow the repository's established Swift style first. Use these rules where the local codebase has no stronger convention.

## Guard Statements

- Prefer one independent condition per `guard`. Separate guards make exit points easier to read, debug, and breakpoint.
- Keep a guard header on one line when it fits the configured line width. If one condition is long, wrap only that condition while keeping it independent.
- Keep the failure path close to the condition it protects.

Prefer:

```swift
guard let session else { return .missingSession }

guard session.isActive else { return .inactiveSession }
```

Avoid merging unrelated checks solely to make the code shorter:

```swift
guard let session, session.isActive else { return .invalidSession }
```

## Invariants And Optionals

- When a value must exist for the application to function correctly, surface an impossible `nil` or invalid state at the first visible point rather than hiding it behind a permissive `guard`, `??`, or placeholder default.
- Use `preconditionFailure`, `assertionFailure`, `fatalError`, or a force unwrap only for genuine invariants; use intentional optional handling for real recovery paths that improve the user experience.
- Do not invent fallback configuration or placeholder data simply to keep execution moving when it leaves the application in an unknown or misleading state.

Prefer:

```swift
guard let modelContext else { preconditionFailure("A model context must be configured before use.") }
```

Avoid silently returning from a required configuration failure:

```swift
guard let modelContext else { return }
```

## Pure Utilities And Dependency Injection

- Do not declare free functions at file scope, including `private` ones. Namespace static helpers inside a holder `struct` or `enum`; make the holder `private` too when it is only needed by that file.
- Use a holder `enum` when the type exists solely as a namespace and should never be instantiated. Use a holder `struct` when that better communicates the utility's role or it may later construct related state. Keep its namespace helpers `static`.
- Keep pure utilities stateless and direct. Namespace-style types with `static` functions are often clearer than injected objects with no lifecycle or replaceable behavior.
- Do not add protocols, stored properties, or initializer parameters merely to mock pure transformations. Test pure utility behavior directly.
- Reserve dependency injection for side effects, external I/O, environment access, mutable state, or behavior that genuinely varies by implementation.

Prefer:

```swift
private enum ProfileNameFormatter {
    static func normalized(_ name: String) -> String {
        name.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
```

Avoid a file-private free function:

```swift
private func normalizedProfileName(_ name: String) -> String {
    name.trimmingCharacters(in: .whitespacesAndNewlines)
}
```

## Type Extensions

- Do not create an extension for a type defined in the project. Add its functions and computed properties to the type's primary declaration so related behavior has one obvious home and is less likely to be duplicated.
- Before extending a type from an external dependency or a system framework, search the project for an existing extension that provides the needed behavior. Create a new extension only when none exists.
- Keep a permitted external-type extension close to its established owner. If more than one feature needs the same extension logic, move it to one central shared extension and reuse it rather than recreating it locally.

Prefer keeping project-owned behavior with its type:

```swift
struct Profile {
    let givenName: String
    let familyName: String

    var displayName: String {
        "\\(givenName) \\(familyName)"
    }
}
```

Avoid splitting a project-owned type from its behavior:

```swift
extension Profile {
    var displayName: String {
        "\\(givenName) \\(familyName)"
    }
}
```

## Shared Ownership

- Search for an existing owner before adding non-trivial logic. Extend or move shared behavior to the lowest suitable service, model, utility, module, or package.
- Do not copy a helper into a second target merely to make it reachable from another caller.
- When moving shared code, remove the old implementation unless it intentionally differs. Make any remaining difference explicit through naming, structure, or tests.

## Public Error APIs

- Follow local API conventions. When a non-private operation has a meaningful failure domain, prefer an explicit typed failure that callers can handle deliberately.
- Keep the error domain narrow and concrete. If an error reaches people, provide a user-presentable localized description.
- Private helpers may throw when that keeps implementation straightforward; translate private failures before crossing a public typed-result boundary.

Example:

```swift
enum ProfileImportError: LocalizedError, Equatable {
    case missingName
    case invalidImage

    var errorDescription: String? {
        switch self {
        case .missingName:
            String(localized: "The profile name could not be found.")
        case .invalidImage:
            String(localized: "The selected image could not be processed.")
        }
    }
}

func importProfile(from image: UIImage) async -> Result<Profile, ProfileImportError> {
    // Perform the import and map failures deliberately.
}
```

## Logging

- Treat logging as an observable product concern at user-facing workflows and important persistence or network boundaries.
- Record meaningful start, success, and failure events as complete, human-readable messages. Include safe context that identifies the operation stage and error.
- Use the repository's shared logger rather than `print` or ad hoc console output. Do not log passwords, credentials, tokens, cookies, or raw sensitive payloads.
- Ensure recoverable failures remain recoverable when logged; logging must not turn expected error handling into a crash.

## Working Style

- Match nearby naming, formatting, file structure, and concurrency patterns.
- Centralize repeated string literals in a suitable enum, constant, or other shared definition when that improves consistency.
- Add new project-specific rules only after the team agrees on them, so the guidance remains precise and trustworthy.
