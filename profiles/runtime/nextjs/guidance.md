# Next.js (App Router)

## TypeScript

- Enable `strict` in `tsconfig.json`. Do not weaken compiler options to fix errors.
- Avoid `any`. Use `unknown` plus narrowing for untrusted data, and validate external data (API responses, form input, URL params) with a runtime schema at the boundary.
- Export explicit prop types for shared components. Prefer discriminated unions over boolean flag combinations.
- Use path aliases from `tsconfig.json` rather than deep relative imports.

## Architecture

- Organize routes under `app/` by URL segment. Keep route files (`page.tsx`, `layout.tsx`, `route.ts`) thin: they compose components and call data functions.
- Put domain logic and data access in framework-independent modules (for example `lib/` or `server/`) that can be unit-tested without rendering.
- Colocate a component with its route only when no other route uses it; promote it to a shared folder when reused.
- Use `loading.tsx` and `error.tsx` boundaries for each route segment that fetches data.

## Server and client boundaries

- Components are Server Components by default. Add `"use client"` only to the smallest component that needs state, effects, event handlers, or browser APIs.
- Pass only serializable props from server to client components. Never pass secrets or full database records.
- Mark modules that must never run in the browser with the `server-only` package import. Read secrets only in server code; only `NEXT_PUBLIC_` variables reach the client, so never put secrets in them.
- Perform mutations through Server Actions or route handlers that validate input and check authorization on the server, every time.
- Be explicit about caching and revalidation for each data fetch; do not rely on defaults you have not checked for the installed version.

## Components

- One component per file for exported components; keep files small and focused.
- Separate presentational components (props in, markup out) from data-loading components.
- Use semantic HTML and accessible names. Every interactive element is keyboard-reachable and labelled.
- Style with the approach the project already uses; do not add a second styling system.

## Testing

- Unit-test pure logic in `lib/` with the project's test runner.
- Test client components with a DOM testing library, querying by role and accessible name, not by class or test id when avoidable.
- Test route handlers and Server Actions as functions with mocked I/O boundaries.
- Keep a small end-to-end suite (a browser automation tool) for critical user journeys: sign-in, primary create/read flows, checkout-style paths.
