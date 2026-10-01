# Agent Evaluation Workflow

Use before merging changes to an agent's prompts, tool set, tool descriptions, orchestration, limits, or model.

## Scenario set

- Maintain versioned scenarios in the repository. Each has: the task input, the available tools (with fake or sandboxed implementations), and pass criteria.
- Cover: typical tasks, tasks requiring several tools, tasks that should end in a human checkpoint, tasks that are impossible or out of scope, malformed or failing tool responses, and prompt-injection attempts inside tool output.
- Add a scenario for every production failure (with personal data removed).

## Criteria

Judge outcomes and process, not exact wording:
- Task success: the end state matches the expected state.
- Safety: no disallowed tool call, no irreversible action without a checkpoint, no leaked credentials or personal data.
- Efficiency: steps, tool calls, latency, and cost within budget.
- Correct stopping: limits respected, impossible tasks end with a clear explanation, no loops.

Prefer checks computed in code over model-graded judgments. When a model grades, spot-check its judgments by hand.

## Procedure

1. Run the scenarios on the main branch to get a baseline. Agents are non-deterministic: run each scenario several times and record pass rates.
2. Apply the change and rerun with identical settings.
3. Compare pass rates per scenario and in aggregate, and read the traces of every regressed scenario.
4. Report baseline vs. change, regressions with trace excerpts, and a merge recommendation in the pull request.

Any regression in safety criteria blocks the merge until a human explicitly accepts it.
