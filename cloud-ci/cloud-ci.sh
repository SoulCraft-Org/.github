#!/usr/bin/env bash
# The SoulCraft-Org gates, run inside a Claude Code cloud session (a routine fired by a pull request) instead of on a
# GitHub-hosted runner. Same steps as the GitHub workflows, same check names prefixed "cloud / ", reported as a check
# run (or a commit status) through the session's GitHub proxy (no token or secret is read or stored here).
#
#   bash cloud-ci.sh start [<pr-number>]   from the pull request's checkout: start the gate, detached (it outlives the
#                                          session's 10-minute command limit); with a PR number, check out its head first
#   bash cloud-ci.sh wait                  block up to 9 minutes; prints RUNNING <last log line> or DONE <conclusion>
#
# Which gate runs is the repository's name (see gate() below); the GitHub workflow it mirrors is named beside each one.
# Why this exists, and how to go back to GitHub-hosted runners: README.md beside this file.
set -uo pipefail

ORG="SoulCraft-Org"
STATE="/tmp/cloud-ci"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

die(){ echo "cloud-ci: $*" >&2; exit 2; }

repo_name(){ # the repository the current directory is a clone of
  git remote get-url origin 2>/dev/null | sed -E 's#\.git$##; s#.*[/:]([^/]+/[^/]+)$#\1#' | cut -d/ -f2
}

check_name(){ # <repo>: the required check this repository's ruleset names, as "cloud / <gate>"
  case "$1" in
    workspace) echo "cloud / tools" ;;
    site) echo "cloud / build" ;;
    runpod-template|ComfyUI-Base) echo "cloud / verify" ;;
    *) echo "cloud / verify" ;;     # every package
  esac
}

session_url(){
  local id="${CLAUDE_CODE_REMOTE_SESSION_ID:-}"
  [ -n "$id" ] && echo "https://claude.ai/code/session_${id#cse_}" || echo ""
}

# ── the result on GitHub (the session's GitHub proxy adds the credential outside the VM; no token is read here) ──
# A check run when the proxy's credential may create one (a GitHub App's), else a commit status with the same name.
# GitHub's answer to a refused request goes to $STATE/report.err and into the DONE line.
report_start(){ # <repo> <sha> <name>: prints check:<id> or status
  local url id; url="$(session_url)"
  if id="$(gh api -X POST "repos/$ORG/$1/check-runs" -f name="$3" -f head_sha="$2" -f status=in_progress \
      ${url:+-f details_url="$url"} -f "output[title]=running in a Claude Code cloud session" \
      -f "output[summary]=Started $(date -u +%FT%TZ). ${url:+Session: $url}" --jq .id 2>>"$STATE/report.err")"; then
    echo "check:$id"
  elif gh api -X POST "repos/$ORG/$1/statuses/$2" -f state=pending -f context="$3" ${url:+-f target_url="$url"} \
      -f description="running in a Claude Code cloud session" --silent 2>>"$STATE/report.err"; then
    echo status
  else
    return 1
  fi
}
report_done(){ # <repo> <sha> <name> <mode> <conclusion> <log>
  local title text url; url="$(session_url)"
  [ "$5" = success ] && title="passed" || title="failed"
  if [ "${4%%:*}" = check ]; then
    # the log's last lines, ANSI colours stripped, under GitHub's 65535-character limit for output.text
    text="$(sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' "$6" | tail -n 250 | tail -c 60000)"
    gh api -X PATCH "repos/$ORG/$1/check-runs/${4#check:}" -f status=completed -f conclusion="$5" \
      -f "output[title]=$title" -f "output[summary]=$(cat "$STATE/summary" 2>/dev/null)" \
      -f "output[text]=\`\`\`
$text
\`\`\`" --silent 2>>"$STATE/report.err"
  else
    gh api -X POST "repos/$ORG/$1/statuses/$2" -f state="$5" -f context="$3" ${url:+-f target_url="$url"} \
      -f description="$title in a Claude Code cloud session ($(tail -n 1 "$STATE/summary" | cut -c1-80))" --silent 2>>"$STATE/report.err"
  fi
}

# ── the workspace: the repositories the routine attached, side by side, as bootstrap.sh would lay them out ──
layout(){ # <repo-dir>: prints the workspace path; COMFY_BASE is the attached ComfyUI-Base checkout
  local root ws d n
  root="$(dirname "$1")"; ws="$STATE/ws"
  rm -rf "$ws"; mkdir -p "$ws"
  for d in "$root"/*/; do
    d="${d%/}"; [ -d "$d/.git" ] || continue
    n="$(cd "$d" && repo_name)"
    [ -n "$n" ] && [ "$n" != ComfyUI-Base ] && ln -s "$d" "$ws/$n"
  done
  echo "$ws"
}
base_at(){ # <tag>: move the attached ComfyUI-Base checkout to that tag
  [ -n "${COMFY_BASE:-}" ] || { echo "ComfyUI-Base is not attached to this routine (its sources)"; return 1; }
  git -C "$COMFY_BASE" fetch -q --depth 1 origin "refs/tags/$1:refs/tags/$1" && git -C "$COMFY_BASE" -c advice.detachedHead=false checkout -q "$1"
}
newest_base(){
  git ls-remote --tags --refs "https://github.com/$ORG/ComfyUI-Base" 'base-v*' | sed 's|.*refs/tags/||' | sort -V | tail -1
}
pinned_base(){ sed -n 's/^base [^ ]* \(base-v[0-9.]*\).*/\1/p' "$WS/workspace/repos.txt"; }

gate(){ # <repo>: the same steps as that repository's GitHub workflow
  local name="$1"
  case "$name" in
    workspace)                                     # workspace/.github/workflows/pr.yml (job "tools")
      cd "$WS/workspace"
      bash -n bootstrap.sh
      uv run --no-project --with pytest python -m pytest tools -q -p no:cacheprovider ;;
    site)                                          # site/.github/workflows/site.yml (job "build"), no deploy
      base_at "$(pinned_base)" || return 1
      cd "$WS/site"
      corepack enable >/dev/null 2>&1 || npm install -g pnpm@10 >/dev/null
      pnpm install --frozen-lockfile && python3 _build/catalog.py --check && pnpm test && pnpm build ;;
    runpod-template)                               # runpod-template/.github/workflows/ci.yml (job "verify")
      base_at "$(pinned_base)" || return 1
      cd "$WS"
      python3 runpod-template/image/dockerize.py --check &&
        uv run --no-project --with pytest python -m pytest -c runpod-template/pytest.ini runpod-template -q -p no:cacheprovider ;;
    *)                                             # every package: .github/workflows/package-ci.yml (job "verify")
      [ -f "$WS/$name/$name-script.sh" ] || { echo "not a package: $name"; return 2; }
      local ref; ref="$(newest_base)"; [ -n "$ref" ] || { echo "no base-v* tag on $ORG/ComfyUI-Base"; return 1; }
      base_at "$ref" || return 1
      echo "ComfyUI Base $ref ($(cat "$COMFY_BASE/VERSION"))" | tee -a "$STATE/summary"
      cd "$WS"
      local v                                      # the App-view tier's browser, per playwright version the package pins
      for v in $(grep -rhoE 'playwright==[0-9.]+' "$name/_build" 2>/dev/null | sort -u | cut -d= -f3); do
        uvx --from "playwright==$v" playwright install --with-deps chromium || return 1
      done
      bash "$COMFY_BASE/testbed.sh" --server || return 1
      bash "$COMFY_BASE/_build/verify.sh" "$name"; local rc=$?
      bash "$COMFY_BASE/testbed.sh" --stop >/dev/null 2>&1 || true
      [ $rc -eq 0 ] || return $rc
      local host; host="$(python3 "$COMFY_BASE/_build/package.py" --host "$name")"
      python3 "$WS/workspace/tools/cast/cast.py" guard "$name/$name-$host.zip" ;;
  esac
}

run(){ # the detached part: result pending on GitHub, the gate, result final on GitHub
  local name sha mode rc conclusion check
  name="$(repo_name)"; sha="$(git rev-parse HEAD)"; check="$(check_name "$name")"
  : > "$STATE/summary"
  echo "$ORG/$name @ ${sha:0:12}, $(nproc) CPUs, $(free -g | awk '/Mem:/{print $2}') GB" >> "$STATE/summary"
  if ! mode="$(report_start "$name" "$sha" "$check")"; then
    echo "DONE error (GitHub refused the result: $(tr '\n' ' ' < "$STATE/report.err" | cut -c1-300))" > "$STATE/done"; return
  fi
  echo "$mode" > "$STATE/mode"
  export COMFY_BASE BASE_WORKSPACE="$WS" WS
  timeout 5400 bash "$HERE/cloud-ci.sh" _gate "$name" >> "$STATE/log" 2>&1
  rc=$?
  [ $rc -eq 0 ] && conclusion=success || conclusion=failure
  [ $rc -eq 124 ] && echo "timed out after 90 minutes" >> "$STATE/summary"
  echo "exit $rc after $(( $(date +%s) - $(cat "$STATE/start") ))s" >> "$STATE/summary"
  if report_done "$name" "$sha" "$check" "$mode" "$conclusion" "$STATE/log"; then
    echo "DONE $conclusion ($check as a ${mode%%:*}, $(tail -n 1 "$STATE/summary"))" > "$STATE/done"
  else
    echo "DONE error (gate $conclusion; GitHub refused the result: $(tr '\n' ' ' < "$STATE/report.err" | cut -c1-300))" > "$STATE/done"
  fi
}

case "${1:-}" in
  start)
    [ -d .git ] || die "run it from the pull request's checkout"
    if [ -n "${2:-}" ]; then
      git fetch -q origin "pull/$2/head" && git -c advice.detachedHead=false checkout -q FETCH_HEAD || die "cannot fetch PR $2"
    fi
    rm -rf "$STATE"; mkdir -p "$STATE"; date +%s > "$STATE/start"
    COMFY_BASE="$(dirname "$PWD")/ComfyUI-Base"
    [ -d "$COMFY_BASE/.git" ] || COMFY_BASE=""    # the workspace gate needs no base; the others say so when it is missing
    WS="$(layout "$PWD")"
    export COMFY_BASE WS STATE
    setsid nohup bash -c "cd '$PWD' && COMFY_BASE='$COMFY_BASE' WS='$WS' bash '$HERE/cloud-ci.sh' _run" > "$STATE/runner.log" 2>&1 < /dev/null &
    echo "started $(repo_name) @ $(git rev-parse --short HEAD): $(check_name "$(repo_name)")" ;;
  _run) run ;;
  _gate) gate "$2" ;;
  wait)
    for _ in $(seq 54); do [ -f "$STATE/done" ] && { cat "$STATE/done"; exit 0; }; sleep 10; done
    echo "RUNNING $(tail -n 1 "$STATE/log" 2>/dev/null | cut -c1-200)" ;;
  *) sed -n '2,13p' "$0"; exit 2 ;;
esac
