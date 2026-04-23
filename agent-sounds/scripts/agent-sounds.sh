#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CONFIG="$ROOT/config.json"

source "$SCRIPT_DIR/colors.sh"

VERSION="1.0.0"

read_config() {
  python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
print(c.get('muted', False))
print(c.get('volume', 0.25))
print(','.join(c.get('enabled', [])))
" 2>/dev/null
}

write_enabled() {
  local enabled="$1"
  python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
c['enabled'] = '$enabled'.split(',') if '$enabled' else []
with open('$CONFIG', 'w') as f:
    json.dump(c, f, indent=2)
    f.write('\n')
"
}

write_volume() {
  local vol="$1"
  python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
c['volume'] = $vol
with open('$CONFIG', 'w') as f:
    json.dump(c, f, indent=2)
    f.write('\n')
"
}

write_muted() {
  local muted="$1"
  python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
c['muted'] = $muted
with open('$CONFIG', 'w') as f:
    json.dump(c, f, indent=2)
    f.write('\n')
"
}

get_packs() {
  local packs=()
  for dir in "$ROOT/sounds"/*/; do
    [ -f "$dir/source.json" ] && packs+=("$(basename "$dir")")
  done
  echo "${packs[@]}"
}

cmd_status() {
  local config
  config=$(read_config)
  local muted volume enabled_str
  muted=$(echo "$config" | sed -n '1p')
  volume=$(echo "$config" | sed -n '2p')
  enabled_str=$(echo "$config" | sed -n '3p')

  echo ""
  printf "  ${NEON_CYAN}${BOLD}Agent Sounds${RESET} ${DIM}v${VERSION}${RESET}\n"
  echo ""

  if [ "$muted" = "True" ]; then
    printf "  ${DIM}Status${RESET}   ${NEON_ORANGE}muted${RESET}\n"
  else
    printf "  ${DIM}Status${RESET}   ${NEON_GREEN}active${RESET}\n"
  fi

  printf "  ${DIM}Volume${RESET}   ${NEON_WHITE}${volume}${RESET}\n"
  printf "  ${DIM}Root${RESET}     ${DIM}${ROOT}${RESET}\n"
  echo ""

  printf "  ${DIM}Enabled packs:${RESET}\n"
  IFS=',' read -ra enabled_arr <<< "$enabled_str"
  for pack in $(get_packs); do
    local is_enabled=false
    for e in "${enabled_arr[@]}"; do
      [ "$e" = "$pack" ] && is_enabled=true
    done
    if $is_enabled; then
      printf "    ${NEON_GREEN}●${RESET} ${NEON_WHITE}${pack}${RESET}\n"
    else
      printf "    ${DIM}○ ${pack}${RESET}\n"
    fi
  done
  echo ""
}

cmd_packs() {
  echo ""
  printf "  ${NEON_CYAN}${BOLD}Sound Packs${RESET}\n"
  echo ""

  local config
  config=$(read_config)
  local enabled_str
  enabled_str=$(echo "$config" | sed -n '3p')

  for pack in $(get_packs); do
    local is_enabled=false
    IFS=',' read -ra enabled_arr <<< "$enabled_str"
    for e in "${enabled_arr[@]}"; do
      [ "$e" = "$pack" ] && is_enabled=true
    done

    if $is_enabled; then
      printf "  ${NEON_GREEN}●${RESET} ${NEON_WHITE}${BOLD}${pack}${RESET}\n"
    else
      printf "  ${DIM}○ ${pack}${RESET}\n"
    fi

    local desc
    desc=$(python3 -c "
descs = {
    'terminal-hacker': 'Sci-fi hacking vibes — boot sequences, data streams, digital alerts',
    'retro-synth': '80s synthwave tones — warm pads, arpeggios, analog warmth',
    'minimal-tones': 'Clean beeps and chimes — subtle, professional, non-distracting',
    'nature-ambient': 'Forest and water sounds — wind chimes, water drops, bird chirps',
}
import json
pack = '$pack'
print(descs.get(pack, 'Custom sound pack'))
with open('$ROOT/sounds/$pack/source.json') as f:
    d = json.load(f)
print(sum(len(v) for v in d.values()))
" 2>/dev/null)
    local pack_desc pack_count
    pack_desc=$(echo "$desc" | sed -n '1p')
    pack_count=$(echo "$desc" | sed -n '2p')
    printf "    ${DIM}${pack_desc}${RESET}\n"
    printf "    ${DIM}${pack_count} sounds${RESET}\n"
    echo ""
  done
}

cmd_enable() {
  local pack="$1"
  if [ "$pack" = "all" ]; then
    local all_packs
    all_packs=$(get_packs | tr ' ' ',')
    write_enabled "$all_packs"
    printf "  ${NEON_GREEN}●${RESET} All packs enabled\n"
    return
  fi

  if [ ! -d "$ROOT/sounds/$pack" ]; then
    printf "  ${NEON_ORANGE}!${RESET} Pack '${pack}' not found. Run ${DIM}agent-sounds packs${RESET} to see available packs.\n"
    return 1
  fi

  local config enabled_str
  config=$(read_config)
  enabled_str=$(echo "$config" | sed -n '3p')

  if echo "$enabled_str" | grep -q "$pack"; then
    printf "  ${DIM}${pack} is already enabled${RESET}\n"
    return
  fi

  if [ -z "$enabled_str" ]; then
    write_enabled "$pack"
  else
    write_enabled "${enabled_str},${pack}"
  fi
  printf "  ${NEON_GREEN}●${RESET} Enabled ${NEON_WHITE}${pack}${RESET}\n"
}

cmd_disable() {
  local pack="$1"
  if [ "$pack" = "all" ]; then
    write_enabled ""
    printf "  ${DIM}○ All packs disabled${RESET}\n"
    return
  fi

  local config enabled_str
  config=$(read_config)
  enabled_str=$(echo "$config" | sed -n '3p')

  local new_enabled
  new_enabled=$(echo "$enabled_str" | tr ',' '\n' | grep -v "^${pack}$" | tr '\n' ',' | sed 's/,$//')
  write_enabled "$new_enabled"
  printf "  ${DIM}○ Disabled ${pack}${RESET}\n"
}

cmd_volume() {
  local vol="$1"
  if [ -z "$vol" ]; then
    local config
    config=$(read_config)
    local current
    current=$(echo "$config" | sed -n '2p')
    printf "  ${DIM}Volume:${RESET} ${NEON_WHITE}${current}${RESET}\n"
    return
  fi

  if ! python3 -c "v=float('$vol'); assert 0<=v<=1" 2>/dev/null; then
    printf "  ${NEON_ORANGE}!${RESET} Volume must be between 0.0 and 1.0\n"
    return 1
  fi

  write_volume "$vol"
  printf "  ${NEON_GREEN}●${RESET} Volume set to ${NEON_WHITE}${vol}${RESET}\n"
}

cmd_mute() {
  write_muted "True"
  printf "  ${DIM}○ Sounds muted${RESET}\n"
}

cmd_unmute() {
  write_muted "False"
  printf "  ${NEON_GREEN}●${RESET} Sounds unmuted\n"
}

cmd_test() {
  local event="${1:-all}"

  if [ "$event" = "all" ]; then
    echo ""
    printf "  ${NEON_CYAN}${BOLD}Testing all events...${RESET}\n"
    echo ""
    for e in ready work done ask; do
      printf "  ${NEON_YELLOW}▶${RESET} ${e}\n"
      bash "$SCRIPT_DIR/play.sh" "$e"
      sleep 1.5
    done
    echo ""
    printf "  ${NEON_GREEN}●${RESET} Done\n"
    echo ""
  else
    case "$event" in
      ready|work|done|ask)
        printf "  ${NEON_YELLOW}▶${RESET} ${event}\n"
        bash "$SCRIPT_DIR/play.sh" "$event"
        ;;
      *)
        printf "  ${NEON_ORANGE}!${RESET} Unknown event: ${event}. Use: ready, work, done, ask\n"
        return 1
        ;;
    esac
  fi
}

cmd_reset() {
  cat > "$CONFIG" << 'CONF'
{
  "enabled": ["terminal-hacker", "retro-synth", "minimal-tones", "nature-ambient"],
  "volume": 0.25,
  "muted": false
}
CONF
  printf "  ${NEON_GREEN}●${RESET} Config reset to defaults\n"
}

cmd_help() {
  echo ""
  printf "  ${NEON_CYAN}${BOLD}Agent Sounds${RESET} ${DIM}v${VERSION}${RESET}\n"
  printf "  ${DIM}Sound effects for Claude Code sessions${RESET}\n"
  echo ""
  printf "  ${NEON_WHITE}${BOLD}Usage:${RESET} agent-sounds <command> [options]\n"
  echo ""
  printf "  ${NEON_WHITE}Commands:${RESET}\n"
  printf "    ${NEON_CYAN}status${RESET}            Show current config\n"
  printf "    ${NEON_CYAN}packs${RESET}             List available sound packs\n"
  printf "    ${NEON_CYAN}enable${RESET}  <pack>    Enable a sound pack\n"
  printf "    ${NEON_CYAN}disable${RESET} <pack>    Disable a sound pack\n"
  printf "    ${NEON_CYAN}volume${RESET}  [0-1]     Get or set volume\n"
  printf "    ${NEON_CYAN}mute${RESET}              Mute all sounds\n"
  printf "    ${NEON_CYAN}unmute${RESET}            Unmute all sounds\n"
  printf "    ${NEON_CYAN}test${RESET}    [event]   Play a test sound (ready|work|done|ask|all)\n"
  printf "    ${NEON_CYAN}reset${RESET}             Reset config to defaults\n"
  printf "    ${NEON_CYAN}version${RESET}           Show version\n"
  printf "    ${NEON_CYAN}help${RESET}              Show this help\n"
  echo ""

  local LINK
  LINK=$(make_link "https://theagentmag.com/tools/agent-sounds" "theagentmag.com/tools/agent-sounds")
  printf "  ${DIM}More at${RESET} ${NEON_PURPLE}${LINK}${RESET}\n"
  echo ""
}

# ── Main ─────────────────────────────────────────────────────

CMD="${1:-help}"
ARG="${2:-}"

case "$CMD" in
  status)      cmd_status ;;
  packs|sounds|list) cmd_packs ;;
  enable)      cmd_enable "${ARG:?Pack name required. Usage: agent-sounds enable <pack>}" ;;
  disable)     cmd_disable "${ARG:?Pack name required. Usage: agent-sounds disable <pack>}" ;;
  volume)      cmd_volume "$ARG" ;;
  mute|off)    cmd_mute ;;
  unmute|on)   cmd_unmute ;;
  test|play)   cmd_test "$ARG" ;;
  reset)       cmd_reset ;;
  version|-v|--version) echo "agent-sounds v${VERSION}" ;;
  help|-h|--help) cmd_help ;;
  *)
    printf "  ${NEON_ORANGE}!${RESET} Unknown command: ${CMD}\n"
    printf "  ${DIM}Run agent-sounds help for usage${RESET}\n"
    exit 1
    ;;
esac
