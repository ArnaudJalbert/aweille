# Issue tracker: GitHub

Track issues and specs in `ArnaudJalbert/aweille` on GitHub. Use the `gh` CLI. Infer the repository from the Git remote, or pass `--repo ArnaudJalbert/aweille` explicitly.

## Issue operations

- Create an issue with `gh issue create --title "..." --body-file <file>`.
- Read an issue with `gh issue view <number> --comments`.
- Query issues with `gh issue list` and the relevant state, label, and JSON fields.
- Add a comment with `gh issue comment <number> --body-file <file>`.
- Apply or remove labels with `gh issue edit <number> --add-label "..."` or `--remove-label "..."`.
- Close an issue with `gh issue close <number>`.

Use files for multiline bodies and comments. Refer to issues by their linked titles in prose.

## Pull requests as a triage surface

PRs as a request surface: no.

## Wayfinding operations

- Manage destination milestones with `gh api repos/ArnaudJalbert/aweille/milestones` (GET to find one; POST with `-f title="..." -f description="..."` to create one). Assign an issue with `gh issue edit <number> --milestone "<title>"`. Follow Wayfinder's milestone convention for maps, child tickets, and implementation follow-up.
- Create the map as an issue labelled `wayfinder:map`. Its body contains Destination, Notes, Decisions so far, Not yet specified, and Out of scope.
- Create each decision ticket as a GitHub sub-issue of the map using `gh api`. Label it `wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling`, or `wayfinder:task`.
- Add blocking relationships through GitHub's native issue-dependency API: `gh api --method POST repos/ArnaudJalbert/aweille/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-database-id>`. Obtain the database ID with `gh api repos/ArnaudJalbert/aweille/issues/<number> --jq .id`.
- If sub-issues are unavailable, use a linked task list in the map and a named parent link in each child. If native dependencies are unavailable, use a `Blocked by:` line containing linked blocker titles in each child.
- Find the frontier among the map's open children. Keep tickets with no assignee and no open blockers, preserving child order. Native dependencies expose the live blocker count in `issue_dependencies_summary.blocked_by`.
- Claim a ticket before working by assigning it with `gh issue edit <number> --add-assignee @me`.
- Resolve a ticket by posting its answer as a comment, closing it, then adding a linked-title context pointer to the map's Decisions so far. Link supporting assets from the resolution comment.

Wayfinder plans decisions. Application implementation follows the planning handoff unless the map explicitly includes execution.
