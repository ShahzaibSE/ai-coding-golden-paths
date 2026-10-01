# Agentic AI

Guidance for systems where a model plans and calls tools in a loop. Independent of any agent SDK or model provider; record those choices in docs/engineering/PROJECT.md.

## Tool boundaries

- Each tool does one thing, has a precise name and description, and a typed input schema validated in code before execution.
- Tools return structured results and structured errors the model can act on (what failed, whether retrying can help).
- Tools enforce authorization themselves, using the identity of the end user or service on whose behalf the agent acts. The model's request is never the authority.
- Credentials live in the tool implementation, never in prompts, model-visible context, or tool arguments.
- Classify every tool as read-only, reversible write, or irreversible/external. The classification drives checkpoints and retries.
- Tool output is untrusted input to the model. Content from the web, documents, or users can carry injected instructions; it must never grant new permissions.

## Orchestration

- Prefer the simplest structure that works: a single call, then a fixed pipeline, then a single agent loop, and only then multiple agents. Justify each step up with an evaluation result.
- Keep orchestration logic (loop control, routing, limits) in ordinary, testable code, separate from prompts.
- Every loop has hard limits: maximum steps, wall-clock time, and token or cost budget. Reaching a limit is a handled outcome, not a crash.
- Define the stop condition explicitly (task complete, needs human, cannot proceed) and make the final state machine-readable.
- When delegating to sub-agents, pass a self-contained task with explicit inputs and expected output shape; do not rely on shared implicit context.

## State

- Make agent state explicit and serializable: goal, step history, tool calls and results, intermediate artifacts.
- Persist state at step boundaries for long-running tasks so they can resume after failure without repeating side effects.
- Bound the context the model sees: summarize or drop old steps deliberately, and keep the raw history in storage for audit.
- Make side-effecting tools idempotent (idempotency keys) so a resumed or retried step does not act twice.

## Failure handling

- Distinguish failure classes: invalid tool arguments (return the validation error to the model), transient tool failure (retry with backoff, if the tool is safe to retry), permanent failure (stop or escalate), and model output that cannot be parsed (bounded re-ask, then fail).
- Detect loops: repeated identical tool calls or no progress across several steps ends the run with an explanation.
- Fail closed: when unsure whether an action is allowed, do not take it and escalate.

## Human checkpoints

- Require human approval before irreversible or externally visible actions (payments, sending messages, deleting data, deploying, changing permissions) unless a documented policy pre-approves them.
- Present the approver with the proposed action, its arguments, the reason, and the expected effect. Record the decision.
- Support pause and resume around checkpoints without losing state.

## Observability

- Trace every run: inputs, each model call (prompt version, model identifier), each tool call with arguments and results, timing, token usage, and final outcome. Apply the privacy baseline to traces.
- Version prompts and tool descriptions alongside code; changes to them are behavior changes.

## Testing

- Unit-test tools, validation, limits, routing, and state transitions deterministically with a scripted fake model.
- Behavior with a real model is measured with the agent-evaluation workflow.
