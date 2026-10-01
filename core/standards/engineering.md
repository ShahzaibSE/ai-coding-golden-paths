# Engineering Standards

These standards apply to every change, in every language and stack.

## Scope and size

- Solve the stated problem. Note unrelated issues instead of fixing them in the same change.
- Prefer several small, reviewable changes over one large one.
- Do not introduce a dependency, framework, or abstraction without a concrete present need.

## Code

- Match the conventions already present in the codebase: naming, layout, error style, comment density.
- Reuse existing utilities before writing new ones. Search before adding.
- Name things for what they mean in the domain, not for how they are implemented.
- Keep functions focused. A function that needs a paragraph to explain its branches should be split.
- Make invalid states unrepresentable where the language allows it (types, enums, validation at construction).
- Delete dead code rather than commenting it out; version control remembers it.

## Errors

- Fail loudly and early on programmer errors; handle expected failures explicitly.
- Never swallow an error silently. Either handle it meaningfully, or propagate it with added context.
- Error messages state what failed, with which input, and what the caller can do about it.

## Configuration

- Configuration that differs between environments comes from environment variables or config files, never from code.
- No hardcoded hostnames, credentials, machine paths, or personal preferences in shared code.
- Provide safe defaults and document every required setting in docs/engineering/PROJECT.md.

## Documentation

- Comments explain why, not what. Update or delete comments that the change makes wrong.
- Public interfaces (modules, APIs, CLIs) document their contract: inputs, outputs, errors.
- When a change alters architecture, commands, or setup, update docs/engineering/PROJECT.md in the same change.

## Honesty in reporting

- State exactly what was run and verified. "Tests pass" means the tests were executed and passed.
- If something was skipped, could not be verified, or is a known limitation, say so explicitly.
