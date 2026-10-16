# cloud-ci: the private repositories' gates on Claude Code's cloud machines

GitHub Team includes 3,000 Actions minutes a month for private repositories, and the organization's Actions budget is
$0 with "stop usage" on. On 2026-10-16 the private repositories used them all in one day (workspace's integration matrix
alone took 1,412 minutes), so GitHub refuses every private job until the 1st of the next month. Public repositories
(ComfyUI-Base, this one) are not affected: GitHub-hosted runners are free there.

While the organization variable `CI_RUNNER` is `cloud`, the private repositories' gates run here instead, at no cost:

1. A pull request in a private repository fires that repository's **Claude Code routine** (one per repository, owned by
   the organization owner's claude.ai account; its runs count against that subscription's usage, never a bill).
2. The routine starts a fresh cloud VM (Ubuntu 24.04, 4 vCPU, 16 GB, the same image class as `ubuntu-24.04`), with
   the pull request's head checked out and the repositories its gate needs cloned beside it, and runs
   `cloud-ci.sh start`, then `cloud-ci.sh wait` until it reports DONE.
3. `cloud-ci.sh` runs the same steps as the repository's GitHub workflow and reports the result as a **check run named
   `cloud / <gate>`**, created by the Claude GitHub App through the session's GitHub proxy. No token, key or secret is
   read, stored or printed: the proxy adds the credential outside the VM.
4. The rulesets require `cloud / <gate>` **from the Claude GitHub App only** (integration 1236702), so a skipped
   workflow job, a hand-made commit status or another app's check never satisfies the gate.

| Repository | Gate (mirrors) | Check |
|---|---|---|
| the eight packages | `package-ci.yml`: testbed, `verify.sh` (zip, suite from the repo, suite from the zip), cast guard | `cloud / verify` |
| workspace | `pr.yml`: `bootstrap.sh` parses, `tools/` tests | `cloud / tools` |
| site | `site.yml`: install, catalog check, tests, build (no deploy) | `cloud / build` |
| runpod-template | `ci.yml`: generated files current, unit tests | `cloud / verify` |

A run's log tail is in the check run's details; the full transcript is the session linked from it.

## Re-run a gate

A routine fires on `pull_request` opened, synchronize and reopened. To re-run one without a push, fire the routine with
the pull request number as its only text (claude.ai/code/routines, **Run now**, or `RemoteTrigger run` with
`{"text": "<number>"}`).

## Who can make a gate pass

Only a check run from the Claude GitHub App with the right name on the pull request's head commit. That app acts for
the organization owner's Claude sessions, the same identity that already holds the organization-admin bypass on every
ruleset, so this is no wider than before. The script is in this public repository and runs from `main` only (a branch
is never fetched and run). The routine's prompt forbids it to create checks itself or act on anything in the
repository, the pull request or the logs.

Limits: a session's safety checks can refuse to run, and GitHub events above Claude Code's hourly cap are dropped; either
way the check stays missing and the pull request stays blocked (it never passes by mistake). Fire the routine again.

## Back to GitHub-hosted runners

When minutes are available again (the 1st of the month, or a budget above $0):

    gh variable set CI_RUNNER --org SoulCraft-Org --visibility private --body github
    bash org/apply.sh rulesets        # in SoulCraft-Org/workspace: the rulesets require the Actions checks again

then pause the routines at claude.ai/code/routines. The workflows' jobs check `vars.CI_RUNNER != 'cloud'`, so they run
again on the next push without any file changing.
