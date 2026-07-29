# Web API Layer Pattern (Phase 9.0)

## Architecture

```
Browser / Frontend
        │
        ▼
FastAPI (applications/api/)
        │  app.state.adapter
        ▼
KnowledgeAgentAdapter (adapters/agent/)
        │
        ▼
KnowledgeEngine (core/engine/)
```

## Directory Structure

```
applications/api/
    __init__.py
    main.py          ← create_app(), inject adapter
    schemas.py       ← Pydantic request/response models
    routes/
        cards.py     ← GET/POST/PUT/DELETE /api/cards
        search.py    ← GET /api/search?q=
        stats.py     ← GET /api/stats, POST /api/rebuild
```

## Key Architecture Constraints

1. **API never imports storage.markdown or storage.index** — validated by AST import scan
2. **API never creates KnowledgeEngine directly** — validated by grep in routes
3. **All knowledge ops go through adapter** — `request.app.state.adapter`
4. **Core layer untouched** — API is pure Application Layer addition

## Adapter Injection Pattern

```python
# main.py
def create_app() -> FastAPI:
    app = FastAPI()
    app.state.adapter = build_adapter()  # single instance, injected at startup
    app.include_router(cards.router)
    return app

# routes/cards.py
def _adapter(request: Request):
    return request.app.state.adapter
```

## Pydantic Schema Isolation

Card dataclass → Pydantic schema → JSON. Never return raw Card objects.

```python
# schemas.py
class CardResponse(BaseModel):
    id, title, type, content, tags, relations, created_at, updated_at

class CardCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content, type, tags, relations = "discriminant", [], []

def card_to_response(card_dict: dict) -> CardResponse:
    """Adapter dict → Pydantic."""
```

## TestClient with InMemory Injection

```python
# tests/test_api.py
@pytest.fixture
def client():
    app = create_app()
    engine = KnowledgeEngine(storage=InMemoryStorage(), search=InMemorySearch())
    app.state.adapter = KnowledgeAgentAdapter(engine)  # override
    return TestClient(app)
```

## Architecture Enforcement Test

```python
# tests/test_api_architecture.py
DENY = ["storage.markdown", "storage.index", "core.engine.KnowledgeEngine"]

def _check_imports(path, deny):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import): ...
        elif isinstance(node, ast.ImportFrom): ...

def test_api_no_storage_imports(): ...

def test_api_uses_adapter():
    # grep routes for adapter presence, KnowledgeEngine absence
```

## Endpoints (9 total)

| Method | Path | Engine Call |
|--------|------|-------------|
| GET | /api/cards?tag=&limit= | list_all() |
| POST | /api/cards | create() |
| GET | /api/cards/{id} | get() |
| PUT | /api/cards/{id} | update() |
| DELETE | /api/cards/{id} | delete() |
| GET | /api/cards/{id}/related | find_related_cards() |
| GET | /api/search?q=&tag= | search() |
| GET | /api/stats | stats() |
| POST | /api/rebuild | rebuild_index() |

## Common Pitfall

**adapter.update_knowledge signature mismatch**: The adapter expects individual kwargs
(`title=, content=, tags=, type_=, relations=`), NOT a single dict. Unpack explicitly:

```python
# WRONG
adapter.update_knowledge(card_id, fields)  # fields is dict

# RIGHT
adapter.update_knowledge(
    card_id,
    title=fields.get("title"),
    content=fields.get("content"),
    tags=fields.get("tags"),
    type_=fields.get("type"),
    relations=fields.get("relations"),
)
```
