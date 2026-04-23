# Agent Sounds

**Sound effects for Claude Code sessions.** Hear audio cues when tasks start, complete, or need your attention.

4 original sound packs. Zero copyrighted audio. Works on macOS, Linux, and Windows.

---

## Install

**Via Claude Code plugin marketplace:**

```bash
claude plugin install sounds@Agent-mag
```

**Via npm (global):**

```bash
npm install -g @agentmag/sounds
```

**Via agentmag CLI:**

```bash
npx agentmag add tool claude-sounds
```

---

## How It Works

Agent Sounds hooks into Claude Code's lifecycle events and plays a random sound from your enabled packs:

| Event | When | Sound |
|-------|------|-------|
| **Session Start** | You open Claude Code | Boot / greeting |
| **Prompt Submit** | You send a message | Acknowledgment blip |
| **Subagent Start** | A subagent spawns | Work sound |
| **Plan Mode** | Enter/exit plan mode | Work / done |
| **Task Complete** | Claude finishes | Success chime |
| **Permission Request** | Claude needs approval | Alert / attention |

All sounds play in the background — they never block Claude Code.

---

## Sound Packs

### terminal-hacker
Sci-fi hacking vibes — boot sequences, data streams, digital alerts. Think command-line in a movie hacking scene.

### retro-synth
80s synthwave tones — warm pads, arpeggios, analog warmth. Nostalgic and smooth.

### minimal-tones
Clean beeps and chimes — subtle, professional, non-distracting. For focused work sessions.

### nature-ambient
Forest and water sounds — wind chimes, water drops, bird chirps. Calming vibes for long sessions.

All packs are enabled by default. Mix and match to your preference.

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
agent-sounds test ready          # Play a specific event sound
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

## Requirements

- **Python 3** (for JSON parsing in shell scripts)
- **Audio player** (auto-detected per platform):
  - macOS: `afplay` (built-in)
  - Linux: `pw-play`, `paplay`, or `ffplay`
  - Windows: `ffplay` or PowerShell MediaPlayer

---

## How Claude Code Sounds Work

Claude Code supports [hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) — shell commands that execute on lifecycle events. Agent Sounds registers hooks for 7 events (SessionStart, UserPromptSubmit, SubagentStart, PreToolUse, PostToolUse, Stop, PermissionRequest) that trigger `play.sh`, which:

1. Reads your config (enabled packs, volume, muted state)
2. Collects matching audio files from all enabled packs
3. Picks one at random
4. Plays it in the background via your OS audio player

The entire plugin is bash scripts + audio files. No Node.js runtime, no heavy dependencies.

---

## Comparison

| Feature | Agent Sounds | claude-sounds |
|---------|-------------|---------------|
| Sound packs | 4 original (royalty-free) | 4 (copyrighted game audio) |
| Custom packs | Yes | Yes |
| Cross-platform | macOS, Linux, Windows | macOS, Linux, Windows |
| CLI management | Full CLI with neon UI | Full CLI |
| Copyrighted audio | No (all original) | Yes (Warcraft, Dota 2, RA2) |
| Install via agentmag | `npx agentmag add tool claude-sounds` | No |
| Branded postinstall | Yes | No |
| License | MIT | MIT (code) / Non-commercial (audio) |

---

## Links

- **Website:** [theagentmag.com/tools/agent-sounds](https://theagentmag.com/tools/agent-sounds)
- **npm:** [@agentmag/sounds](https://www.npmjs.com/package/@agentmag/sounds)
- **GitHub:** [Agent-mag/agent-sounds](https://github.com/Agent-mag/agent-sounds)
- **Agent Mag:** [theagentmag.com](https://theagentmag.com)

---

## License

MIT License. All sound files are original, royalty-free waveform synthesis — no copyrighted audio.

Built by [Agent Mag](https://theagentmag.com) — the AI agent magazine.
