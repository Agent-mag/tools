#!/usr/bin/env bash
# Neon color palette for Agent Sounds

NEON_CYAN="\033[38;5;51m"
NEON_MAGENTA="\033[38;5;201m"
NEON_GREEN="\033[38;5;46m"
NEON_YELLOW="\033[38;5;226m"
NEON_PURPLE="\033[38;5;129m"
NEON_WHITE="\033[38;5;231m"
NEON_ORANGE="\033[38;5;208m"
DIM="\033[2m"
BOLD="\033[1m"
ITALIC="\033[3m"
RESET="\033[0m"

supports_hyperlinks() {
  [[ -n "${WT_SESSION:-}" ]] && return 0
  [[ "${TERM_PROGRAM:-}" == "iTerm.app" ]] && return 0
  [[ "${TERM_PROGRAM:-}" == "WezTerm" ]] && return 0
  [[ -n "${KITTY_PID:-}" ]] && return 0
  [[ "${TERM:-}" == "xterm-kitty" ]] && return 0
  [[ -n "${VTE_VERSION:-}" ]] && [[ "${VTE_VERSION:-0}" -ge 5000 ]] && return 0
  return 1
}

make_link() {
  local url="$1" text="$2"
  if supports_hyperlinks; then
    printf "\033]8;;%s\033\\\\%s\033]8;;\033\\\\" "$url" "$text"
  else
    printf "%s (%s)" "$text" "$url"
  fi
}
