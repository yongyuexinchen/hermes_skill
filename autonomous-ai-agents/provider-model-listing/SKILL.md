---
name: provider-model-listing
description: "Diagnose and resolve model-visibility issues with Hermes providers: understand how the model picker works, access models not shown by default, and handle provider model-name changes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
---

# Provider Model Listing

Models visible in Hermes' model picker (`/model`, `hermes model`, `hermes setup`) come from **three sources** combined at runtime. A model you know exists at the provider may be invisible for several distinct reasons.

## Model-Source Stack

Hermes resolves model visibility through a **4-layer fallback chain**. Each layer is hit only if the previous one fails or returns incomplete data:

| # | Source | Location | Used when |
|---|--------|----------|-----------|
| 1 | **Live `/v1/models` endpoint** | `GET {base_url}/models` on the provider's base URL | Provider has `auth_type=api_key` + a reachable endpoint |
| 2 | **Static curated lists** (`_PROVIDER_MODELS`) | `hermes_cli/models.py` → `_CURATED_MODEL_LISTS[provider]` | Live fetch succeeds: merged with live (curated-first unless in `_LIVE_FIRST_PICKER_PROVIDERS`). Live fails: next fallback |
| 3 | **Provider profile `fallback_models`** | `plugins/model-providers/<provider>/__init__.py` → `DeepSeekProfile(fallback_models=(...))` | Live fetch returns empty/None AND curated list also empty OR no `_PROVIDER_MODELS` entry exists |
| 4 | **models.dev disk cache** | `models_dev_cache.json` (for `_MODELS_DEV_PREFERRED` providers like deepseek) | Applied as a second merge pass on top of the curated static list, adding models.dev models the static list doesn't know about |

> **Critical insight from debugging:** Layer 3 (`fallback_models`) is the one most likely to be stale. The curated list (`_PROVIDER_MODELS`) gets reviewed during PRs, but `fallback_models` lives in the provider plugin file and is easy to forget. When the live fetch fails (common on restrictive networks, proxies, or Windows with `WinError 10054`), the `fallback_models` tuple becomes the **sole source of truth** for the picker.

## Why a Model May Be Invisible

### 1. Provider renamed the model (most common)

Providers deprecate old model names and introduce new ones. Example from this session:

| Old name | New name | Status |
|----------|----------|--------|
| `deepseek-chat` | `deepseek-v4-flash` | `deepseek-chat` deprecated 2026/07/24 |
| `deepseek-reasoner` | ← maps to v4-flash thinking mode | `deepseek-reasoner` deprecated 2026/07/24 |
| `deepseek-v4-pro` | *(new flagship)* | Current |
| `deepseek-v4-flash` | *(new fast)* | Current |

**Hermes' curated lists** (`_CURATED_MODEL_LISTS["deepseek"]`) already include all four: `deepseek-v4-pro`, `deepseek-v4-flash`, `deepseek-chat`, `deepseek-reasoner`. If the picker doesn't show them, the issue is in the merge logic, not the data.

### 2. Static list is outdated

`_CURATED_MODEL_LISTS` in `hermes_cli/models.py` is maintained manually. If a provider releases a new model, it won't appear there until the next Hermes update. The live `/v1/models` endpoint may return it, but the picker's merge logic may still filter to the static list.

### 3. Live `/v1/models` returns limited results

Some providers (including DeepSeek) don't return a complete model list from their `/v1/models` endpoint — they may only return the "recommended" or "default" models. This is provider-side, not a Hermes bug.

### 4. The model picker screens or deduplicates

The `/model` picker can filter models based on:
- Current provider (shows only models for the selected provider)
- Deduplication (if a model appears on multiple providers, only one entry is shown)
- Aggregator vs direct provider routing logic

### 5. Context-length metadata may be missing

Hermes builds a context-length lookup from `model_metadata.py` → `_CONTEXT_LENGTHS_BY_SUBSTRING`. If a model name isn't in there, Hermes falls back to a default. This doesn't block the model from the picker but can cause issues at inference time.

## Diagnostic Flow

When a user reports "I can see `deepseek-chat` but not `deepseek-v4-pro`":

```
1. Check Hermes internal knowledge
   ├── grep model_metadata.py for deepseek-v4 → confirms Hermes knows the context length
   └── grep _CURATED_MODEL_LISTS in models.py → confirms model is in curated list

2. Check provider profile's fallback_models
   ├── cat plugins/model-providers/<provider>/__init__.py
   ├── Look for fallback_models=(...)
   └── If it's missing the new models AND the live fetch is broken, this is the blocker

3. Check provider's official API docs
   ├── curl their docs site or API reference
   └── Confirm the model name is correct (providers change names)

4. Test the model directly (bypass picker)
   ├── /model deepseek-v4-pro              (in-session)
   ├── /model deepseek/deepseek-v4-pro     (with provider prefix)
   └── hermes -m deepseek/deepseek-v4-pro  (CLI launch)

5. Refresh model cache
   ├── /model --refresh                     (re-fetch live /v1/models)
   └── hermes doctor --fix                  (check config + dependencies)

6. Set model in config (permanent bypass)
   └── hermes config set model.default deepseek/deepseek-v4-pro

7. Debug the live fetch (if it's failing)
   ├── python -c "from hermes_cli.auth import resolve_api_key_provider_credentials; from providers import get_provider_profile; creds = resolve_api_key_provider_credentials('deepseek'); p = get_provider_profile('deepseek'); live = p.fetch_models(api_key=creds['api_key'], base_url=creds.get('base_url') or None); print(live)"
   ├── WinError 10054 (connection reset by peer) → typical Windows firewall/proxy block
   └── If live fetch fails → provider_model_ids falls through to fallback_models
```

## Diagnostic Script: Dump Model Sources (for execute_code)

```python
from hermes_cli.models import provider_model_ids, _PROVIDER_MODELS, clear_provider_models_cache
from hermes_cli.auth import resolve_api_key_provider_credentials
from providers import get_provider_profile

# Check what the model picker sees (clears cache for fresh result)
clear_provider_models_cache("deepseek")
print("Picker models:", provider_model_ids("deepseek", force_refresh=True))

# Check the curated list
print("Curated:", _PROVIDER_MODELS.get("deepseek", []))

# Check fallback_models and live fetch
p = get_provider_profile("deepseek")
print("Profile fallback:", p.fallback_models)
creds = resolve_api_key_provider_credentials("deepseek")
if api_key := creds.get("api_key"):
    live = p.fetch_models(api_key=api_key, base_url=creds.get("base_url") or None)
    print("Live API result:", live if live else "(failed)")
```

## Direct Access Methods (bypass the picker entirely)

| Method | Command |
|--------|---------|
| In-session switch | `/model deepseek-v4-pro` |
| With provider prefix | `/model deepseek/deepseek-v4-pro` |
| CLI launch | `hermes -m deepseek/deepseek-v4-pro` |
| CLI launch + provider | `hermes -m deepseek/deepseek-v4-pro --provider deepseek` |
| Config perma-set | `hermes config set model.default deepseek/deepseek-v4-pro` |
| Config provider pin | `hermes config set model.provider deepseek` |

## Pitfalls

- **`deepseek-chat` and `deepseek-reasoner` will stop working on 2026/07/24.** If a user starts a session with these today, it works because DeepSeek maps them server-side. After deprecation, the API will reject them. Proactively migrate to `deepseek-v4-pro` or `deepseek-v4-flash`.
- **`/model --refresh` can be slow** — it fetches live endpoints for all providers, which serializes at ~1–2 seconds per provider.
- **Curated list vs live endpoint ordering matters.** The merge in `provider_model_ids()` may prefer the live list or the curated list depending on whether the provider is in `_LIVE_FIRST_PICKER_PROVIDERS`. Check `models.py` for this set before concluding which source "wins".
- **Model names with `vendor/` prefix** work differently on aggregators (OpenRouter: `deepseek/deepseek-v4-pro`) vs direct providers (DeepSeek: `deepseek-v4-pro`). Use the direct name for direct providers.
- **`fallback_models` is the silent cache poison.** When the live `/v1/models` fetch fails (common on Windows with `WinError 10054` from firewalls/proxies), `provider_model_ids()` returns the provider profile's `fallback_models` tuple — NOT the curated `_PROVIDER_MODELS` list. If `fallback_models` is stale, the picker silently shows outdated models. Always check `fallback_models` in `plugins/model-providers/<provider>/__init__.py` alongside `_CURATED_MODEL_LISTS` in `models.py`.
- **Windows `WinError 10054` blocks live model discovery.** The `urllib` request to `GET /v1/models` on the provider's endpoint fails with a connection reset. This isn't a Hermes bug — it's the Windows network stack (firewall, VPN, corporate proxy, or TCP reset). The fix is to update `fallback_models` so the offline fallback has the right models. Test with a direct curl:
  ```bash
  curl -s https://api.deepseek.com/v1/models \
    -H "Authorization: Bearer $DEEPSEEK_API_KEY"
  ```

## Key Hermes Source Files

| File | What it contains |
|------|-----------------|
| `agent/model_metadata.py` → `_CONTEXT_LENGTHS_BY_SUBSTRING` | Context window lengths keyed by model-name substring |
| `hermes_cli/models.py` → `_CURATED_MODEL_LISTS` | Static per-provider model ID lists (fallback + curated display) |
| `hermes_cli/providers.py` → `HERMES_OVERLAYS` | Provider metadata: transport, auth type, aggregator flags |
| `hermes_cli/model_switch.py` | Model alias resolution + switch logic |
| `cli.py` → `_open_model_picker` | The interactive model picker UI |
| `hermes_cli/doctor.py` → `check_diagnostics` | `hermes doctor` health checks including /v1/models probe |
