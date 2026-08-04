# React Testing Library Best Practices

Follow these rules when writing or reviewing tests that use `@testing-library/react`. Rules are ordered by importance (high > medium > low).

## Query Priority (high)

Use queries in this order of preference:

1. `*ByRole` — primary choice for almost everything
2. `*ByLabelText` — form fields
3. `*ByPlaceholderText` — when label is unavailable
4. `*ByText` — non-interactive elements
5. `*ByDisplayValue` — filled-in form elements
6. `*ByAltText` — images
7. `*ByTitle` — rare cases
8. `*ByTestId` — last resort only

### Prefer `*ByRole` with `name` option

```tsx
// bad
screen.getByTestId('submit-button')

// good
screen.getByRole('button', { name: /submit/i })
```

The `name` option matches the element's accessible name and works even when text is split across child elements:

```tsx
// <button><span>Hello</span> <span>World</span></button>

screen.getByText(/hello world/i)        // fails (text split across elements)
screen.getByRole('button', { name: /hello world/i })  // works
```

### Never use `container.querySelector`

```tsx
// bad
const { container } = render(<Example />)
container.querySelector('.btn-primary')

// good
screen.getByRole('button', { name: /click me/i })
```

### Query by visible text, not test IDs

Querying by text catches translation issues and keeps tests closer to user experience.

## Always Use `screen` (medium)

```tsx
// bad
const { getByRole } = render(<Example />)
getByRole('alert')

// good
render(<Example />)
screen.getByRole('alert')
```

Use `screen.debug()` for debugging output.

## Query Variant Rules (high)

| Variant | Use for |
|---------|---------|
| `get*` | Element is in the DOM right now |
| `find*` | Element will appear asynchronously |
| `query*` | Asserting element does **not** exist |

```tsx
// bad — query* for existence check gives poor error messages
expect(screen.queryByRole('alert')).toBeInTheDocument()

// good
expect(screen.getByRole('alert')).toBeInTheDocument()
expect(screen.queryByRole('alert')).not.toBeInTheDocument()
```

### Use `find*` instead of `waitFor` + `get*`

```tsx
// bad
const button = await waitFor(() =>
  screen.getByRole('button', { name: /submit/i }),
)

// good
const button = await screen.findByRole('button', { name: /submit/i })
```

## Use `userEvent` Over `fireEvent` (medium)

`@testing-library/user-event` fires realistic event sequences (keyDown, keyPress, keyUp, etc.).

```tsx
// bad
fireEvent.change(input, { target: { value: 'hello world' } })

// good
await userEvent.type(input, 'hello world')
```

Use `fireEvent` only when `userEvent` doesn't support the specific interaction.

## `waitFor` Rules (high)

### Always assert inside `waitFor`

```tsx
// bad — empty callback is fragile
await waitFor(() => {})
expect(window.fetch).toHaveBeenCalledWith('foo')

// good
await waitFor(() => expect(window.fetch).toHaveBeenCalledWith('foo'))
```

### One assertion per `waitFor` callback

```tsx
// bad — slow failure when first assertion passes but second fails
await waitFor(() => {
  expect(window.fetch).toHaveBeenCalledWith('foo')
  expect(window.fetch).toHaveBeenCalledTimes(1)
})

// good
await waitFor(() => expect(window.fetch).toHaveBeenCalledWith('foo'))
expect(window.fetch).toHaveBeenCalledTimes(1)
```

### No side-effects inside `waitFor`

The callback may run multiple times. Keep actions outside, assertions inside.

```tsx
// bad — fireEvent runs on every retry
await waitFor(() => {
  fireEvent.keyDown(input, { key: 'ArrowDown' })
  expect(screen.getAllByRole('listitem')).toHaveLength(3)
})

// good
fireEvent.keyDown(input, { key: 'ArrowDown' })
await waitFor(() => {
  expect(screen.getAllByRole('listitem')).toHaveLength(3)
})
```

## Don't Wrap in `act` Unnecessarily (medium)

`render` and `fireEvent` are already wrapped in `act`. Extra wrapping does nothing.

```tsx
// bad
act(() => {
  render(<Example />)
})

// good
render(<Example />)
```

If you see `act(...)` warnings, investigate the root cause rather than wrapping in `act`.

## Use `jest-dom` Assertions (high)

Prefer `jest-dom` matchers for better error messages.

```tsx
// bad
expect(button.disabled).toBe(true)

// good
expect(button).toBeDisabled()
```

## Don't Call `cleanup` (medium)

Cleanup is automatic in modern testing frameworks. Don't import or call it.

## Accessibility Attributes (high)

Don't add unnecessary ARIA roles or attributes. Use semantic HTML instead.

```tsx
// bad — button already has implicit role="button"
render(<button role="button">Click me</button>)

// good
render(<button>Click me</button>)
```

For inputs, set the `type` attribute to get the correct implicit role.

## Naming Conventions (low)

Don't name the render return value `wrapper`. Destructure what you need or call it `view`.

```tsx
// bad
const wrapper = render(<Example prop="1" />)

// good
const { rerender } = render(<Example prop="1" />)
```

## Make Existence Assertions Explicit (low)

```tsx
// works but unclear intent
screen.getByRole('alert', { name: /error/i })

// better — communicates intent to readers
expect(screen.getByRole('alert', { name: /error/i })).toBeInTheDocument()
```

## Quick Reference

| Rule | Importance |
|------|-----------|
| Use `*ByRole` as default query | high |
| Use correct query variant (get/find/query) | high |
| Assert inside `waitFor`, one assertion only | high |
| No side-effects in `waitFor` | high |
| Use `jest-dom` matchers | high |
| Don't add unnecessary ARIA attributes | high |
| Query by visible text, not test IDs | high |
| Use `screen` for queries | medium |
| Use `userEvent` over `fireEvent` | medium |
| Don't wrap in `act` unnecessarily | medium |
| Don't call `cleanup` | medium |
| Destructure render, don't use `wrapper` | low |
| Make `getBy*` assertions explicit | low |
