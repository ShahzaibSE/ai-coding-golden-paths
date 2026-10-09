# React + Vite (single-page application)

This profile covers a client-rendered React application bundled with Vite. It assumes everything runs in the browser and does not apply to server-rendered frameworks.

## TypeScript

- Enable `strict` in `tsconfig.json`. Do not weaken compiler options to clear an error.
- Avoid `any`. Use `unknown` plus narrowing for untrusted data, and parse it with a runtime schema where it enters the application (fixtures, URL parameters, stored values, form input).
- Export explicit prop types for shared components. Prefer discriminated unions over combinations of boolean flags.
- Use path aliases from `tsconfig.json` (mirrored in the Vite config) rather than deep relative imports.

## Structure

- Organize `src/` by feature. A feature folder owns its components, hooks, types, and tests.
- Keep route modules thin: they compose feature components and read URL parameters.
- Extract a component, hook, or helper into a shared folder only when a second feature needs it, or when the need is concrete and immediate.
- Keep pure domain logic (formatting, calculations, state transitions) in plain modules that can be tested without rendering.
- Keep generated or seeded sample data separate from UI code; UI modules import data, never the reverse.
- One exported component per file; keep files small and focused.

## State

- Start with local component state. Lift it only as far as the nearest common parent.
- Hold filter, sort, and pagination state in the URL when users should be able to share or reload it.
- Share state across features only when several of them genuinely read or write it. Model its changes as pure functions of the previous state and an action, so they can be unit-tested.
- Subscribers to shared state should read only the slice they render, so unrelated components do not rerender when it changes.
- Do not mirror props or other state into new state with an effect. Compute derived values during render, and memoize only after measuring a problem.
- Run side effects in event handlers where possible; reserve effects for synchronizing with something outside React, and clean them up.

## Components and accessibility

- Separate presentational components (props in, markup out) from components that read state.
- Use semantic elements first; add ARIA only where no native element fits. Every interactive control is keyboard-reachable and has an accessible name.
- Dialogs trap and restore focus. Announce asynchronous or simulated outcomes to assistive technology with a live region.
- Never convey status by color alone; pair it with text or an icon.
- Give lists and tables stable keys derived from record identity, not array index.

## Build and configuration

- Only variables prefixed for client exposure reach the browser bundle, so never place secrets in them.
- Load heavy, rarely used code (large charts, editors) lazily, behind a route or an interaction.
- Treat the Vite config as code that is reviewed: record any plugin or alias addition in `docs/engineering/PROJECT.md`.

## Testing

- Unit-test pure logic and state transitions with the project's test runner.
- Test components with a DOM testing library, querying by role and accessible name rather than by class or test id.
- Simulate user input with the user-event utilities, not by calling handlers directly.
- Include an automated accessibility check for key screens.
- Keep a small end-to-end suite for critical journeys, such as the primary create, update, and review flows.
