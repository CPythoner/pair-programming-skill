#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install.sh <portable|codex|cursor|gemini-cli|github-copilot|claude-code|opencode> [options]

Options:
  --scope <project|user>   Installation scope. Default: project
  --target <dir>           Project root for project scope. Default: current directory
  --native                 Use the host-native directory when it differs from .agents/skills
  --force                  Replace an existing installation
  -h, --help               Show this help

Portable-first defaults:
  portable / codex / cursor / gemini-cli / github-copilot -> .agents/skills
  claude-code -> .claude/skills
  opencode -> .opencode/skills

Native overrides:
  cursor         -> .cursor/skills
  gemini-cli     -> .gemini/skills
  github-copilot -> .github/skills (project), ~/.copilot/skills (user)
EOF
}

if [[ $# -lt 1 ]]; then usage; exit 2; fi
platform="$1"; shift
scope="project"
target="$(pwd)"
force="false"
native="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope) scope="${2:-}"; shift 2 ;;
    --target) target="${2:-}"; shift 2 ;;
    --native) native="true"; shift ;;
    --force) force="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

case "$platform" in
  portable|codex|cursor|gemini-cli|github-copilot|claude-code|opencode) ;;
  *) echo "Unsupported platform: $platform" >&2; exit 2 ;;
esac
case "$scope" in
  project|user) ;;
  *) echo "Unsupported scope: $scope" >&2; exit 2 ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_root="$(cd "$script_dir/.." && pwd)"

if [[ "$scope" == "project" ]]; then
  project_root="$(cd "$target" && pwd)"
  case "$platform" in
    portable|codex) parent="$project_root/.agents/skills" ;;
    cursor)
      [[ "$native" == "true" ]] && parent="$project_root/.cursor/skills" || parent="$project_root/.agents/skills"
      ;;
    gemini-cli)
      [[ "$native" == "true" ]] && parent="$project_root/.gemini/skills" || parent="$project_root/.agents/skills"
      ;;
    github-copilot)
      [[ "$native" == "true" ]] && parent="$project_root/.github/skills" || parent="$project_root/.agents/skills"
      ;;
    claude-code) parent="$project_root/.claude/skills" ;;
    opencode) parent="$project_root/.opencode/skills" ;;
  esac
else
  : "${HOME:?HOME must be set for user-level installation}"
  case "$platform" in
    portable|codex) parent="$HOME/.agents/skills" ;;
    cursor)
      [[ "$native" == "true" ]] && parent="$HOME/.cursor/skills" || parent="$HOME/.agents/skills"
      ;;
    gemini-cli)
      [[ "$native" == "true" ]] && parent="$HOME/.gemini/skills" || parent="$HOME/.agents/skills"
      ;;
    github-copilot)
      [[ "$native" == "true" ]] && parent="$HOME/.copilot/skills" || parent="$HOME/.agents/skills"
      ;;
    claude-code) parent="$HOME/.claude/skills" ;;
    opencode) parent="${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills" ;;
  esac
fi

dest="$parent/pair-programming"

if [[ -e "$dest" ]]; then
  if [[ "$force" != "true" ]]; then
    echo "Pair Programming Skill already exists at:" >&2
    echo "  $dest" >&2
    if [[ "$parent" == */.agents/skills ]]; then
      echo "This shared Agent Skills installation can be discovered by multiple compatible hosts." >&2
    fi
    echo "Re-run with --force to replace it." >&2
    exit 3
  fi
  rm -rf "$dest"
fi

tmp="${dest}.tmp.$$"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp"
cp "$source_root/SKILL.md" "$tmp/SKILL.md"
cp -R "$source_root/reference" "$tmp/reference"
cp -R "$source_root/templates" "$tmp/templates"
cp -R "$source_root/examples" "$tmp/examples"
cp -R "$source_root/schemas" "$tmp/schemas"
mkdir -p "$tmp/scripts"
cp "$source_root/scripts/check-guide.py" "$tmp/scripts/check-guide.py"
mkdir -p "$parent"
mv "$tmp" "$dest"
trap - EXIT

echo "Installed pair-programming for $platform ($scope):"
echo "  $dest"

case "$platform" in
  codex|portable) echo 'Codex: $pair-programming status' ;;
  cursor) echo 'Cursor: /pair-programming status' ;;
  gemini-cli) echo 'Gemini CLI: ask it to use the pair-programming skill, then run your semantic pair command.' ;;
  github-copilot) echo 'Copilot: Use the /pair-programming skill and run status.' ;;
  claude-code|opencode) echo 'Try: /pair-programming status' ;;
esac
