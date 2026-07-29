# Hermes Disk Health & Maintenance

Quick diagnostic workflow for reclaiming disk space and fixing common bloat issues in a Hermes installation.

## Diagnostic Checklist

Run these in order — each step is fast and non-destructive:

### 1. Broken Install Packages

Failed updates leave `hermes-agent.broken-*` directories in `~/.hermes/`. Each can be 130MB–1.7GB.

```bash
# Find them
find ~/.hermes/ -maxdepth 1 -type d -name "hermes-agent.broken-*"

# Check total size
du -sh ~/.hermes/hermes-agent.broken-*

# Safe to delete if current version is working
rm -rf ~/.hermes/hermes-agent.broken-*
```

### 2. state.db Bloat

SQLite session database can grow large from FTS indexes and message history. Two approaches:

**A. VACUUM (safe, online)**
```python
import sqlite3
conn = sqlite3.connect(r'C:\Users\<user>\AppData\Local\hermes\state.db')
conn.execute('VACUUM')
conn.close()
```
Note: `sqlite3` CLI may fail with "unable to open database file" when Hermes is running — use Python's sqlite3 module instead, which handles WAL-mode locks.

**B. Prune old sessions (more effective for large DBs)**
```bash
hermes sessions prune --older-than 30
```
VACUUM only recovers fragmented space. If state.db is 100MB because of 6,000+ messages and dual FTS indexes, pruning old sessions is the real fix.

**C. Check what's taking space**
```python
cur.execute("SELECT COUNT(*) FROM messages")    # message count
cur.execute("SELECT COUNT(*) FROM sessions")    # session count
cur.execute("PRAGMA freelist_count")            # fragmented pages
```

### 3. Profiles Directory

Kanban worker profiles accumulate state.db files. 15 profiles × 50MB each = 750MB+ is common.

```bash
du -sh ~/.hermes/profiles/*/ | sort -rh
```

Delete unused profiles:
```bash
hermes profile delete <name>
```

### 4. CDP Browser Temp Files

Chrome CDP sessions may leak temp directories:

```bash
ls $TEMP/agent-browser-cdp_*   # Windows
ls $TMPDIR/agent-browser-cdp_* # macOS/Linux
# Safe to delete
rm -rf "$TEMP/agent-browser-cdp_"*
```

### 5. CDP Browser Connection Failures

If logs show repeated `localhost:9222` connection errors:
```bash
hermes config set browser.cdp_url ""
hermes config set browser.backend playwright
```
This stops the CDP backend from spamming connection attempts. Use `browser_navigate` with Chrome manually started when needed.

## When state.db VACUUM Won't Help

VACUUM only removes fragmented free pages. If `freelist_count` is low (< 5% of `page_count`), the DB is genuinely full of data, not fragmented. In that case:
- Prune old sessions with `hermes sessions prune`
- Or accept the size — 100MB for 6,000+ messages with FTS indexes is normal
