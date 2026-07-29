# Frontend Knowledge Explorer Pattern (Phase 9.1)

## Architecture

```
React + Vite + TypeScript SPA
        │  axios
        ▼
FastAPI (applications/api/)
        │  app.state.adapter
        ▼
KnowledgeAgentAdapter
```

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | React 18 + Vite | SPA, no SSR needed |
| Language | TypeScript | Type safety for API contracts |
| HTTP | axios | Simple, promise-based |
| Routing | react-router-dom v6 | Client-side navigation |
| Graph | Cytoscape.js | Zoomable, draggable knowledge graph |
| Styling | Plain CSS + CSS variables | Zero dependency, dark theme |

## Directory Structure

```
frontend/
├── package.json + vite.config.ts
├── index.html
└── src/
    ├── api/
    │   ├── types.ts      ← CardData, StatsData, GraphData, etc.
    │   └── client.ts     ← fetchStats, searchCards, fetchGraph, ...
    ├── components/
    │   ├── StatsPanel.tsx    ← 4-stat overview (cards/relations/tags/domains)
    │   ├── SearchBar.tsx     ← text input + button
    │   ├── CardList.tsx      ← scrollable card list with selection
    │   ├── CardView.tsx      ← card detail (tags, relations, content)
    │   └── RelationGraph.tsx ← Cytoscape.js dynamic import
    ├── pages/
    │   ├── Dashboard.tsx     ← /  (stats + quick actions + recent)
    │   ├── Explorer.tsx      ← /explorer (search + list + detail)
    │   └── GraphPage.tsx     ← /graph (full knowledge graph)
    ├── App.tsx               ← BrowserRouter + NavLinks + Routes
    ├── App.css               ← Dark theme via CSS variables
    └── main.tsx              ← entry
```

## Key Patterns

### API Client Centralization

All HTTP calls go through `src/api/client.ts`. Components NEVER write URLs directly.

```typescript
// src/api/client.ts
const api = axios.create({ baseURL: '/api' });

export async function fetchStats(): Promise<StatsData> { ... }
export async function searchCards(q: string): Promise<SearchResult> { ... }
export async function fetchGraph(domain?: string): Promise<GraphData> { ... }
```

### Cytoscape Dynamic Import

Cytoscape.js is heavy (~200KB). Lazy-load on the graph page only:

```typescript
useEffect(() => {
  import('cytoscape').then(cy => {
    const inst = cy.default({ container, elements, style, layout });
    inst.on('tap', 'node', e => onNodeClick?.(e.target.id()));
    return () => inst.destroy();
  });
}, [data]);
```

### Dark Theme CSS Variables

```css
:root {
  --bg: #0a0a14; --panel: #12122a; --text: #c8c8dc;
  --accent: #6c5ce7; --border: #1e1e3a;
}
```

### Backend /api/graph Endpoint

For the graph view, the backend provides a dedicated endpoint:

```python
# applications/api/routes/graph.py
@router.get("")
def graph(request, domain: str | None = None) -> GraphResponse:
    cards = adapter.engine.list_all(limit=200)
    # Build nodes from cards, edges from relations
    # Optionally filter by domain
    return GraphResponse(nodes=[...], edges=[...])
```

GraphResponse uses Pydantic models (GraphNode, GraphEdge) — never raw dicts.

## Architecture Constraints

1. **Frontend only talks to FastAPI** — no direct markdown file access, no whoosh
2. **API client centralized** — all endpoints called through `src/api/client.ts`
3. **No SSR, no database, no auth** — pure SPA knowledge browser
4. **TypeScript compiles clean** — `tsc --noEmit` passes

## Verification

```bash
cd frontend
npm install
npx tsc --noEmit          # TypeScript check
npx vite build             # Production build → dist/
```

## Common Pitfalls

1. **Cytoscape types**: Install `@types/cytoscape` for TypeScript support. Use dynamic `import('cytoscape')` not static `import` to avoid bloating the main bundle.
2. **Vite proxy**: In `vite.config.ts`, add proxy to FastAPI backend (`/api` → `http://localhost:8000`) for dev. Production uses nginx or same-origin serving.
3. **Card types in frontmatter**: YAML `408` becomes int. The frontend's `CardData.type` is `string` — if backend returns int for some fields, frontend type checks fail. Always cast on backend.
