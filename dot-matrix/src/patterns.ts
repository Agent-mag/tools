export type DotMatrixCategory = "spinner" | "progress" | "ambient" | "agent" | "status"
export type DotMatrixMotion = "orbit" | "scan" | "wave" | "ripple" | "spark" | "march" | "breathe" | "hold"

export interface DotMatrixCell {
  x: number
  y: number
  opacity: number
  delay: number
  scale?: number
}

export interface DotMatrixPattern {
  id: string
  name: string
  category: DotMatrixCategory
  motion: DotMatrixMotion
  family: "ring" | "line" | "field" | "agent" | "status"
  tags: string[]
  cells: DotMatrixCell[]
  durationMs: number
}

export const gridCells = Array.from({ length: 25 }, (_, index) => ({
  x: index % 5,
  y: Math.floor(index / 5),
}))

type Seed = Omit<DotMatrixPattern, "cells" | "durationMs"> & {
  rows: [string, string, string, string, string]
  durationMs?: number
}

const center = 2
const ordered = gridCells
  .map((cell) => ({ ...cell, weight: Math.hypot(cell.x - center, cell.y - center) }))
  .sort((a, b) => a.weight - b.weight)

function normalize(index: number, length: number) {
  return length <= 1 ? 0 : index / (length - 1)
}

function rowsToCells(rows: Seed["rows"], motion: DotMatrixMotion): DotMatrixCell[] {
  const active = rows.flatMap((row, y) =>
    row.split("").flatMap((value, x) => (value === "1" ? [{ x, y }] : []))
  )

  return active.map((cell, index) => {
    const radial = Math.hypot(cell.x - center, cell.y - center)
    const orderIndex = ordered.findIndex((item) => item.x === cell.x && item.y === cell.y)
    const delay = motion === "ripple" ? normalize(orderIndex, ordered.length) : normalize(index, active.length)

    return {
      ...cell,
      opacity: Math.max(0.64, 1 - radial * 0.1),
      delay,
      scale: 0.82 + Math.max(0, 1 - radial / 3) * 0.24,
    }
  })
}

const seeds: Seed[] = [
  { id: "pulse-rings", name: "Pulse Rings", category: "spinner", family: "ring", motion: "ripple", tags: ["pulse", "ring"], rows: ["00100", "01110", "11111", "01110", "00100"] },
  { id: "corner-orbit", name: "Corner Orbit", category: "spinner", family: "ring", motion: "orbit", tags: ["orbit", "perimeter"], rows: ["11111", "10001", "10001", "10001", "11111"] },
  { id: "spiral-in", name: "Spiral In", category: "spinner", family: "ring", motion: "orbit", tags: ["spiral"], rows: ["11111", "00001", "11101", "10001", "11111"] },
  { id: "cross-expand", name: "Cross Expand", category: "spinner", family: "ring", motion: "ripple", tags: ["cross"], rows: ["00100", "00100", "11111", "00100", "00100"] },
  { id: "diamond-loop", name: "Diamond Loop", category: "spinner", family: "ring", motion: "orbit", tags: ["diamond"], rows: ["00100", "01010", "10001", "01010", "00100"] },
  { id: "column-scan", name: "Column Scan", category: "progress", family: "line", motion: "scan", tags: ["column", "scan"], rows: ["10000", "10000", "10000", "10000", "10000"] },
  { id: "row-scan", name: "Row Scan", category: "progress", family: "line", motion: "march", tags: ["row", "scan"], rows: ["00000", "00000", "11111", "00000", "00000"] },
  { id: "diagonal-scan", name: "Diagonal Scan", category: "progress", family: "line", motion: "scan", tags: ["diagonal"], rows: ["10000", "01000", "00100", "00010", "00001"] },
  { id: "pipeline", name: "Pipeline", category: "progress", family: "line", motion: "march", tags: ["pipeline"], rows: ["11111", "00000", "11111", "00000", "11111"] },
  { id: "stream", name: "Stream", category: "progress", family: "line", motion: "wave", tags: ["stream"], rows: ["10000", "11000", "01110", "00011", "00001"] },
  { id: "sparkle", name: "Sparkle", category: "ambient", family: "field", motion: "spark", tags: ["sparkle"], rows: ["10001", "00100", "01010", "00100", "10001"] },
  { id: "rain", name: "Rain", category: "ambient", family: "field", motion: "wave", tags: ["rain"], rows: ["10101", "01010", "10101", "01010", "10101"] },
  { id: "breathing-grid", name: "Breathing Grid", category: "ambient", family: "field", motion: "breathe", tags: ["grid"], rows: ["11111", "11111", "11111", "11111", "11111"] },
  { id: "typing", name: "Typing", category: "ambient", family: "field", motion: "wave", tags: ["typing"], rows: ["00000", "00000", "01110", "00000", "00000"] },
  { id: "agent-thinking", name: "Agent Thinking", category: "agent", family: "agent", motion: "ripple", tags: ["agent", "thinking"], rows: ["00100", "01110", "11011", "01110", "00100"] },
  { id: "tool-call", name: "Tool Call", category: "agent", family: "agent", motion: "scan", tags: ["agent", "tool"], rows: ["11011", "10001", "00100", "10001", "11011"] },
  { id: "memory-write", name: "Memory Write", category: "agent", family: "agent", motion: "march", tags: ["agent", "memory"], rows: ["11110", "10010", "11110", "10010", "11110"] },
  { id: "retrieval-scan", name: "Retrieval Scan", category: "agent", family: "agent", motion: "orbit", tags: ["agent", "retrieval"], rows: ["00100", "10101", "01110", "10101", "00100"] },
  { id: "verified", name: "Verified", category: "status", family: "status", motion: "hold", tags: ["status", "success"], rows: ["00001", "00010", "10100", "01000", "00000"], durationMs: 2200 },
  { id: "blocked", name: "Blocked", category: "status", family: "status", motion: "breathe", tags: ["status", "blocked"], rows: ["11111", "10001", "10101", "10001", "11111"] },
  { id: "queued", name: "Queued", category: "status", family: "status", motion: "march", tags: ["status", "queued"], rows: ["10000", "11000", "11100", "11000", "10000"] },
  { id: "complete", name: "Complete", category: "status", family: "status", motion: "ripple", tags: ["status", "complete"], rows: ["00100", "01110", "11111", "01110", "00100"] },
]

export const dotMatrixPatterns: DotMatrixPattern[] = seeds.map((seed, index) => ({
  ...seed,
  durationMs: seed.durationMs ?? 980 + ((index * 71) % 640),
  cells: rowsToCells(seed.rows, seed.motion),
}))

export function getDotMatrixPattern(id: string) {
  return dotMatrixPatterns.find((pattern) => pattern.id === id) ?? dotMatrixPatterns[0]!
}
