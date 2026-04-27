"use client"

import * as React from "react"
import { dotMatrixPatterns, getDotMatrixPattern, gridCells, type DotMatrixPattern } from "./patterns"

export type { DotMatrixCategory, DotMatrixMotion, DotMatrixPattern } from "./patterns"
export { dotMatrixPatterns, getDotMatrixPattern }

export interface DotMatrixIconProps extends Omit<React.SVGProps<SVGSVGElement>, "color"> {
  pattern?: string | DotMatrixPattern
  size?: number
  color?: string
  speed?: number
  paused?: boolean
  dotRadius?: number
}

export function DotMatrixIcon({
  pattern = "agent-thinking",
  size = 48,
  color = "currentColor",
  speed = 1,
  paused = false,
  dotRadius = 4.6,
  className,
  style,
  "aria-label": ariaLabel,
  ...props
}: DotMatrixIconProps) {
  const resolvedPattern = typeof pattern === "string" ? getDotMatrixPattern(pattern) : pattern
  const duration = Math.max(240, Math.round(resolvedPattern.durationMs / Math.max(0.2, speed)))

  return (
    <svg
      viewBox="0 0 96 96"
      width={size}
      height={size}
      role="img"
      aria-label={ariaLabel || resolvedPattern.name}
      data-motion={resolvedPattern.motion}
      className={["dotmatrix-icon", className].filter(Boolean).join(" ")}
      style={{
        color,
        "--dotmatrix-duration": `${duration}ms`,
        "--dotmatrix-play-state": paused ? "paused" : "running",
        ...style,
      } as React.CSSProperties}
      {...props}
    >
      {gridCells.map((cell) => (
        <circle
          key={`base-${cell.x}-${cell.y}`}
          data-dot-bg=""
          cx={12 + cell.x * 18}
          cy={12 + cell.y * 18}
          r={dotRadius}
          fill="currentColor"
        />
      ))}
      {resolvedPattern.cells.map((cell) => (
        <circle
          key={`${cell.x}-${cell.y}`}
          data-dot=""
          cx={12 + cell.x * 18}
          cy={12 + cell.y * 18}
          r={dotRadius}
          fill="currentColor"
          opacity={cell.opacity}
          style={{
            "--dotmatrix-delay": `${Math.round(cell.delay * duration)}ms`,
            "--dotmatrix-dot-scale": cell.scale ?? 1,
          } as React.CSSProperties}
        />
      ))}
    </svg>
  )
}
