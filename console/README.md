# FreightHero Watchtower Console

A production-grade operational console for FreightHero's Watchtower agent system. Built with React 19, TypeScript, and MUI 9 with a dark theme inspired by Datadog, LangSmith, and Grafana.

## Features

- **Dashboard** — Real-time overview of loads, agents, and system health
- **Load Details** — Drill into individual loads with events, agent runs, and memory tabs
- **Agent Execution Viewer** — Inspect agent decisions, tool calls, and memory operations
- **Workflow Visualizer** — Interactive execution graph using React Flow
- **Memory Explorer** — Browse and search STM, LTM, semantic, procedural, and episodic memories
- **Tool Call Explorer** — Inspect tool names, inputs, outputs, and latency
- **Trace Explorer** — LangSmith-style full execution tree viewer
- **Agent Debugger** — Step-by-step replay with state, memory, decision, and tool inspection
- **Monitoring** — ECharts dashboards for agent runs, memory ops, and error rates

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 19 + TypeScript 6 |
| Build | Vite 8 |
| UI Library | MUI 9 (Material UI) |
| Styling | Tailwind CSS 4 + CSS Variables |
| State | Zustand 5 (client) + TanStack Query 5 (server) |
| Routing | React Router 7 |
| Charts | ECharts 6 + echarts-for-react |
| Flow | @xyflow/react 12 |
| Testing | Vitest 4 + @testing-library/react + MSW 2 |

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm run test

# Run tests with coverage
npm run test:coverage

# Build for production
npm run build
```

## Project Structure

```
src/
├── api/
│   ├── client.ts          # API client with typed endpoints
│   └── mockData.ts        # Mock data for development
├── components/
│   ├── layout/
│   │   ├── AppHeader.tsx  # Top navigation bar
│   │   ├── AppLayout.tsx  # Main layout with sidebar
│   │   └── AppSidebar.tsx # Navigation sidebar
│   └── shared/
│       └── index.tsx       # StatCard, StatusChip, StateChip, SectionHeader, EmptyState
├── screens/
│   ├── Dashboard.tsx      # Operations dashboard
│   ├── LoadDetail.tsx      # Load list + detail views
│   ├── AgentViewer.tsx     # Agent execution viewer + run detail
│   ├── WorkflowVisualizer.tsx # React Flow workflow graph
│   ├── MemoryExplorer.tsx # Memory browser with filters
│   ├── ToolCallExplorer.tsx   # Tool call inspector
│   ├── TraceExplorer.tsx  # Execution tree viewer
│   ├── AgentDebugger.tsx  # Step-by-step replay debugger
│   └── Monitoring.tsx      # ECharts monitoring dashboards
├── stores/
│   └── index.ts           # Zustand stores (dashboard, load, agent, memory, sidebar)
├── theme/
│   └── index.ts           # Dark theme config + color maps
├── types/
│   └── index.ts           # TypeScript type definitions
├── test/
│   ├── setup.ts           # Test setup (mocks for IntersectionObserver, etc.)
│   └── utils.tsx          # renderWithProviders helper
└── App.tsx                # Root component with routing
```

## Test Coverage

| Metric | Threshold | Current |
|--------|-----------|---------|
| Statements | 80% | ~87% |
| Branches | 65% | ~67% |
| Functions | 80% | ~83% |
| Lines | 80% | ~86% |

## API Integration

The console connects to the FreightHero Watchtower backend at `/api/v1`. In development, Vite proxies API requests to `localhost:8000`. The API client supports:

- **Loads**: CRUD operations and state transitions
- **Events**: Task submission, inbound communication, tracking, load updates
- **Monitoring**: Dashboard stats, agent runs, memory metrics, failures
- **Debugger**: Agent run inspection, load history, memory state management, workflow testing
- **Health**: System health checks

## Theme

The dark theme uses CSS variables for consistent styling:

- `--bg-primary`: `#0a0e17` — Main background
- `--bg-secondary`: `#111827` — Sidebar/secondary background
- `--bg-card`: `#1a2235` — Card background
- `--accent-blue`: `#3b82f6` — Primary accent color

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
