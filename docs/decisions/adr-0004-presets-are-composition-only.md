# ADR-0004: Presets Are Composition Only

## Status

Accepted

## Context

Presets such as `fastapi-rag` are convenient names for common stacks. It is tempting to put stack-specific guidance in them (for example FastAPI conventions), but that would make presets a second source of guidance, parallel to profiles, and the same advice would then exist in two places.

## Decision

A preset file may contain only `name`, `description`, and `profiles`. Validation rejects any other key. Guidance that seems to "belong to a preset" becomes a profile instead. FastAPI guidance therefore lives in `runtime/fastapi`, which requires `runtime/python-backend`. See [Profile contract](../profile-contract.md#presets).

## Consequences

- Choosing a preset gives exactly the same result as selecting its profiles explicitly (tested).
- All guidance stays in profiles, where duplication checks and composition tests apply.
- Some small profiles exist mainly to serve one preset, which slightly increases the profile count.

## Alternatives Considered

- **Preset overlay files with extra guidance:** fewer profiles, but a second content source with no duplication or conflict checks.
- **No FastAPI content at all:** simplest, but the preset name would promise more than it delivers.

## Date

2026-10-01
