#!/usr/bin/env bash
set -euo pipefail

readonly SOURCE_URL="https://github.com/j-mauro-r/dengue-signal-atlas.git"
readonly SOURCE_BRANCH="main"
readonly PREFIX="apps/dashboard"

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

subtree() {
  local primary
  primary="$(git --exec-path)/git-subtree"
  if [[ -x "${primary}" ]]; then
    git subtree "$@"
  elif [[ -x /usr/lib/git-core/git-subtree ]]; then
    git --exec-path=/usr/lib/git-core subtree "$@"
  else
    printf '%s\n' "git-subtree is required but was not found." >&2
    return 127
  fi
}

require_clean_worktree() {
  if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
    printf '%s\n' "Refusing subtree synchronization with a dirty worktree." >&2
    return 1
  fi
}

require_feature_branch() {
  local current_branch
  current_branch="$(git branch --show-current)"
  if [[ -z "${current_branch}" || "${current_branch}" == "main" || "${current_branch}" == "master" ]]; then
    printf '%s\n' "Run dashboard synchronization from a feature branch, never main." >&2
    return 1
  fi
}

pull_source() {
  require_clean_worktree
  require_feature_branch
  subtree pull --prefix="${PREFIX}" "${SOURCE_URL}" "${SOURCE_BRANCH}" --squash
}

publish_branch() {
  local destination_branch="${1:-}"
  if [[ -z "${destination_branch}" ]]; then
    printf '%s\n' "Usage: $0 publish <new-dashboard-branch>" >&2
    return 2
  fi
  if [[ "${destination_branch}" == "main" || "${destination_branch}" == "master" ]]; then
    printf '%s\n' "Refusing to publish dashboard changes to ${destination_branch}." >&2
    return 2
  fi
  git check-ref-format --branch "${destination_branch}" >/dev/null

  # Pull first on every outbound flow so the split includes current source/main.
  pull_source

  if git ls-remote --exit-code --heads "${SOURCE_URL}" "refs/heads/${destination_branch}" >/dev/null 2>&1; then
    printf '%s\n' "Remote branch ${destination_branch} already exists; choose a new branch." >&2
    return 2
  fi

  local split_commit
  split_commit="$(subtree split --prefix="${PREFIX}")"
  git push "${SOURCE_URL}" "${split_commit}:refs/heads/${destination_branch}"
}

case "${1:-}" in
  pull)
    [[ $# -eq 1 ]] || { printf '%s\n' "Usage: $0 pull" >&2; exit 2; }
    pull_source
    ;;
  publish)
    [[ $# -eq 2 ]] || { printf '%s\n' "Usage: $0 publish <new-dashboard-branch>" >&2; exit 2; }
    publish_branch "$2"
    ;;
  *)
    printf '%s\n' "Usage: $0 {pull|publish <new-dashboard-branch>}" >&2
    exit 2
    ;;
esac
