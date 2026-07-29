# Pi auth.json Format (from source)

## Correct format

```json
{
  "deepseek": {
    "type": "api_key",
    "key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
}
```

## Why plain string fails

From `dist/core/auth-storage.js`:

```js
const credential = this.data[provider];
if (credential?.type !== "api_key")    // ← plain string has no .type
    return credential;                  // ← returns the string, not the key
if (credential.key === undefined)
    return credential;
return { ...credential, key: resolveConfigValue(credential.key, credential.env) };
```

From `dist/core/provider-composer.js`:

```js
input.credential.key
    ? { auth: { apiKey: input.....key }, env: input.credential.env, source: "stored credential" }
```

The composer expects `credential.key` to exist — a plain string (`"sk-..."`) has no `.key` property, so auth resolution fails silently.

## Optional fields

- `"env"`: environment variable name for config-value resolution via `resolveConfigValue()`
- Only `"type": "api_key"` and `"key"` are required for API key providers

## Other credential types

OAuth credentials use `"type": "oauth"` with different fields (tokens, refresh tokens). This is managed by `/login` in interactive mode for subscription providers (ChatGPT Plus, Claude Pro, GitHub Copilot, etc.).
