# Swift Documentation Comments

Use Swift's `///` documentation markup for every public declaration: methods,
initializers, computed and stored properties, classes, structs, actors,
enums, and protocols. Skip `private`, `fileprivate`, and other non-public
declarations unless their behavior is genuinely non-obvious.

## Understand Before Documenting

Never write a documentation comment straight from a declaration's signature
or name. Read the implementation body first, then trace how it is actually
used:

- Read the full function, initializer, or property body, including any
  private helpers it calls, so the summary describes real behavior rather
  than a guess based on the name.
- Find where the declaration is called or referenced across the codebase
  (call sites, tests, previews) to confirm the parameters, return value, and
  thrown errors mean what they appear to mean, and to write an example that
  reflects a real usage rather than an invented one.
- For a type, check where it originates: is it constructed directly, decoded
  from data, produced by a factory, or injected? Document the type's role and
  intended construction path as it exists, not as it might be assumed.
- If behavior is ambiguous after reading the implementation and its call
  sites, say so rather than documenting a guess as fact.

Only write the comment once the behavior, return value, error cases, and a
realistic call site are confirmed from the code itself.

## Required Content

Every documentation comment must cover:

1. **What it does** — a concise summary line describing the behavior, not a
   restatement of the name.
2. **What it produces** — for methods and computed properties, describe the
   return value and any thrown errors. For types, describe what the type
   represents and when to use it.
3. **An example** — a realistic usage snippet under an `- Example:` callout
   showing how to call it and what to expect back.

Use the standard callouts (`- Parameters:`, `- Returns:`, `- Throws:`) so
Xcode's Quick Help renders them correctly.

## Methods And Initializers

```swift
/// Converts a raw profile payload into a validated `Profile`, trimming
/// whitespace from the display name and rejecting unusable images.
///
/// - Parameters:
///   - image: The image data selected by the person during import.
///   - name: The raw display name as entered in the import form.
/// - Returns: A `Profile` ready to persist.
/// - Throws: `ProfileImportError.missingName` when `name` is empty after
///   trimming, or `ProfileImportError.invalidImage` when `image` cannot be
///   decoded.
///
/// - Example:
///   ```swift
///   let profile = try importProfile(from: selectedImageData, name: "Ada Lovelace")
///   print(profile.displayName) // "Ada Lovelace"
///   ```
func importProfile(from image: Data, name: String) throws -> Profile {
    // ...
}
```

## Properties

```swift
/// The person's full display name, combining given and family name with a
/// single space.
///
/// - Example:
///   ```swift
///   let profile = Profile(givenName: "Ada", familyName: "Lovelace")
///   profile.displayName // "Ada Lovelace"
///   ```
var displayName: String {
    "\(givenName) \(familyName)"
}
```

## Types

```swift
/// Represents a validated person profile ready for persistence or display.
///
/// Construct a `Profile` through `importProfile(from:name:)` rather than
/// the memberwise initializer when the data originates from user input, so
/// validation runs before a value exists.
///
/// - Example:
///   ```swift
///   let profile = Profile(givenName: "Ada", familyName: "Lovelace")
///   ```
struct Profile {
    let givenName: String
    let familyName: String
}
```

## Style Notes

- Keep the summary line to one sentence; add further detail in a blank-line-separated paragraph only when the summary alone would mislead a caller.
- Write examples that compile against the declaration's actual signature; do not invent parameters or return types that do not exist.
- Document thrown errors by case when the failure domain is small enough to enumerate; otherwise describe the conditions that trigger a failure.
- Update the documentation comment in the same change whenever the signature, behavior, or thrown errors change so it never drifts from the implementation.
