# Contributing

## Start with the task

Read the issue or task and agree on scope before coding. Use `gh` for GitHub issues and pull requests.

Before changing core, API, or adapters, read the README's [Architecture](README.md#architecture) and [Public core interface](README.md#public-core-interface). For domain changes, also read [CONTEXT.md](CONTEXT.md) and relevant ADRs if present.

Work on feature branches and open pull requests targeting `main`. Never push directly to `main`.

## Set up

Use uv with the Python version selected by `.python-version`. Montreal scheduling requires an IANA timezone database for Python's `zoneinfo`. From the repository root:

```sh
uv sync --locked --all-packages
```

The full test suite includes Chromium browser checks. Install the matching browser after syncing and after Playwright updates:

```sh
uv run playwright install chromium
```

The browser download is separate from `uv.lock`. Browser tests start Uvicorn against temporary SQLite files and use public page interactions and HTTP requests.

## Write the change

Keep changes focused on current requirements. Reuse existing code and the standard library before adding dependencies or abstractions. Refactors preserve public interfaces and observable behavior unless the task asks to change them.

Use small files named for one component and directories for collections, such as `use_cases/create_run.py` and `use_cases/read_runs.py`.

Keep private helpers and closely related supporting types with their component. Shared helpers get their own named modules. `__init__.py` and `conftest.py` may expose or register multiple components, with definitions kept in their own files. Test files mirror the component they check.

Main functions describe the workflow through named steps. Give each helper a clear responsibility and a name that describes its work. Public entry functions use Google style docstrings covering inputs, outputs, and expected errors.

### Tests

Every test case must protect a named use case, edge case, or regression. Before adding one, check whether existing assertions already protect that behavior. Reuse an existing scenario when it can check the behavior clearly. Add a separate case when it protects something distinct.

Write `pytest` tests as functions, using fixtures and parametrization when helpful. Test through agreed public interfaces; agree new test seams with the maintainer before adding tests there. Use test-first development for new behavior. Assert returned values, errors, and saved behavior through those interfaces.

For core tests, use a small in-memory storage fake for normal stateful behavior and mocks at the storage port for failures. Keep private collaborators and call sequences out of assertions. Verify real adapters at their agreed integration seams.

Prefer representative cases for each rule over exhaustive input lists. Combine parameter dimensions only when their interaction changes behavior. Avoid tests that merely repeat the implementation or check library internals.

Before finishing a change, review added and modified tests for usefulness and overlap. Keep distinct contract and edge cases even when they execute the same branch. When trimming tests, compare line and branch coverage and check that the remaining assertions still catch the relevant failures. Coverage and test counts alone do not show whether tests are useful.

## Check the change

Run affected test files and ty during implementation. Before finishing a code change, run:

```sh
uv run pytest
uv run ty check
uv run ruff check .
uv run ruff format --check .
```

Use `uv run ruff format .` to format changes. To inspect core coverage:

```sh
uv run pytest --cov=aweille.core --cov-branch --cov-report=term-missing
```

For documentation changes, check the diff with `git diff --check` and verify links and examples.

## Name branches and commits

Use `<type>/<short-kebab-case-description>` for branches, such as `feat/planned-run-core` or `docs/contributing-guide`. Branch prefixes use the same types as commits.

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for commit messages and PR titles:

```text
<type>(<optional-scope>): <short description>
```

Omit the parentheses when there is no scope. Use a concise scope when it clarifies the part of the codebase. Descriptions are lowercase, action-oriented, and have no trailing period.

Common types:

| Type | Use |
| --- | --- |
| `feat` | Add a capability. |
| `fix` | Correct a bug. |
| `refactor` | Restructure code without changing behavior. |
| `perf` | Improve performance. |
| `test` | Add or change tests. |
| `docs` | Change documentation. |
| `ci` | Change CI configuration. |
| `build` | Change the build system or dependencies. |
| `chore` | Routine maintenance. |
| `style` | Formatting changes. |

For example:

```text
feat(core): add planned-run creation
docs: add contribution guide
```

Add a body after a blank line when the reason or trade-off needs explaining. Use footers such as `Refs: #5` for references when useful. Mark breaking changes with `!` before the colon or a `BREAKING CHANGE:` footer, and explain what consumers must change.

## Open and merge a pull request

Keep the PR focused on one change. Explain the problem and resulting behavior, link relevant issues, and report the checks run. Put issue-closing references in the PR body when it completes an issue.

Address review comments and rerun checks affected by revisions. Squash merge using the PR title as the commit message so `main` gets one Conventional Commit per PR.
