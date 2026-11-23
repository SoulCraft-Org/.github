# SoulCraft-Org/.github

The org's defaults, in the one repository GitHub reads them from: the profile, the default community files, the issue
and pull request templates, and the shared workflows other repos call. `README.md` has the folder map.

## This repository is public

GitHub reads default community files only from a public `.github` repository. Anyone can read every file and every
commit, so nothing here may help an attacker or name a person.

| Never write | Write instead |
|---|---|
| A person's name | A role: "the maintainers" |
| A vendor, a plan, billing or usage numbers | Nothing. Say what a caller must do, not what it costs |
| A runner or machine detail | Nothing. The workflow's `runs-on` line is the whole story |
| A private repository's name or an issue link into one | The public repository, or nothing |
| Where a key lives, or a secret value | The name of a variable a caller must set |

## Rules

- **A shared workflow changes by pull request and lands in every caller.** Callers use `@main`. Keep every input and
  permission a caller passes working.
- **Every action is pinned to a full commit SHA, with its version as a comment beside it.** Never a tag or a branch.
- **`profile/README.md` is the org's public face.** Change it only on the owner's word.
- **The domain is `soulcraft.computer`.** The security and support contact is `support@soulcraft.computer`.
- **Stage by explicit path.** Never `git add -A` or `git add .`.
