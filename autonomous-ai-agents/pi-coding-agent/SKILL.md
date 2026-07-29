---
name: pi-coding-agent
description: Install and configure Inflection's Pi Coding Agent (CLI) — npm global install, provider/model defaults, and auth setup.
category: autonomous-ai-agents
triggers:
  - "install pi coding agent"
  - "set up pi"
  - "configure pi"
  - "@earendil-works/pi-coding-agent"
  - "pi CLI tool"
---

# Pi Coding Agent

Pi is Inflection's CLI coding agent (`@earendil-works/pi-coding-agent`, npm). It has read/bash/edit/write/grep/find/ls tools, session management, and supports 20+ providers including DeepSeek, OpenAI, Anthropic.

## Quick Install

```bash
npm install -g @earendil-works/pi-coding-agent
```

Bin: `pi`. Version ~0.81.x, maintained by Armin Ronacher (mitsuhiko) + Mario Zechner (badlogic).

## Configuration Files

| File | Purpose |
|------|---------|
| `~/.pi/agent/settings.json` | Default provider, model, thinking level, UI prefs |
| `~/.pi/agent/auth.json` | API keys and OAuth tokens per provider |
| `~/.pi/agent/models-store.json` | Cached model catalog |
| `~/.pi/agent/sessions/` | Session history |

### settings.json — default provider/model

```json
{
  "defaultProvider": "deepseek",
  "defaultModel": "deepseek-v4-pro",
  "theme": "dark"
}
```

Key names are `defaultProvider` / `defaultModel` — NOT `provider` / `model`.

### auth.json — API key format

```json
{
  "deepseek": {
    "type": "api_key",
    "key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
}
```

**CRITICAL**: must be `{"provider": {"type": "api_key", "key": "..."}}` — plain `{"provider": "sk-..."}` does NOT work. Optional `"env"` field for config-value resolution.

## Windows Git-Bash Pitfalls

### npm prefix path mapping

Git-bash `/e/npm-global` ≠ `E:\npm-global`. npm resolves `/e/...` to `C:\e\...`.

**Fix**: use Windows-style paths:
```bash
npm config set prefix "E:\\npm-global"
```

### Environment variable passing

Inline `VAR=val command` may not reach Node processes on git-bash.

**Use export**:
```bash
export DEEPSEEK_API_KEY="sk-..." && pi -p "hello"
```

### PATH for global npm bin

After setting prefix to a non-default location, add to `.bashrc`:
```bash
export PATH="E:\\npm-global:$PATH"
```

## Usage

```bash
pi                                    # Interactive TUI (uses defaultProvider/defaultModel)
pi -p "question"                      # Non-interactive, one-shot
pi -p --provider deepseek "question"  # Override provider
pi --continue                         # Resume last session
pi --resume                           # Pick session to resume
pi --list-models deepseek             # List available models
```

## Model switching

In interactive mode: `Ctrl+P` cycles through models. `--models` flag limits the cycling pool.

## Environment Variables

| Var | Provider |
|-----|----------|
| `DEEPSEEK_API_KEY` | DeepSeek |
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |
| `GEMINI_API_KEY` | Google Gemini |

Full list: `pi --help` or `E:/npm-global/node_modules/@earendil-works/pi-coding-agent/docs/providers.md`.
