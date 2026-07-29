---
name: hermes-cron-workflows
description: "Create, chain, and configure Hermes cron jobs — multi-job pipelines with context_from, toolset restriction, and delivery targeting. Covers the CLI vs cronjob-tool split, common pitfalls, and the recommended two-phase workflow."
version: 1.0.0
category: software-development
tags: [hermes, cron, scheduling, pipelines, automation]
metadata:
  hermes:
    tags: [hermes, cron, scheduling, pipelines, automation]
---

# Hermes Cron Workflows

## When to Load

Load this skill whenever you need to:
- Create one or more cron jobs
- Chain cron jobs into a pipeline (Job A → Job B → Job C)
- Configure advanced cron features: `context_from`, `enabled_toolsets`, `attach_to_session`, `deliver`
- Debug a cron job that isn't picking up context or running silently
- Use the `cronjob` tool — which has non-obvious required-parameter interactions

## The Two-Phase Workflow (RECOMMENDED)

Creating a cron job has two tools available: the `hermes cron create` **CLI** and the `cronjob` **tool**. They have **different feature surfaces**. The recommended workflow uses both:

### Phase 1: Create via CLI

```bash
hermes cron create "<schedule>" "<prompt>" --name "<name>" --deliver origin
```

The CLI is **reliable** for creation. It supports: `schedule`, `prompt`, `--name`, `--deliver`, `--repeat`, `--skill`, `--script`, `--no-agent`, `--workdir`.

The CLI does **NOT** support: `context_from`, `enabled_toolsets`, `attach_to_session`.

**Schedule formats:** `"30m"`, `"every 2h"`, `"0 10 * * *"` (cron), `"2026-07-17T10:00:00"` (ISO one-shot).

**Delivery:** `--deliver origin` sends results to the current chat. `--deliver local` is local-only (no delivery).

### Phase 2: Enrich via cronjob tool

```python
cronjob(
    action="update",
    job_id="<job_id>",
    context_from=["<upstream_job_id>"],  # chain: this job reads upstream's latest output
    enabled_toolsets=["web"],            # restrict tools to save tokens
    attach_to_session=True               # make results continuable
)
```

Fields the CLI can't set but the `cronjob` tool can:
- **`context_from`** — list of upstream job IDs whose last output is injected as context
- **`enabled_toolsets`** — restrict which tools the job's agent can use (e.g. `["web"]` for web-only jobs)
- **`attach_to_session`** — when True, results are delivered into a continuable session so the user can reply

Use the CLI `hermes cron edit` for basic updates (schedule, prompt, name, deliver, etc.) — it avoids the `cronjob` tool's stricter parameter requirements.

## Common Pitfalls

### 1. cronjob create: must include BOTH schedule AND prompt

The `cronjob` tool requires **both** `schedule` and `prompt` (or `skills`) for `action="create"`. Omitting either produces alternating errors:

- Without `schedule`: `"schedule is required for create"`
- Without `prompt`: `"create requires either prompt or at least one skill"`

**Fix:** Always include both in a single call. If you hit either error, the other field is the one you're missing.

### 2. cronjob update: must include job_id AND a field to update

For `action="update"`, both `job_id` and at least one updatable field are required:

- Without `job_id`: `"job_id is required for action 'update'"`
- With `job_id` but no update fields: `"No updates provided."`

Updatable fields: `schedule`, `prompt`, `name`, `deliver`, `repeat`, `skills`, `no_agent`, `agent`, `workdir`, `enabled_toolsets`, `context_from`, `attach_to_session`.

### 3. deliver="local" means silent — no results visible

Jobs created with `deliver="local"` run silently. The results are saved but not delivered to any chat. For visible results, set `deliver="origin"` (current chat) or a specific platform target.

### 4. context_from chains need sequential timing

When Job B's `context_from` references Job A, ensure Job B's schedule runs **after** Job A has completed. A 30-minute gap between chained jobs is safe. If Job B fires before Job A finishes, it gets the *previous* run's output (or nothing on first run).

## Pipeline Example

Three-job blog topic pipeline:

```
10:00 Job 1 — collect (web_search HN + Zhihu)
        │
10:30 Job 2 — filter Top 3 (reads Job 1 via context_from)
        │
11:00 Job 3 — generate briefs (reads Job 2 via context_from)
```

Creation:

```bash
# Phase 1: create all three
hermes cron create "0 10 * * *" "<prompt-collect>" --name "Blog-Collect" --deliver origin
hermes cron create "30 10 * * *" "<prompt-filter>" --name "Blog-Filter" --deliver origin
hermes cron create "0 11 * * *" "<prompt-brief>" --name "Blog-Brief" --deliver origin
```

```python
# Phase 2: enrich Job 2 and Job 3
cronjob(action="update", job_id="<job2_id>", context_from=["<job1_id>"],
        enabled_toolsets=["web"], attach_to_session=True)
cronjob(action="update", job_id="<job3_id>", context_from=["<job2_id>"],
        enabled_toolsets=["web"], attach_to_session=True)
# Job 1 also needs tools
cronjob(action="update", job_id="<job1_id>", enabled_toolsets=["web"],
        attach_to_session=True)
```

## Reference Files

- `references/blog-pipeline-example.md` — Full session transcript: exact prompt templates for a 3-job blog pipeline, error transcript from cronjob tool creation struggles, and final job configuration table.

## Verification

After creation, verify with:

```bash
hermes cron list              # check all jobs exist with correct schedules
cronjob(action="list")        # detailed view with last_status, enabled_toolsets
cronjob(action="run", job_id="<id>")  # manual test run — check execution_success
```

All three runs should return `"ok"` and `execution_success: true`.

## CLI Quick Reference

```bash
hermes cron list                          # list all jobs
hermes cron list --all                    # include disabled
hermes cron create SCHED "PROMPT"         # create (--name, --deliver, --repeat, --skill, --script)
hermes cron edit ID                       # edit (--schedule, --prompt, --name, --deliver, --repeat, --skill, --script, --workdir)
hermes cron pause ID                      # pause a job
hermes cron resume ID                     # resume a paused job
hermes cron run ID                        # trigger on next tick
hermes cron remove ID                     # delete a job
hermes cron status                        # scheduler health
```