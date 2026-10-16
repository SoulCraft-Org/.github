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
read-only `soulcraft-ci` GitHub App that lets a package's CI read the private workspace's cast tool. The organization
variable `COMFY_BASE_REPO` says where ComfyUI Base lives (default `SoulCraft-Org/ComfyUI-Base`), and `CI_RUNNER`
(private repositories only) where the jobs run: `hf` is the organization's self-hosted runner on a free Hugging Face
Space (label `soulcraft-hf`, runner group `hf-free`; SoulCraft-Org/workspace `ci/hf-runner/`), anything else GitHub's
`ubuntu-24.04`.

What runs when, so testing costs nothing (2026-10-16): **tier 0** is ComfyUI Base's `_build/quick.sh <pkg>`, seconds,
run by whoever makes a change; **tier 1** is `package-ci.yml` on each pull request (not again on the merge to main:
the pull request already ran it) and on each release tag, on the free self-hosted runner while `CI_RUNNER` is `hf`;
**tier 2** is `package-gpu.yml`, by hand, on the pod.
