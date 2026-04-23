#!/usr/bin/env python3
"""Generate royalty-free sound packs using pure waveform synthesis.
No dependencies beyond Python stdlib. Outputs WAV files."""

import wave
import struct
import math
import os
import random

SAMPLE_RATE = 44100
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sounds")


def write_wav(filename, samples, sample_rate=SAMPLE_RATE):
    with wave.open(filename, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            f.writeframes(struct.pack("<h", int(clamped * 32767)))


def sine(freq, duration, volume=0.5, fade_in=0.01, fade_out=0.05):
    n = int(SAMPLE_RATE * duration)
    fade_in_n = int(SAMPLE_RATE * fade_in)
    fade_out_n = int(SAMPLE_RATE * fade_out)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 1.0
        if i < fade_in_n:
            env = i / fade_in_n
        elif i > n - fade_out_n:
            env = (n - i) / fade_out_n
        samples.append(volume * env * math.sin(2 * math.pi * freq * t))
    return samples


def square(freq, duration, volume=0.3, fade_in=0.01, fade_out=0.05):
    n = int(SAMPLE_RATE * duration)
    fade_in_n = int(SAMPLE_RATE * fade_in)
    fade_out_n = int(SAMPLE_RATE * fade_out)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 1.0
        if i < fade_in_n:
            env = i / fade_in_n
        elif i > n - fade_out_n:
            env = (n - i) / fade_out_n
        val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        samples.append(volume * env * val)
    return samples


def noise_burst(duration, volume=0.2, fade_out=0.05):
    n = int(SAMPLE_RATE * duration)
    fade_out_n = int(SAMPLE_RATE * fade_out)
    samples = []
    for i in range(n):
        env = 1.0
        if i > n - fade_out_n:
            env = (n - i) / fade_out_n
        samples.append(volume * env * (random.random() * 2 - 1))
    return samples


def sweep(start_freq, end_freq, duration, volume=0.4, fade_in=0.01, fade_out=0.05):
    n = int(SAMPLE_RATE * duration)
    fade_in_n = int(SAMPLE_RATE * fade_in)
    fade_out_n = int(SAMPLE_RATE * fade_out)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        freq = start_freq + (end_freq - start_freq) * progress
        env = 1.0
        if i < fade_in_n:
            env = i / fade_in_n
        elif i > n - fade_out_n:
            env = (n - i) / fade_out_n
        samples.append(volume * env * math.sin(2 * math.pi * freq * t))
    return samples


def chord(freqs, duration, volume=0.3, fade_in=0.02, fade_out=0.1):
    n = int(SAMPLE_RATE * duration)
    fade_in_n = int(SAMPLE_RATE * fade_in)
    fade_out_n = int(SAMPLE_RATE * fade_out)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 1.0
        if i < fade_in_n:
            env = i / fade_in_n
        elif i > n - fade_out_n:
            env = (n - i) / fade_out_n
        val = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
        samples.append(volume * env * val)
    return samples


def silence(duration):
    return [0.0] * int(SAMPLE_RATE * duration)


def mix(tracks):
    max_len = max(len(t) for t in tracks)
    result = [0.0] * max_len
    for track in tracks:
        for i, s in enumerate(track):
            result[i] += s
    peak = max(abs(s) for s in result) or 1.0
    if peak > 0.95:
        result = [s / peak * 0.9 for s in result]
    return result


# ── Terminal Hacker Pack ─────────────────────────────────────

def gen_terminal_hacker():
    pack_dir = os.path.join(ROOT, "terminal-hacker")

    # ready: boot sequence — ascending sweep + digital confirmation
    write_wav(os.path.join(pack_dir, "boot-01.wav"),
              mix([sweep(200, 1200, 0.3, 0.35), silence(0.3) + sine(880, 0.15, 0.4) + silence(0.05) + sine(1100, 0.2, 0.4)]))
    write_wav(os.path.join(pack_dir, "boot-02.wav"),
              mix([sweep(150, 800, 0.25, 0.3), silence(0.25) + chord([660, 880, 1100], 0.3, 0.35)]))
    write_wav(os.path.join(pack_dir, "boot-03.wav"),
              sine(440, 0.1, 0.3) + silence(0.05) + sine(660, 0.1, 0.3) + silence(0.05) + sine(880, 0.2, 0.4))

    # work: keypress/data stream — short blips
    write_wav(os.path.join(pack_dir, "data-01.wav"), sine(1000, 0.08, 0.3) + silence(0.02) + sine(1200, 0.06, 0.25))
    write_wav(os.path.join(pack_dir, "data-02.wav"), square(800, 0.06, 0.2) + silence(0.02) + square(1000, 0.06, 0.2))
    write_wav(os.path.join(pack_dir, "data-03.wav"), sweep(600, 1400, 0.12, 0.25))

    # done: success chime — descending resolution
    write_wav(os.path.join(pack_dir, "success-01.wav"),
              sine(1200, 0.12, 0.35) + silence(0.03) + sine(1400, 0.12, 0.35) + silence(0.03) + chord([880, 1100, 1320], 0.3, 0.4))
    write_wav(os.path.join(pack_dir, "success-02.wav"),
              chord([660, 990, 1320], 0.15, 0.3) + silence(0.05) + chord([880, 1100, 1320], 0.35, 0.4))

    # ask: alert — attention-getting pulse
    write_wav(os.path.join(pack_dir, "alert-01.wav"),
              sine(880, 0.1, 0.35) + silence(0.08) + sine(880, 0.1, 0.35) + silence(0.08) + sine(1100, 0.15, 0.4))
    write_wav(os.path.join(pack_dir, "alert-02.wav"),
              square(660, 0.08, 0.25) + silence(0.06) + square(660, 0.08, 0.25) + silence(0.06) + square(880, 0.12, 0.3))

    print("  terminal-hacker: 10 sounds generated")


# ── Retro Synth Pack ─────────────────────────────────────────

def gen_retro_synth():
    pack_dir = os.path.join(ROOT, "retro-synth")

    # ready: warm synth pad startup
    write_wav(os.path.join(pack_dir, "pad-01.wav"),
              chord([220, 330, 440], 0.6, 0.35, fade_in=0.1, fade_out=0.2))
    write_wav(os.path.join(pack_dir, "pad-02.wav"),
              chord([261, 329, 392], 0.5, 0.35, fade_in=0.08, fade_out=0.15))
    write_wav(os.path.join(pack_dir, "pad-03.wav"),
              sweep(110, 440, 0.4, 0.3) + chord([440, 550, 660], 0.3, 0.35))

    # work: arpeggiated blip
    write_wav(os.path.join(pack_dir, "arp-01.wav"),
              sine(330, 0.06, 0.3) + sine(440, 0.06, 0.3) + sine(550, 0.08, 0.3))
    write_wav(os.path.join(pack_dir, "arp-02.wav"),
              sine(440, 0.05, 0.25) + sine(550, 0.05, 0.25) + sine(660, 0.07, 0.3))
    write_wav(os.path.join(pack_dir, "arp-03.wav"),
              square(220, 0.06, 0.2) + square(330, 0.06, 0.2) + square(440, 0.08, 0.25))

    # done: warm resolution chord
    write_wav(os.path.join(pack_dir, "resolve-01.wav"),
              chord([330, 415, 494, 660], 0.5, 0.35, fade_in=0.02, fade_out=0.2))
    write_wav(os.path.join(pack_dir, "resolve-02.wav"),
              chord([440, 550, 660, 880], 0.45, 0.35, fade_in=0.02, fade_out=0.15))

    # ask: synth question — rising tone
    write_wav(os.path.join(pack_dir, "question-01.wav"),
              sweep(330, 660, 0.2, 0.3) + silence(0.05) + sweep(330, 660, 0.2, 0.35))
    write_wav(os.path.join(pack_dir, "question-02.wav"),
              sweep(440, 880, 0.25, 0.3))

    print("  retro-synth: 10 sounds generated")


# ── Minimal Tones Pack ───────────────────────────────────────

def gen_minimal_tones():
    pack_dir = os.path.join(ROOT, "minimal-tones")

    # ready: clean single bell
    write_wav(os.path.join(pack_dir, "bell-01.wav"), sine(880, 0.3, 0.35, fade_out=0.15))
    write_wav(os.path.join(pack_dir, "bell-02.wav"), sine(1046, 0.25, 0.3, fade_out=0.12))

    # work: subtle tick
    write_wav(os.path.join(pack_dir, "tick-01.wav"), sine(1200, 0.04, 0.25))
    write_wav(os.path.join(pack_dir, "tick-02.wav"), sine(1000, 0.05, 0.2))
    write_wav(os.path.join(pack_dir, "tick-03.wav"), sine(1400, 0.03, 0.2))

    # done: two-note completion
    write_wav(os.path.join(pack_dir, "done-01.wav"), sine(660, 0.1, 0.3) + silence(0.04) + sine(880, 0.15, 0.35))
    write_wav(os.path.join(pack_dir, "done-02.wav"), sine(784, 0.1, 0.3) + silence(0.04) + sine(1046, 0.15, 0.35))

    # ask: gentle double tap
    write_wav(os.path.join(pack_dir, "tap-01.wav"), sine(800, 0.06, 0.25) + silence(0.06) + sine(800, 0.06, 0.25))
    write_wav(os.path.join(pack_dir, "tap-02.wav"), sine(900, 0.05, 0.2) + silence(0.08) + sine(900, 0.05, 0.2))

    print("  minimal-tones: 9 sounds generated")


# ── Nature Ambient Pack ──────────────────────────────────────

def gen_nature_ambient():
    pack_dir = os.path.join(ROOT, "nature-ambient")

    # ready: wind chime — layered high-freq sines with slow fade
    write_wav(os.path.join(pack_dir, "chime-01.wav"),
              mix([sine(1568, 0.4, 0.2, fade_out=0.25), sine(2093, 0.35, 0.15, fade_out=0.2), sine(2637, 0.3, 0.1, fade_out=0.15)]))
    write_wav(os.path.join(pack_dir, "chime-02.wav"),
              mix([sine(1318, 0.45, 0.2, fade_out=0.3), sine(1760, 0.4, 0.15, fade_out=0.25), sine(2349, 0.35, 0.1, fade_out=0.2)]))

    # work: water drop — quick descending blip
    write_wav(os.path.join(pack_dir, "drop-01.wav"), sweep(2000, 400, 0.08, 0.25))
    write_wav(os.path.join(pack_dir, "drop-02.wav"), sweep(1800, 350, 0.1, 0.2))
    write_wav(os.path.join(pack_dir, "drop-03.wav"), sweep(2200, 500, 0.07, 0.22))

    # done: gentle bell bowl — rich low chord with long fade
    write_wav(os.path.join(pack_dir, "bowl-01.wav"),
              chord([396, 528, 660], 0.7, 0.3, fade_in=0.02, fade_out=0.4))
    write_wav(os.path.join(pack_dir, "bowl-02.wav"),
              chord([352, 440, 528], 0.65, 0.3, fade_in=0.02, fade_out=0.35))

    # ask: bird chirp — quick rising sweep
    write_wav(os.path.join(pack_dir, "chirp-01.wav"),
              sweep(1500, 3000, 0.06, 0.2) + silence(0.04) + sweep(1800, 3200, 0.05, 0.18))
    write_wav(os.path.join(pack_dir, "chirp-02.wav"),
              sweep(2000, 3500, 0.05, 0.18) + silence(0.05) + sweep(2200, 3800, 0.04, 0.15))

    print("  nature-ambient: 9 sounds generated")


if __name__ == "__main__":
    random.seed(42)
    print("\nGenerating sound packs...\n")
    gen_terminal_hacker()
    gen_retro_synth()
    gen_minimal_tones()
    gen_nature_ambient()
    print(f"\nDone! 38 sounds generated in {ROOT}\n")
