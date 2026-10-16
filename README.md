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
| `workflow-templates/` | "New workflow" templates for a new package repository |

The packages call the reusable workflows at `@main`: one maintainer, and a change here is a pull request whose own
check is the next package run. When a second consumer appears, tag `v1` and move the callers to it, so a breaking
change ships as `v2` one package at a time.

Secrets the workflows read (organization secrets, set by `workspace/org/apply.sh`): `CI_APP_ID` and `CI_APP_KEY`, the
read-only `soulcraft-ci` GitHub App that lets a package's CI read the private workspace's cast tool. The organization
variable `COMFY_BASE_REPO` says where ComfyUI Base lives (default `Soul-Craft/ComfyUI-Base`, its first home).
