## Git workflow

Make code and documentation changes on feature branches and open pull requests targeting `main`. Never push commits directly to `main`.

## File organization

Prefer more small, focused files over files containing independent components. Name each file for the component it defines, and use directories to group collections, such as `use_cases/create_run.py` and `use_cases/read_runs.py`.

Keep a component's private helpers in its file. Give shared helpers their own named modules. Framework entry files such as `__init__.py` and `conftest.py` may expose or register multiple components; keep their component definitions in separate files. Test files mirror the component they check and may contain multiple tests for it.

## Agent skills

### Issue tracker

For planning maps, tickets, or issue updates, read `docs/agents/issue-tracker.md`. Work is tracked in GitHub Issues using `gh`.

### Triage labels

Before triaging or applying a triage role, read `docs/agents/triage-labels.md` for the label mapping.

### Domain docs

Before domain exploration or design, read `docs/agents/domain.md`. This project uses a single domain context.
