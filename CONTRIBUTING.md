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
4. Open a pull request that lists:
   - what changed and why;
   - specification tasks covered;
   - commands run and results;
   - screenshots for interface changes;
   - known limitations or follow-up work.
5. Wait for the project owner to approve the pull request before merging.
6. Prefer squash merge so `main` stays readable while GitHub retains review history.

## Quality gates

- Recipe and adaptation output must pass red-meat exclusions.
- Nutrition must be attributed or deterministically calculated.
- No pantry or dietary input may be sent to a cloud model.
- UI changes must be checked at mobile and desktop widths with keyboard-visible focus.
- Dataset additions must document license, attribution, schema quality, and known limitations.
