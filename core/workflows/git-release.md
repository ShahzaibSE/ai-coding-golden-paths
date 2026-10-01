# Git Release Workflow

Use only when asked to commit a change and push it to the shared remote. The flow is review, validate, stage, commit, push, report.

## Procedure

1. Inspect the branch and its configured upstream remote (`git remote -v`, `git rev-parse --abbrev-ref @{upstream}`). If there is no upstream, stop and ask where to push.
2. Review the changes (follow the git-review workflow). Stop and ask if the state is ambiguous or the changes are not one logical unit.
3. Check the branch against the project's branch policy in `standards/git-workflow.md`. If the repository follows a branch and pull request workflow, do not release from the default branch. If the policy is unclear, ask first.
4. Validate: follow the run-tests workflow for the applicable tests, lint, and type checks. If anything fails, stop before committing.
5. Check the diff for secrets and machine-specific files.
6. Stage only the intended files by explicit path.
7. Create one atomic commit (follow the git-commit workflow for message format).
8. Push to the existing upstream with a plain `git push`. Do not add flags that rewrite remote history.
9. Report the branch, commit hash, remote, and the push result.

## Safety

- Never force-push, including `--force-with-lease`, unless the user explicitly asks for it by name.
- Never use `git reset --hard`, destructive `git clean`, or branch deletion.
- Never run a rebase or other history rewrite without explicit instruction.
- Never silently overwrite remote history. If the push is rejected, report it and stop; do not retry with different flags.
- Never skip hooks or checks to get a push through.
- Abort or ask whenever the repository state is ambiguous.

## Success and failure

- Success: validation passed, one commit was created, and the push was accepted by the upstream. The report states branch, hash, remote, and result.
- Failure: stop at the first failing step and report which step failed and what state the repository was left in (for example, "committed locally, not pushed").
