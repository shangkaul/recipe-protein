# Contributing to Protein Pantry

## Branch and pull-request workflow

`main` is the reviewed history of the project. Do not implement directly on it.

1. Start from the latest `main`.
2. Create a focused branch:
   - `feat/<short-name>` for product work
   - `fix/<short-name>` for defects
   - `docs/<short-name>` for documentation
   - `chore/<short-name>` for tooling or maintenance
3. Keep commits scoped and include tests with behavior changes.
4. Push iterative commits to the feature branch as each coherent unit becomes testable. This keeps
   progress visible and reviewable without exposing unfinished work on `main`.
5. Open a merge pull request from the feature branch into `main` that lists:
   - what changed and why;
   - specification tasks covered;
   - commands run and results;
   - screenshots for interface changes;
   - known limitations or follow-up work.
6. Wait for the project owner to approve the pull request before merging.
7. Prefer squash merge so `main` stays readable while GitHub retains the branch's iterative commit,
   review, and pull-request history.

## Quality gates

- Recipe and adaptation output must pass red-meat exclusions.
- Nutrition must be attributed or deterministically calculated.
- No pantry or dietary input may be sent to a cloud model.
- UI changes must be checked at mobile and desktop widths with keyboard-visible focus.
- Dataset additions must document license, attribution, schema quality, and known limitations.
