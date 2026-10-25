# SoulCraft-Org/.github

The organization's defaults, in the one repository GitHub reads them from. It is public because GitHub only applies
default community health files and issue and pull-request templates from a public `.github` repository. Nothing private lives here.

| Path | What it does |
|---|---|
| `profile/README.md` | The organization's public profile page |
| `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md` | Defaults for every repository that has none of its own |
| `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md` | The default issue forms and pull-request template |
| `.github/workflows/package-ci.yml` | The gate every workflow package calls from its `ci.yml`: zip matches tree, suite from the repository, suite from the extracted zip (ComfyUI Base's `verify.sh`), then the private cast guard |
| `.github/workflows/package-release.yml` | Called on a `v<version>` tag: checks the tag against `PKG_VERSION`, re-runs the gate with the cast guard required, and attaches `<name>-runpod.zip` to a GitHub release |
| `.github/workflows/package-gpu.yml` | By hand (`workflow_dispatch` in a package's `gpu.yml`): the suite's pod-only tiers (`runpod`, `gpu`) on the pod itself, which is a free ephemeral self-hosted runner labelled `gpu-pod` while it is up (ComfyUI Base `podctl runner <pod>`). It installs and restarts nothing |
| `.github/workflows/gitleaks.yml` | Secret scanning for every repository: gitleaks over the whole history, failing on a finding. package-ci.yml calls it for the packages; the others call it from their own `gitleaks.yml` |
| `workflow-templates/` | "New workflow" templates for a new package repository |

The packages call the reusable workflows at `@main`: one maintainer, and a change here is a pull request whose own
check is the next package run. When a second consumer appears, tag `v1` and move the callers to it, so a breaking
change ships as `v2` one package at a time.

Every action these workflows use is pinned to a full commit SHA, with its version as a comment beside it
(GitHub's guidance: a SHA is the only reference that cannot be moved). Dependabot moves the pins in one grouped weekly
pull request.

Secrets the workflows read (organization secrets, set by `workspace/org/apply.sh`): `CI_APP_ID` and `CI_APP_KEY`, the
read-only `soulcraft-ci` GitHub App that lets a package's CI read the private workspace's cast tool; `ROUTER_APP_KEY`
(with the variable `ROUTER_CLIENT_ID`), the `soulcraft-router` app of the CI router below. The organization
variable `COMFY_BASE_REPO` says where ComfyUI Base lives (default `SoulCraft-Org/ComfyUI-Base`), and `CI_RUNNER`
(private repositories only) where the jobs run: `hf` is the organization's self-hosted runner on a free Hugging Face
Space (label `soulcraft-hf`, runner group `hf-free`; SoulCraft-Org/workspace `ci/hf-runner/`), anything else GitHub's
`ubuntu-24.04`.

What runs when, so testing costs nothing (2026-10-16): **tier 0** is ComfyUI Base's `_build/quick.sh <pkg>`, seconds,
run by whoever makes a change; **tier 1** is `package-ci.yml` on each pull request (not again on the merge to main:
the pull request already ran it) and on each release tag, on the free self-hosted runner while `CI_RUNNER` is `hf`;
**tier 2** is `package-gpu.yml`, by hand, on the pod.

## The CI router: a free slot first, overflow minutes second

GitHub has no fallback between runner labels (a job's `runs-on` labels must all match one runner), so a job aimed at
the free self-hosted pool waits whenever every slot is busy, even while free hosted minutes sit unused. With the router
on, `package-ci.yml` runs a `route` job before `verify`: it reads the organization's runners and sends `verify` to the
free pool (`soulcraft-hf`, or `soulcraft-free` while `CI_POOL` is `on`) when a slot is idle. Only when none is idle,
and overflow is allowed, it sends `verify` to the first overflow label that has used less than 90% of its free minutes
this month; with none left, `verify` waits for a slot as before. After an overflow run, a `ledger` job adds its minutes
to the month's count and, once every allowance is at 90%, turns overflow off until the month ends. The required check
stays `verify / verify`; `route` and `ledger` are extra checks beside it. The run's summary and the `route` job's log
say why it picked what it picked (`route: ["ubuntu-latest"]: 0 of 2 online soulcraft-hf slots idle (reserve 0);
overflow to ubuntu-latest (12 of its 3000 free minutes used in 2026-10)`).

Both jobs run on their own light runner processes, label **`soulcraft-router`** (one per Hugging Face Space, beside the
runner processes; SoulCraft-Org/workspace `ci/hf-runner/`), never GitHub-hosted: a hosted job is billed a whole minute,
and the router runs on every pull request. **While no `soulcraft-router` process is online, a routed run's `route` job
waits**: turn `CI_ROUTER` off and re-run it.

The router never fails a run: no token (the app not set up yet, or a Dependabot run, which gets no organization
secrets), an API error or unreadable data all route to the free pool.

### Switches (organization variables, visibility "Private repositories")

| Variable | Value | Effect |
|---|---|---|
| `CI_ROUTER` | `on` | the `route` job runs, in private repositories while `CI_RUNNER` is `hf`. **Unset: today's behaviour**, `route` and `ledger` are skipped and `verify` picks its runner as before |
| `CI_OVERFLOW_ENABLED` | `true` | overflow allowed when no slot is idle. Anything else, or unset: never overflow (wait for a slot). The ledger job writes `full <yyyy-mm>` when every allowance is 90% used; the router reads that as off for that month and on again the next |
| `CI_OVERFLOW_LABELS` | `<runs-on label>=<free minutes a month> ...` in order | where overflow goes, first choice first. Today `ubuntu-latest=3000` (GitHub Team); once Blacksmith's app is installed, `blacksmith-2vcpu-ubuntu-2404-arm=4800 ubuntu-latest=3000`; later Ubicloud at the end. **Never list a label no runner serves**: a job waits 24 hours for it |
| `CI_OVERFLOW_USED` | written by the ledger job | the month's count, `<yyyy-mm> <label>=<minutes> ...`; a new month starts from zero. Set it by hand to correct it (below) |
| `CI_ROUTER_RESERVE` | a number, default `0` | overflow while this many slots or fewer are idle, keeping them for jobs the router does not route (gitleaks, release tags, other workflows). `0` = overflow only when every slot is busy |

### Turning overflow on and off

On (the router, then overflow to GitHub's minutes until Blacksmith is installed):

    gh variable set CI_OVERFLOW_LABELS  --org SoulCraft-Org --visibility private --body "ubuntu-latest=3000"
    gh variable set CI_OVERFLOW_ENABLED --org SoulCraft-Org --visibility private --body true
    gh variable set CI_ROUTER           --org SoulCraft-Org --visibility private --body on

Overflow off, the router still on (every job waits for a free slot, as before): `gh variable set CI_OVERFLOW_ENABLED
--org SoulCraft-Org --visibility private --body false`. Everything off: `gh variable delete CI_ROUTER --org
SoulCraft-Org`. A change applies to runs that start after it.

The count only knows what the router sent. GitHub's minutes are shared with every GitHub-hosted job of the private
repositories (Dependabot's included), so when overflow goes on in the middle of a month, start the count from GitHub's
own usage (public repositories' minutes are free and not counted):

    pub="$(gh repo list SoulCraft-Org --visibility public --json name --jq '[.[].name]')"
    gh api "/organizations/SoulCraft-Org/settings/billing/usage?year=$(date -u +%Y)&month=$(date -u +%-m)" \
      | jq --argjson pub "$pub" '[.usageItems[] | select(.product == "actions" and (.sku | startswith("Actions Linux"))
          and (.repositoryName | IN($pub[]) | not)) | .quantity] | add // 0 | ceil'
    gh variable set CI_OVERFLOW_USED --org SoulCraft-Org --visibility private --body "$(date -u +%Y-%m) ubuntu-latest=<that number>"

### Setup (once; Paul in the browser)

1. **The app.** https://github.com/organizations/SoulCraft-Org/settings/apps/new : name `soulcraft-router`, homepage
   `https://github.com/SoulCraft-Org/.github`, Webhook **Active off**, Permissions, Organization: **Self-hosted
   runners: Read-only** and **Variables: Read and write**, nothing else; "Only on this account"; Create. Then
   **Install App**, SoulCraft-Org (repository access does not matter: both permissions are the organization's).
2. **Its Client ID** (on the app's page) as the organization variable `ROUTER_CLIENT_ID` (visibility Private
   repositories; an id, not a secret).
3. **Its key.** Generate a private key, keep it as `API-Key-GitHub-RouterApp`, and push it as the organization secret
   **`ROUTER_APP_KEY`** (visibility Private repositories) with the API keys session (`Soul-Craft/api-keys`, local
   `~/API-Keys`). Nobody else handles it.
4. **Check:** `gh api orgs/SoulCraft-Org/installations --jq '.installations[] | select(.app_slug == "soulcraft-router")
   | .permissions'` prints `organization_self_hosted_runners: read` and `organization_actions_variables: write`.
5. **Blacksmith** (for its 4,800 free arm64 minutes, no card): install its GitHub App on SoulCraft-Org, then put its
   label first in `CI_OVERFLOW_LABELS`. The gate is proven on arm64 (Oracle); the first Blacksmith run is its test.

Why a third app: `soulcraft-ci`'s key (`CI_APP_KEY`) is read in `verify`, after the testbed has run third-party packs,
so it stays read-only. `ROUTER_APP_KEY` is also an organization secret of the private repositories, but only `route`
and `ledger` read it, on the router's processes, and it can do two things: read the runner list and change the
organization's Actions variables (at worst, flip these switches; no code, no secrets).

Why no `concurrency` group to serialize the router: GitHub scopes those to one repository, so they cannot order routers
across the organization. Two routers deciding at the same moment can both pick the last idle slot; the cost is that one
`verify` waits for a slot, as without the router, never minutes.
