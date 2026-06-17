#!/usr/bin/env python3
"""Deterministic core for the meeting-action-items skill.

Subcommands:
  list   pure read: scan meeting summaries, dedup against state, apply the
         assignee allowlist, emit candidate JSON on stdout. Never writes.
  apply  owns all mutation: creates Todoist tasks via the td CLI and writes
         state atomically per item, so a crash never leaves a created task
         unrecorded.

Stdlib only. The LLM layer (SKILL.md) does triage via AskUserQuestion and
calls these subcommands; it never touches td or the state file directly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

DEFAULT_VAULT = Path.home() / "Documents" / "Work"
STATE_REL = Path(".lyt-assistant") / "_action-item-state.json"

# Allowlist of normalized assignee values that pass the filter. Matching:
# split the raw assignee on / , + &, trim, lowercase, exact-match each part.
ASSIGNEE_ALLOW = {
    "ian", "ian bartholomew", "ian-bartholomew", "ian b", "ian b.",
    "ian bart", "me",
    "all", "all recipients", "all hands", "all employees", "everyone",
    "team", "fes", "fes team", "fes platform", "fes platform team",
    "platform", "platform team", "sre", "sre team",
}

BULLET_RE = re.compile(r"^\s*[-*]\s+(\[[ xX]\]\s+)?")
CHECKED_RE = re.compile(r"^\s*[-*]\s+\[[xX]\]")
BOLD_PREFIX_RE = re.compile(r"^\*\*[A-Za-z][A-Za-z0-9 ,/+&-]*:\*\*\s+")
BARE_PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 ,/+&.-]*:\s+")


def normalize(s: str) -> str:
    """Reproduce the legacy bash sed chain byte-for-byte: strip bullet
    marker + optional checkbox, then bold prefix, then bare Word: prefix
    (sequentially, so both can strip), collapse whitespace, lowercase."""
    s = BULLET_RE.sub("", s)
    s = BOLD_PREFIX_RE.sub("", s)
    s = BARE_PREFIX_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def key_for(meeting_dir: str, normalized: str) -> str:
    h = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    return f"{meeting_dir}::{h}"


DEDUP_THRESHOLD = 0.85
DEDUP_STOPWORDS = {
    "the", "a", "an", "to", "of", "for", "and", "with",
    "on", "in", "re", "about", "please",
}


def dedup_normalize(s: str) -> str:
    """Aggressive normalization for cross-todo dedup. Distinct from
    normalize() (which mirrors the legacy state-key bash chain): NFKC fold,
    strip a leading bullet/checkbox, lowercase, replace every non-word char
    with a space, collapse whitespace."""
    s = unicodedata.normalize("NFKC", s)
    s = BULLET_RE.sub("", s)
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def dedup_tokens(s: str) -> set:
    return {t for t in dedup_normalize(s).split() if t not in DEDUP_STOPWORDS}


def title_similarity(a: str, b: str) -> float:
    """Jaccard over significant tokens. 1.0 == identical significant-token
    sets. Substring containment deliberately does NOT score high."""
    ta, tb = dedup_tokens(a), dedup_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def find_duplicate(candidate: str, existing: list[str]) -> str | None:
    """First existing title that is a normalized-equal or high-token-overlap
    match for candidate, else None. Never uses substring containment."""
    cnorm = dedup_normalize(candidate)
    if cnorm:
        for e in existing:
            if dedup_normalize(e) == cnorm:
                return e
    for e in existing:
        if title_similarity(candidate, e) >= DEDUP_THRESHOLD:
            return e
    return None


def body_of(raw: str) -> str:
    """Bullet body with marker/checkbox/prefix stripped, case preserved."""
    s = BULLET_RE.sub("", raw)
    s = BOLD_PREFIX_RE.sub("", s)
    s = re.sub(r"^[A-Za-z][A-Za-z0-9 ,/+&-]*:\s+", "", s)
    return s.strip()


def extract_assignee(raw: str) -> str:
    body = BULLET_RE.sub("", raw)
    m = re.match(r"^\*\*([^*]+)\*\*\s*", body)
    if m:
        return m.group(1).rstrip(":")
    m = re.match(r"^([A-Za-z][A-Za-z0-9 /,+&.-]*):\s", body)
    if m:
        return m.group(1)
    return ""


def should_include_assignee(assignee: str) -> bool:
    if not assignee:
        return True
    for part in re.split(r"[/,+&]", assignee.lower()):
        if part.strip() in ASSIGNEE_ALLOW:
            return True
    return False


def suggest_due_from_text(text: str) -> str:
    lc = text.lower()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", lc)
    if m:
        return m.group(1)
    if re.search(r"(^|[^a-z])(eow|end of week)([^a-z]|$)", lc):
        return "Friday"
    if re.search(r"(^|[^a-z])(eom|end of month)([^a-z]|$)", lc):
        return "end of month"
    if re.search(r"(^|[^a-z])(eod|today|tonight)([^a-z]|$)", lc):
        return "today"
    if re.search(r"(^|[^a-z])tomorrow([^a-z]|$)", lc):
        return "tomorrow"
    m = re.search(r"(^|[^a-z])(next|this)\s+week([^a-z]|$)", lc)
    if m:
        return f"{m.group(2)} week"
    m = re.search(
        r"(^|[^a-z])((next|this)\s+)?"
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)([^a-z]|$)",
        lc)
    if m:
        prefix, day = m.group(3), m.group(4)
        return f"{prefix} {day}" if prefix else day
    m = re.search(r"(^|[^a-z])in\s+(\d+)\s+(day|days|week|weeks)([^a-z]|$)", lc)
    if m:
        return f"in {m.group(2)} {m.group(3)}"
    m = re.search(
        r"(^|[^a-z])(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
        r"\s+(\d{1,2})(st|nd|rd|th)?([^0-9a-z]|$)", lc)
    if m:
        return f"{m.group(2)} {m.group(3)}"
    m = re.search(
        r"(by|due|before|on|deadline|ship[a-z]*|deliver[a-z]*)\s+"
        r"(\d{1,2})/(\d{1,2})(/\d{2,4})?([^0-9/]|$)", lc)
    if m:
        mo, dy, yr = int(m.group(2)), int(m.group(3)), m.group(4) or ""
        if 1 <= mo <= 12 and 1 <= dy <= 31:
            return f"{mo}/{dy}{yr}"
    return ""


def suggest_title(body: str) -> str:
    if len(body) <= 70:
        title = body
    else:
        slice_ = body[:70]
        trimmed = slice_.rsplit(" ", 1)[0] if " " in slice_ else slice_
        title = trimmed + "…"
    return re.sub(r"[\s.,;:]+$", "", title) if not title.endswith("…") \
        else title


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def extract_action_items(summary_path: Path) -> list[str]:
    """Bullets under the Action Items heading (case-insensitive; optional
    bold markers and leading section number), until the next heading/EOF."""
    bullets, inside = [], False
    text = summary_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            if inside:
                break
            hdr = m.group(2).replace("**", "")
            hdr = re.sub(r"^\d+\.?\s+", "", hdr).strip().lower()
            inside = hdr == "action items"
            continue
        if inside and re.match(r"^\s*[-*]", line):
            bullets.append(line)
    return bullets


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_state(state_file: Path) -> dict:
    if not state_file.exists():
        return {"version": 1, "last_run": None, "items": {}}
    data = json.loads(state_file.read_text())
    if data.get("version") != 1:
        sys.exit(f"Unsupported state version {data.get('version')}.")
    return data


def write_state(state_file: Path, data: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(state_file.parent), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, state_file)


def compute_window(args, state: dict) -> str:
    if args.since and args.days:
        sys.exit("Use either --days or --since, not both.")
    if args.since:
        return args.since
    if args.days:
        return (date.today() - timedelta(days=args.days)).isoformat()
    if state.get("last_run"):
        return str(state["last_run"])[:10]
    return (date.today() - timedelta(days=2)).isoformat()


def cmd_list(args) -> int:
    vault = Path(args.vault)
    state = load_state(vault / STATE_REL)
    start = compute_window(args, state)
    meetings_dir = vault / "meetings"
    pending, auto_checked, filtered = [], [], 0
    meetings_scanned = 0
    dirs = sorted(meetings_dir.iterdir()) if meetings_dir.exists() else []
    for d in dirs:
        name = d.name
        if not re.match(r"^\d{4}-\d{2}-\d{2}-", name) or name[:10] < start:
            continue
        summary = d / "summary-default.md"
        if not summary.exists():
            cands = sorted(d.glob("summary-*.md"))
            if not cands:
                continue
            summary = cands[0]
        meetings_scanned += 1
        for raw in extract_action_items(summary):
            norm = normalize(raw)
            if not norm:
                continue
            key = key_for(name, norm)
            if key in state["items"]:
                continue
            if CHECKED_RE.match(raw):
                auto_checked.append(
                    {"key": key, "meeting_dir": name, "raw": raw})
                continue
            if not should_include_assignee(extract_assignee(raw)):
                filtered += 1
                continue
            body = body_of(raw)
            pending.append({
                "key": key, "meeting_dir": name, "raw": raw,
                "suggested": {
                    "title": suggest_title(body),
                    "description": f"{body}\n\nFrom meeting: "
                                   f"{name[11:]} ({name[:10]})",
                    "due": suggest_due_from_text(body) or "tomorrow",
                    "priority": "p2",
                },
            })
    json.dump({"window": {"start": start, "end": date.today().isoformat()},
               "meetings_scanned": meetings_scanned, "pending": pending,
               "auto_checked": auto_checked, "filtered_count": filtered},
              sys.stdout, indent=2)
    print()
    return 0


def td_add(title, priority, description, due, dry_run):
    cmd = ["td", "task", "add", title, "--project", "Work",
           "--priority", priority, "--description", description]
    if due:
        cmd += ["--due", due]
    if dry_run:
        print(f"DRY-RUN: {cmd}", file=sys.stderr)
        return True, "https://app.todoist.com/app/task/DRYRUN"
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return False, "td task add timed out after 30s"
    if r.returncode != 0:
        return False, (r.stderr or r.stdout).strip()
    m = re.search(r"^ID:\s+(\S+)", r.stdout, re.MULTILINE)
    return True, (f"https://app.todoist.com/app/task/{m.group(1)}"
                  if m else None)


def fetch_open_titles(dry_run: bool) -> list[str]:
    """Open Work-project task titles via td. Empty list on ANY failure:
    dedup is a best-effort backstop, never a hard dependency. Uses --all to
    page past the 300-task default."""
    if dry_run:
        return []
    try:
        r = subprocess.run(
            ["td", "task", "list", "--project", "Work", "--all", "--json"],
            capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return []
    if r.returncode != 0:
        return []
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return []
    results = data.get("results", []) if isinstance(data, dict) else data
    if not isinstance(results, list):
        return []
    return [t.get("content", "") for t in results
            if isinstance(t, dict) and t.get("content")]


def cmd_apply(args) -> int:
    vault = Path(args.vault)
    state_file = vault / STATE_REL
    state = load_state(state_file)
    try:
        if args.input:
            with open(args.input) as f:
                payload = json.load(f)
        else:
            payload = json.load(sys.stdin)
    except FileNotFoundError:
        sys.exit(f"Input file not found: {args.input}")
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON input: {e}")
    if not args.dry_run:
        try:
            authed = subprocess.run(["td", "auth", "status"],
                                    capture_output=True,
                                    timeout=30).returncode == 0
        except subprocess.TimeoutExpired:
            authed = False
        if not authed:
            sys.exit("Todoist CLI not authenticated. Run 'td auth login'.")
    if args.existing_todos:
        with open(args.existing_todos) as f:
            existing_titles = list(json.load(f))
    else:
        existing_titles = fetch_open_titles(args.dry_run)
    results = []

    def record(key, meeting_dir, raw, status, url):
        state["items"][key] = {
            "meeting_dir": meeting_dir, "text": raw, "status": status,
            "todoist_url": url, "decided_at": iso_now()}
        write_state(state_file, state)   # flush per item: crash-safe

    for item in payload.get("auto_checked", []):
        record(item["key"], item["meeting_dir"], item["raw"], "todoed", None)
        results.append({"key": item["key"], "outcome": "auto-recorded"})

    for d in payload.get("decisions", []):
        # Per-decision guard: a malformed decision (missing keys, wrong
        # types) must fail just that item, not kill the batch mid-flight.
        try:
            action = d["action"]
            if action == "skip":
                results.append({"key": d["key"], "outcome": "skipped"})
                continue
            if action == "dismiss":
                record(d["key"], d["meeting_dir"], d["raw"],
                       "dismissed", None)
                results.append({"key": d["key"], "outcome": "dismissed"})
                continue
            if action == "todo":
                matched = find_duplicate(d["title"], existing_titles)
                if matched is not None:
                    # non-terminal: skip creation, do NOT record state, so it
                    # resurfaces if the matched live todo is later completed.
                    results.append({"key": d["key"], "outcome": "duplicate",
                                    "matched": matched})
                    continue
                ok, info = td_add(d["title"], d.get("priority", "p2"),
                                  d["description"], d.get("due", ""),
                                  args.dry_run)
                if ok:
                    record(d["key"], d["meeting_dir"], d["raw"],
                           "todoed", info)
                    existing_titles.append(d["title"])  # dedup later batch items
                    results.append({"key": d["key"], "outcome": "created",
                                    "url": info})
                else:
                    results.append({"key": d["key"], "outcome": "failed",
                                    "error": info})
                continue
            results.append({"key": d["key"], "outcome": "failed",
                            "error": f"unknown action {action!r}"})
        except Exception as e:
            key = d.get("key", "?") if isinstance(d, dict) else "?"
            results.append({"key": key, "outcome": "failed",
                            "error": f"{type(e).__name__}: {e}"})

    state["last_run"] = iso_now()
    write_state(state_file, state)
    json.dump({"results": results}, sys.stdout, indent=2)
    print()
    return 1 if any(r["outcome"] == "failed" for r in results) else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vault", default=str(DEFAULT_VAULT))
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("list")
    pl.add_argument("--since")
    pl.add_argument("--days", type=int)
    pa = sub.add_parser("apply")
    pa.add_argument("--input")
    pa.add_argument("--dry-run", action="store_true")
    pa.add_argument("--existing-todos")
    args = p.parse_args()
    return cmd_list(args) if args.cmd == "list" else cmd_apply(args)


if __name__ == "__main__":
    sys.exit(main())
