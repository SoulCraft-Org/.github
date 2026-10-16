# Contributing

SoulCraft repositories are maintained by SoulCraft. Pull requests from outside the organization are welcome on the
public ones (ComfyUI-Base); the workflow repositories are private.

**Before a pull request**

- One change per pull request, described in its title and body: what changed and why.
- Run the repository's own gate locally first. For a workflow package that is ComfyUI Base's `verify.sh`
  (`bash "$COMFY_BASE/_build/verify.sh" <name>` from the workspace); for ComfyUI Base it is `bash _build/verify.sh`.
  Warnings are errors (`filterwarnings = error`): fix them, never filter them.
- Generated files are never edited by hand. A workflow JSON comes out of the package's `_build/` builder, a zip out of
  ComfyUI Base's `package.py`: change the source and rebuild.
- Stage files by path. Never `git add -A` or `git commit -a`.
- A change to anything a package ships moves its version in every place the version lives and rebuilds its zip.

**Content rule.** SoulCraft is safe for work, with no exceptions and no switch: no nudity, no sexual content, no brutal
gore or violence (realistic blood is fine), and no field, toggle, flag or model row that turns any of these on. A
change that needs one of these is declined.

Merging needs the `verify` check green. `main` takes squash merges only.
