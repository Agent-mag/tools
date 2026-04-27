# Dot Matrix Icons

Animated 5x5 SVG loaders for agent interfaces, product tools, status states, and compact dashboards.

This is the open-source source package behind:

- `https://dotmatrix.theagentmag.com`
- `https://theagentmag.com/tools/dotmatrix`
- `npx agentmag add tool dotmatrix-icons`

## Install From Agent Mag CLI

```bash
npx agentmag add tool dotmatrix-icons
```

The CLI writes a local React bundle into `components/dotmatrix/`:

```txt
components/dotmatrix/
  registry.ts
  dotmatrix-icon.tsx
  dotmatrix.css
  index.ts
  README.md
```

## Usage

```tsx
import "@/components/dotmatrix/dotmatrix.css"
import { DotMatrixIcon } from "@/components/dotmatrix"

export function ToolCallLoader() {
  return <DotMatrixIcon pattern="agent-thinking" size={40} color="currentColor" />
}
```

## What Is Included

- 72 animated 5x5 dot-matrix loaders
- Spinner, progress, ambient, agent, and status categories
- Copyable SVG output on the Agent Mag microsite
- React component, CSS keyframes, and registry data
- Pause, tint, speed, and density controls on the web surface

## License

MIT. See the repository root license.
