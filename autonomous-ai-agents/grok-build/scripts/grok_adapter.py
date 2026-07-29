#!/usr/bin/env python
"""Hermes-Grok Adapter (v0.1)

Hermes 与 Grok Build (xAI `grok` CLI) 之间的唯一桥接层。
架构红线:
  1. 仅通过 subprocess 调用 grok headless —— 进程边界即架构边界
  2. 强制 GROK_MEMORY=0 —— 记忆主权归 Hermes
  3. verification 一律以 git 为准, 不信 LLM 自述

子命令:
  doctor                          环境体检 (二进制/版本/代理/认证)
  run    --task T --workdir W     一次性任务 -> envelope JSON (stdout 最后一行)
  resume --session S --task T     续接既有 Grok 会话
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "config.yaml"


def load_config() -> dict:
    import yaml
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_env(cfg: dict) -> dict:
    env = os.environ.copy()
    env.update(cfg["grok"].get("env") or {})       # GROK_MEMORY=0
    proxy = cfg["grok"].get("proxy")
    if proxy:
        env.setdefault("HTTPS_PROXY", proxy)
        env.setdefault("HTTP_PROXY", proxy)
    return env


def policy_flags(cfg: dict, policy: str) -> list:
    p = (cfg.get("policies") or {}).get(policy)
    if p is None:
        raise SystemExit(f"unknown policy: {policy}")
    flags = []
    if p.get("yolo"):
        flags.append("--yolo")
    if p.get("tools"):
        flags += ["--tools", p["tools"]]
    for rule in p.get("allow") or []:
        flags += ["--allow", rule]
    for rule in p.get("deny") or []:
        flags += ["--deny", rule]
    return flags


def cmd_doctor(cfg: dict) -> int:
    report = {"binary": None, "version": None, "proxy_ok": None, "auth_hint": None, "ok": False}
    binary = shutil.which(cfg["grok"]["binary"]) or (
        cfg["grok"]["binary"] if Path(cfg["grok"]["binary"]).exists() else None)
    report["binary"] = binary
    if binary:
        try:
            out = subprocess.run([binary, "--version"], capture_output=True,
                                 text=True, timeout=30, env=build_env(cfg))
            report["version"] = (out.stdout or out.stderr).strip()
        except Exception as e:
            report["version"] = f"error: {e}"
    proxy = cfg["grok"].get("proxy")
    if proxy:
        import urllib.request
        try:
            req = urllib.request.Request("https://x.ai", method="HEAD")
            urllib.request.urlopen(req, timeout=10)
            report["proxy_ok"] = True
        except Exception:
            report["proxy_ok"] = False
    creds = Path.home() / ".grok"
    report["auth_hint"] = "~/.grok exists" if creds.exists() else "no ~/.grok — run `grok` once interactively (OAuth)"
    report["ok"] = bool(binary) and report["proxy_ok"] is not False and creds.exists()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def git(workdir: str, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=workdir, capture_output=True, text=True)
    return r.stdout.strip()


def snapshot_head(workdir: str, auto_init: bool) -> str:
    if not (Path(workdir) / ".git").exists():
        if not auto_init:
            return ""
        subprocess.run(["git", "init"], cwd=workdir, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=workdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "adapter: pre-task snapshot", "--allow-empty"],
                       cwd=workdir, capture_output=True)
    return git(workdir, "rev-parse", "HEAD")


def verify(workdir: str, base: str) -> dict:
    status = git(workdir, "status", "--porcelain")
    changed = [{"status": ln[:2].strip(), "path": ln[3:]} for ln in status.splitlines() if ln]
    diff_stat = git(workdir, "diff", "--stat", base) if base else git(workdir, "diff", "--stat")
    return {"files_changed": changed, "diff_stat": diff_stat.splitlines()[-1] if diff_stat else ""}


def compose_task(task: str, digest_max: int) -> str:
    return (f"{task}\n\n完成后必须:\n"
            f"1. 确保验收标准逐条满足;\n"
            f"2. 用不超过{digest_max}字总结: 改了什么/关键决策/遗留问题。")


def run_grok(cfg: dict, args, resume_id: str | None) -> int:
    d = cfg["defaults"]
    workdir = str(Path(args.workdir).resolve())
    base = snapshot_head(workdir, cfg["verification"]["auto_git_init"])

    model = cfg.get("defaults", {}).get("model", "ds-v4")
    binary = shutil.which(cfg["grok"]["binary"]) or cfg["grok"]["binary"]
    cmd = [binary,
           "-p", compose_task(args.task, cfg["memory_writeback"]["digest_max_chars"]),
           "-m", model,
           "--output-format", d["output_format"],
           "--max-turns", str(args.max_turns or d["max_turns"]),
           "--cwd", workdir,
           "--no-auto-update"]
    if resume_id:
        cmd += ["--resume", resume_id]
    if args.rules:
        cmd += ["--rules", args.rules]
    cmd += policy_flags(cfg, args.policy or d["policy"])

    envelope = {"ok": False, "task": args.task, "workdir": workdir, "session_id": resume_id,
                "stop_reason": None, "text": None, "num_turns": None, "usage": None,
                "cost_usd": None, "verification": None, "memory_digest": None, "error": None}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              timeout=args.timeout or d["timeout_seconds"],
                              env=build_env(cfg), cwd=workdir)
        raw = (proc.stdout or "").strip()
        try:
            data = json.loads(raw.splitlines()[-1]) if raw else {}
        except json.JSONDecodeError:
            data = {"text": raw}
        envelope.update({
            "ok": proc.returncode == 0 and data.get("type") != "error",
            "session_id": data.get("sessionId") or resume_id,
            "stop_reason": data.get("stopReason"),
            "text": data.get("text"),
            "num_turns": data.get("num_turns"),
            "usage": data.get("usage"),
            "cost_usd": data.get("total_cost_usd"),
            "error": None if proc.returncode == 0 else (data.get("message") or proc.stderr[-2000:]),
        })
        if envelope["text"]:
            envelope["memory_digest"] = envelope["text"][-cfg["memory_writeback"]["digest_max_chars"]:]
    except subprocess.TimeoutExpired:
        envelope["error"] = "timeout: grok did not finish; consider background mode or resume"
    except FileNotFoundError:
        envelope["error"] = "grok binary not found — run doctor; fallback to codex/claude-code skill"

    if cfg["verification"]["git_diff"]:
        envelope["verification"] = verify(workdir, base)
    print(json.dumps(envelope, ensure_ascii=False))
    return 0 if envelope["ok"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(prog="grok_adapter")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    for name in ("run", "resume"):
        p = sub.add_parser(name)
        p.add_argument("--task", required=True)
        p.add_argument("--workdir", required=True)
        p.add_argument("--policy")
        p.add_argument("--max-turns", type=int, dest="max_turns")
        p.add_argument("--timeout", type=int)
        p.add_argument("--rules")
        if name == "resume":
            p.add_argument("--session", required=True)
    args = ap.parse_args()
    cfg = load_config()
    if args.cmd == "doctor":
        return cmd_doctor(cfg)
    return run_grok(cfg, args, getattr(args, "session", None))


if __name__ == "__main__":
    sys.exit(main())
