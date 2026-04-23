#!/usr/bin/env bash

# Skip in CI environments
[[ -n "${CI:-}" ]] || [[ -n "${CONTINUOUS_INTEGRATION:-}" ]] && exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/colors.sh"

echo ""
printf "${NEON_CYAN}${BOLD}"
cat << 'ART'
      _                    _     ____                        _
     / \   __ _  ___ _ __ | |_  / ___|  ___  _   _ _ __   __| |___
    / _ \ / _` |/ _ \ '_ \| __| \___ \ / _ \| | | | '_ \ / _` / __|
   / ___ \ (_| |  __/ | | | |_   ___) | (_) | |_| | | | | (_| \__ \
  /_/   \_\__, |\___|_| |_|\__| |____/ \___/ \__,_|_| |_|\__,_|___/
          |___/
ART
printf "${RESET}"
echo ""
printf "  ${NEON_MAGENTA}${BOLD}Sound effects for Claude Code${RESET}\n"
echo ""

# Progress bar
printf "  ${DIM}Installing sound packs${RESET} "
for i in $(seq 1 25); do
  printf "${NEON_GREEN}█${RESET}"
  sleep 0.02
done
printf " ${NEON_GREEN}${BOLD}done${RESET}\n"
echo ""

# Sound packs summary
printf "  ${NEON_WHITE}${BOLD}4 packs installed:${RESET}\n"
echo ""
printf "  ${NEON_CYAN}●${RESET} ${BOLD}terminal-hacker${RESET}   ${DIM}Sci-fi hacking vibes${RESET}\n"
printf "  ${NEON_MAGENTA}●${RESET} ${BOLD}retro-synth${RESET}       ${DIM}80s synthwave tones${RESET}\n"
printf "  ${NEON_GREEN}●${RESET} ${BOLD}minimal-tones${RESET}     ${DIM}Clean beeps and chimes${RESET}\n"
printf "  ${NEON_PURPLE}●${RESET} ${BOLD}nature-ambient${RESET}    ${DIM}Forest and water sounds${RESET}\n"
echo ""

# Separator
printf "  ${DIM}─────────────────────────────────────────────${RESET}\n"
echo ""

# Quick start
printf "  ${NEON_WHITE}${BOLD}Quick start:${RESET}\n"
echo ""
printf "  ${DIM}\$${RESET} ${NEON_YELLOW}agent-sounds status${RESET}          ${DIM}# current config${RESET}\n"
printf "  ${DIM}\$${RESET} ${NEON_YELLOW}agent-sounds test${RESET}            ${DIM}# hear all sounds${RESET}\n"
printf "  ${DIM}\$${RESET} ${NEON_YELLOW}agent-sounds volume 0.5${RESET}      ${DIM}# set volume${RESET}\n"
printf "  ${DIM}\$${RESET} ${NEON_YELLOW}agent-sounds packs${RESET}           ${DIM}# browse packs${RESET}\n"
echo ""

# Separator
printf "  ${DIM}─────────────────────────────────────────────${RESET}\n"
echo ""

# Clickable hyperlink to theagentmag.com
LINK=$(make_link "https://theagentmag.com/tools/agent-sounds" "theagentmag.com/tools/agent-sounds")
printf "  ${NEON_YELLOW}${BOLD}>>>${RESET}  Browse more packs at ${NEON_PURPLE}${BOLD}${LINK}${RESET}\n"
echo ""

SITE_LINK=$(make_link "https://theagentmag.com" "theagentmag.com")
printf "  ${DIM}Built by${RESET} ${NEON_CYAN}${BOLD}Agent Mag${RESET} ${DIM}—${RESET} ${NEON_PURPLE}${SITE_LINK}${RESET}\n"
echo ""

# Play welcome sound on macOS
if command -v afplay &>/dev/null; then
  WELCOME="$SCRIPT_DIR/../sounds/minimal-tones/bell-01.wav"
  [[ -f "$WELCOME" ]] && afplay -v 0.3 "$WELCOME" &>/dev/null &
fi
