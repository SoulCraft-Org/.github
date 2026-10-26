# SoulCraft-Org/.github

The organisation's defaults, in the one repository GitHub reads them from: the public profile, the default community
health files, the issue and pull-request templates, and the reusable workflows every package calls. `README.md` has the
table of what each path does. Read it before changing a workflow.

## This repository is public

GitHub applies default community health files only from a public `.github` repository, so nothing private goes here:
no secret value, no private repository's contents, no pod id, no internal path beyond what `README.md` already states.
Names of secrets and variables the workflows read are fine.

## Rules

- **A change to a reusable workflow lands in every package's next run.** The packages call `package-ci.yml`,
  `package-release.yml` and `package-gpu.yml` at `@main`. Make the change by pull request, keep every input the callers
  pass working, and expect the next package run to be the check.
- **Every action is pinned to a full commit SHA with its version as a comment beside it.** Dependabot moves the pins in
  one grouped pull request each weekday; do not pin to a tag or a branch.
- **Where jobs run is stated in `README.md`** (the self-hosted pool for private repositories, GitHub-hosted for public
  ones). Do not add a GitHub-hosted fallback for a private repository.
- **`profile/README.md` is the organisation's public face.** Change it only on the owner's word.
- **The domain is `soulcraft.computer`.** A page here that names the website uses it.
- Stage by explicit path; never `git add -A` or `git add .`. Every defect found is a GitHub issue in the repository whose
  code is at fault. Nothing worth keeping exists only on one Mac: push the branch or open a pull request.

## House rules for the packages

The packages' working rules (the session cycle, the list rule, versions and zips, SFW only) are in the private
repository `SoulCraft-Org/workspace`, in `AGENTS.md`; `gh repo clone SoulCraft-Org/workspace` fetches it for members. The
gate these workflows run is ComfyUI Base's `_build/verify.sh`; its design is in the base's handbook.
