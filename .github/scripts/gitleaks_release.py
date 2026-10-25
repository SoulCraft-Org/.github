"""gitleaks' release in gitleaks.yml, a pin no Dependabot ecosystem reads: moves it to the newest release.

    python3 -I .github/scripts/gitleaks_release.py            # the pinned release and the newest; nothing written
    python3 -I .github/scripts/gitleaks_release.py --write    # every pin to the newest (nothing when it is current)

Run each morning by .github/workflows/gitleaks-release.yml, which makes a rewrite a pull request that merges itself once
`gitleaks` passes; by hand from any machine with gh. The pinned release is VERSION in .github/workflows/gitleaks.yml,
with SHA256_X64 and SHA256_ARM64 beside it: the linux_x64 and linux_arm64 lines of the release's
gitleaks_<VERSION>_checksums.txt, each checked against the digest GitHub publishes for that asset when it has one. This
repository's .pre-commit-config.yaml hook moves too, to the release's commit with the version as the frozen comment
(the form Dependabot writes), unless Dependabot moved it first. Prints pinned=<x.y.z> and newest=<x.y.z> on stdout
(for $GITHUB_OUTPUT). Exit 1 when a pin is not where this script looks, or the two published sums disagree.
"""
import json
import os
import re
import subprocess
import sys

REPO = "gitleaks/gitleaks"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKFLOW = ".github/workflows/gitleaks.yml"
HOOKS = ".pre-commit-config.yaml"
ARCHES = {"SHA256_X64": "linux_x64", "SHA256_ARM64": "linux_arm64"}  # env name: tarball architecture
SEMVER = r"\d+\.\d+\.\d+"
HOOK = re.compile(r"(repo: https://github\.com/gitleaks/gitleaks\s*\n\s*rev:\s*)([0-9a-f]{40})(\s*#\s*frozen:\s*v)("
                  + SEMVER + r")\b")


def env_line(name, value):
    """A pattern for gitleaks.yml's `NAME: value` env line (value a group), which must stand there exactly once."""
    return re.compile(rf"^(\s+{name}:\s*)({value})\s*$", re.M)


def pinned(text, name, value):
    found = env_line(name, value).findall(text)
    if len(found) != 1:
        sys.exit(f"{WORKFLOW}: {len(found)} '{name}:' lines where one was expected")
    return found[0][1]


def newer(a, b):
    """True when release a is newer than release b (by number: 8.30.10 is newer than 8.30.9)."""
    return tuple(map(int, a.split("."))) > tuple(map(int, b.split(".")))


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def gh(path):
    return json.loads(run("gh", "api", path))


def sums(release):
    """{env name: SHA-256 hex} for the two linux tarballs, from the release's checksums.txt, each matched against the
    digest GitHub publishes for the asset (gitleaks' own file and GitHub's upload record must agree)."""
    v = release["tag_name"].lstrip("v")
    listed = run("gh", "release", "download", release["tag_name"], "-R", REPO,
                 "-p", f"gitleaks_{v}_checksums.txt", "-O", "-")
    by_name = {m.group(2): m.group(1) for m in re.finditer(r"^([0-9a-f]{64})\s+\*?(\S+)\s*$", listed, re.M)}
    digest = {a["name"]: str(a.get("digest") or "") for a in release.get("assets", [])}
    found = {}
    for name, arch in ARCHES.items():
        tarball = f"gitleaks_{v}_{arch}.tar.gz"
        if tarball not in by_name:
            sys.exit(f"{REPO} {release['tag_name']}: gitleaks_{v}_checksums.txt has no {tarball} line")
        if digest.get(tarball, "").startswith("sha256:") and digest[tarball] != f"sha256:{by_name[tarball]}":
            sys.exit(f"{REPO} {release['tag_name']}: {tarball} is {digest[tarball]} on GitHub but "
                     f"{by_name[tarball]} in its checksums.txt")
        found[name] = by_name[tarball]
    return found


def commit(tag):
    """The commit a tag names, through an annotated tag object when it is one (v8.30.1 is lightweight)."""
    obj = gh(f"repos/{REPO}/git/ref/tags/{tag}")["object"]
    if obj["type"] == "tag":
        obj = gh(f"repos/{REPO}/git/tags/{obj['sha']}")["object"]
    return obj["sha"]


def main(argv):
    def read(path):
        with open(os.path.join(ROOT, path)) as f:
            return f.read()

    workflow, hooks = read(WORKFLOW), read(HOOKS)
    old = pinned(workflow, "VERSION", SEMVER)
    latest = gh(f"repos/{REPO}/releases/latest")
    new = latest["tag_name"].lstrip("v")
    if not re.fullmatch(SEMVER, new):
        sys.exit(f"{REPO}: the latest release is {latest['tag_name']}, not v<x.y.z>")
    print(f"pinned={old}")
    print(f"newest={new}")
    if not newer(new, old):
        print(f"gitleaks {old} is the newest release", file=sys.stderr)
        return 0

    moved = {}
    text = env_line("VERSION", SEMVER).sub(rf"\g<1>{new}", workflow)
    for name, value in sums(latest).items():
        pinned(text, name, "[0-9a-f]{64}")
        text = env_line(name, "[0-9a-f]{64}").sub(rf"\g<1>{value}", text)
    moved[WORKFLOW] = text

    hook = HOOK.search(hooks)
    if not hook:
        sys.exit(f"{HOOKS}: no gitleaks hook with a 'rev: <commit>  # frozen: v<x.y.z>' line")
    if newer(new, hook.group(4)):
        moved[HOOKS] = HOOK.sub(rf"\g<1>{commit(latest['tag_name'])}\g<3>{new}", hooks)
    else:
        print(f"{HOOKS}: the hook is at v{hook.group(4)} already (Dependabot moved it)", file=sys.stderr)

    for path, text in moved.items():
        if "--write" in argv:
            with open(os.path.join(ROOT, path), "w") as f:
                f.write(text)
        print(f"{'moved' if '--write' in argv else 'would move'} {path}: {old} -> {new}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
