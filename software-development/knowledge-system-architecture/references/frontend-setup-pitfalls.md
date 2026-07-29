# Frontend Setup Pitfalls

From Phase 9.1+9.5 Knowledge Explorer development.

## Vite Proxy Must Be Configured

The React+Vite dev server at `:5173` makes API calls to `/api/*` paths. Without a proxy config, these requests go to `http://127.0.0.1:5173/api/...` (the Vite dev server itself), which returns the `index.html` HTML page, NOT JSON.

**Symptom**: Browser console shows `Uncaught TypeError: recent.map is not a function` in Dashboard component. The API client's `fetchCards()` receives HTML text instead of a JSON array, and `.map()` fails.

**Fix** — `vite.config.ts`:
```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',  // backend FastAPI port
    },
  },
})
```

After changing Vite config, **restart the dev server** (`npm run dev`).

## Int Tags in YAML Frontmatter

When writing Knowledge OS card `.md` files with numeric tags like `408`:
```yaml
tags:
- calculus
- 408
```

YAML parses `408` as an **integer**, not a string. This crashes `whoosh_search._to_document()` which does `" ".join(card.tags)` expecting all strings.

**Fix**: Quote numeric tags:
```yaml
tags:
- calculus
- '408'
```

**Defense**: `_to_document()` should use `str(t)` instead of bare `t`:
```python
"tags": " ".join(str(t) for t in card.tags)
```

## API Client Type Assumptions

The `fetchCards()` return type `Promise<CardData[]>` is just a TypeScript assertion — not runtime validation. If the backend returns an error response or HTML, the actual value at runtime won't be an array. Components using `.map()` on API results should guard:
```typescript
// Either:
useState<CardData[]>([])
// Or:
{Array.isArray(recent) && recent.map(...)}
```

## Backend Port

Default: `uvicorn applications.api.main:app --host 127.0.0.1 --port 8000`
Frontend Vite proxy must point to this same port.
