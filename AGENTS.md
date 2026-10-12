## Git workflow

Make code and documentation changes on feature branches and open pull requests targeting `main`. Never push commits directly to `main`.

## File organization

Prefer more small, focused files over files containing independent components. Name each file for the component it defines, and use directories to group collections, such as `use_cases/create_run.py` and `use_cases/read_runs.py`.

Keep a component's private helpers in its file. Give shared helpers their own named modules. Framework entry files such as `__init__.py` and `conftest.py` may expose or register multiple components; keep their component definitions in separate files. Test files mirror the component they check and may contain multiple tests for it.

## Function structure

Main functions describe the workflow through named steps. Put each step's implementation in a focused helper with a single clear responsibility, and name it for the work it performs.

## Implementation

Before changing core or adapters, read the root README's Architecture and Public core interface sections for dependency direction, typed inputs, exact numeric values, validation ownership, and error contracts.

Keep changes focused on current requirements. Reuse existing code and the standard library before adding dependencies or abstractions. During refactors, preserve public interfaces and observable behavior unless the requested change includes changing them.

## Tests

Write pytest tests as functions. Use fixtures and parametrization when they make the checks clearer.

Test through the agreed public interfaces. Confirm a new test seam with the user before adding tests there; reuse already agreed seams. Use test-first development for new behavior at those seams. Assert returned values, errors, and saved behavior through those interfaces.

For core tests, use a small in-memory storage fake for normal stateful behavior and mocks at the storage port for failure cases. Keep private collaborators and their call sequences out of assertions. Real adapter verification belongs at its agreed integration seam.

Choose cases for distinct contract behavior and useful edge cases. When trimming tests, compare line and branch coverage and check that the remaining assertions still protect those behaviors. Coverage and case count support that judgment.

## Tooling and verification

Use uv for project commands, ty for typechecking, and Ruff for formatting and linting. The root README's Development section is the command reference.

For code changes, run focused tests and typechecking during implementation. Finish with the full test suite, typechecking, Ruff linting, and a formatting check. Run checks that are relevant to documentation-only changes.

## Agent skills

### Issue tracker

For planning maps, tickets, or issue updates, read `docs/agents/issue-tracker.md`. Work is tracked in GitHub Issues using `gh`.

### Triage labels

Before triaging or applying a triage role, read `docs/agents/triage-labels.md` for the label mapping.

### Domain docs

Before domain exploration or design, read `docs/agents/domain.md`. This project uses a single domain context.
