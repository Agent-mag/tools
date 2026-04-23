<div align="center">

<a href="https://theagentmag.com"><img src="https://raw.githubusercontent.com/Agent-mag/.github/main/profile/agentmag-banner-github.png" alt="Agent Mag" width="100%" /></a>

# Agent Sounds

**Sound effects for Claude Code sessions — hear audio cues when tasks start, complete, or need attention.**

[![npm version](https://img.shields.io/npm/v/@agentmag/sounds?style=for-the-badge&color=000)](https://www.npmjs.com/package/@agentmag/sounds)
[![npm downloads](https://img.shields.io/npm/dw/@agentmag/sounds?style=for-the-badge&color=000)](https://www.npmjs.com/package/@agentmag/sounds)
[![License: MIT](https://img.shields.io/badge/License-MIT-000?style=for-the-badge)](../LICENSE)
[![Agent Mag](https://img.shields.io/badge/by-Agent_Mag-000?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyTDIgMjJoMjBMMTIgMnoiLz48L3N2Zz4=)](https://theagentmag.com)

[Browse Tools](https://theagentmag.com/tools) &nbsp;&middot;&nbsp; [npm](https://www.npmjs.com/package/@agentmag/sounds) &nbsp;&middot;&nbsp; [Website](https://theagentmag.com)

</div>

---

## What It Does

Agent Sounds hooks into Claude Code's lifecycle events and plays audio cues so you know what's happening without watching the terminal.

4 original sound packs. 38 royalty-free sounds. Zero copyrighted audio. Works on macOS, Linux, and Windows.

| Event | When It Fires | Sound |
|-------|--------------|-------|
| **Session Start** | You open Claude Code | Boot / greeting chime |
| **Prompt Submit** | You send a message | Acknowledgment blip |
| **Subagent Start** | A subagent spawns | Work sound |
| **Plan Mode** | Enter / exit plan mode | Work / done |
| **Task Complete** | Claude finishes responding | Success tone |
| **Permission Request** | Claude needs your approval | Alert / attention |

All sounds play in the background — they never block Claude Code.

---

## Quick Start

### Option A: One command (via agentmag CLI)

```bash
npx agentmag add tool claude-sounds
```

### Option B: npm global install

```bash
npm install -g @agentmag/sounds
```

### Option C: Claude Code plugin marketplace

```bash
claude plugin install sounds@Agent-mag
```

---

## Sound Packs

| Pack | Vibe | Sounds |
|------|------|--------|
| **terminal-hacker** | Sci-fi hacking — boot sequences, data streams, digital alerts | 10 |
| **retro-synth** | 80s synthwave — warm pads, arpeggios, analog warmth | 10 |
| **minimal-tones** | Clean beeps and chimes — subtle, professional, non-distracting | 9 |
| **nature-ambient** | Forest and water — wind chimes, water drops, bird chirps | 9 |

All packs are enabled by default. Mix and match to your preference.

All sounds are generated via Python waveform synthesis (sine waves, square waves, envelope shaping) — no copyrighted game audio, no licensing issues.

---

## CLI Commands

```bash
agent-sounds status              # Show current config
agent-sounds packs               # List available sound packs
agent-sounds enable <pack>       # Enable a sound pack
agent-sounds disable <pack>      # Disable a sound pack
agent-sounds volume 0.5          # Set volume (0.0 to 1.0)
agent-sounds mute                # Mute all sounds
agent-sounds unmute              # Unmute all sounds
agent-sounds test                # Play all event sounds
agent-sounds test ready          # Play a specific event
agent-sounds reset               # Reset config to defaults
```

---

## Configuration

Config is stored in `config.json` in the package root:

```json
{
  "enabled": ["terminal-hacker", "retro-synth", "minimal-tones", "nature-ambient"],
  "volume": 0.25,
  "muted": false
}
```

---

## Create Custom Sound Packs

1. Create a directory under `sounds/` with your pack name
2. Add audio files (`.wav` or `.mp3`)
3. Create a `source.json` mapping events to files:

```json
{
  "ready": ["my-start-sound.wav"],
  "work": ["working-01.wav", "working-02.wav"],
  "done": ["complete.wav"],
  "ask": ["attention.wav"]
}
```

4. Enable it: `agent-sounds enable my-pack`

---

## How Claude Code Sounds Work

Claude Code supports [hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) — shell commands that execute on lifecycle events. Agent Sounds registers hooks for 7 events that trigger `play.sh`, which:

1. Reads your config (enabled packs, volume, muted state)
2. Collects matching audio files from all enabled packs
3. Picks one at random
4. Plays it in the background via your OS audio player

The entire plugin is bash scripts + audio files. No Node.js runtime, no heavy dependencies.

## Requirements

- **Python 3** — for JSON parsing in shell scripts
- **Audio player** — auto-detected per platform:

| Platform | Player |
|----------|--------|
| macOS | `afplay` (built-in) |
| Linux | `pw-play` → `paplay` → `ffplay` |
| Windows | `ffplay` → PowerShell MediaPlayer |

---

## Comparison

| Feature | Agent Sounds | claude-sounds |
|---------|-------------|---------------|
| Sound packs | 4 original (royalty-free) | 4 (copyrighted game audio) |
| Custom packs | Yes | Yes |
| Cross-platform | macOS, Linux, Windows | macOS, Linux, Windows |
| CLI management | Full CLI with neon UI | Full CLI |
| Copyrighted audio | No — all original | Yes (Warcraft, Dota 2, Red Alert 2) |
| Install via agentmag | `npx agentmag add tool claude-sounds` | No |
| License | MIT (code + audio) | MIT (code) / Non-commercial (audio) |

---

## Inputs

| Config Key | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | `string[]` | All 4 packs | Which sound packs are active |
| `volume` | `number` | `0.25` | Playback volume (0.0 — 1.0) |
| `muted` | `boolean` | `false` | Whether sounds are muted |

---

## License

MIT — see [LICENSE](../LICENSE) for details. All sound files are original, royalty-free waveform synthesis.

---

<div align="center">

**Built by [Agent Mag](https://theagentmag.com)** — the magazine for AI agent builders.

[Website](https://theagentmag.com) &nbsp;&middot;&nbsp; [Tools](https://theagentmag.com/tools) &nbsp;&middot;&nbsp; [Skills](https://theagentmag.com/skills) &nbsp;&middot;&nbsp; [Newsletter](https://theagentmag.com/newsletter) &nbsp;&middot;&nbsp; [GitHub](https://github.com/Agent-mag)

</div>
