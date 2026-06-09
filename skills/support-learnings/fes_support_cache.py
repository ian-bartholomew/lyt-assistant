#!/usr/bin/env python3
"""Trust-check and per-thread lookup for the EOD #fes-platform-support
thread cache (/tmp/eod-fes-support-cache.json).

VENDORED in two places; keep them byte-identical:
  - lyt-assistant: skills/support-learnings/fes_support_cache.py
  - fes-platform-claude: plugins/fes-support-learnings/skills/fes-support-learnings/fes_support_cache.py

Scope is capped at parse + trust + lookup. The producer (end-of-day's
build_cache.py) owns assembly and validation at write time.

Usage:
  python3 fes_support_cache.py check [path]   -> JSON {trusted, reason, thread_count, ts_list}
  python3 fes_support_cache.py get <ts> [path] -> thread JSON, exit 1 on miss/untrusted
"""
import json
import sys
from datetime import datetime, timezone

DEFAULT_PATH = "/tmp/eod-fes-support-cache.json"
MAX_AGE_SECONDS = 6 * 3600


def load(path: str):
    """Return (cache_dict, "") if trusted, else (None, reason).

    Trust requires: file exists, valid JSON, required keys present,
    generated_at is a timezone-aware ISO-8601 timestamp within
    MAX_AGE_SECONDS of now, and every thread has a parent with ts and text.
    A naive generated_at (no UTC offset) is treated as untrusted with a
    reason starting "shape:" because the timezone-aware age comparison
    would raise TypeError.
    """
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        return None, "missing: no cache file"
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return None, f"parse: {e}"
    if not isinstance(data, dict):
        return None, "shape: top level is not an object"
    for k in ("generated_at", "channel_id", "threads"):
        if k not in data:
            return None, f"shape: missing key {k}"
    try:
        gen = datetime.fromisoformat(str(data["generated_at"]).replace("Z", "+00:00"))
    except ValueError:
        return None, "shape: generated_at is not ISO-8601"
    try:
        age = (datetime.now(timezone.utc) - gen).total_seconds()
    except TypeError:
        return None, "shape: generated_at has no timezone offset"
    if age > MAX_AGE_SECONDS:
        return None, f"stale: {int(age)}s old (max {MAX_AGE_SECONDS})"
    threads = data["threads"]
    if not isinstance(threads, dict):
        return None, "shape: threads is not an object"
    for ts, t in threads.items():
        parent = t.get("parent") if isinstance(t, dict) else None
        if not isinstance(parent, dict) or "ts" not in parent or "text" not in parent:
            return None, f"shape: thread {ts} parent lacks ts/text"
    return data, ""


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] not in ("check", "get"):
        print(__doc__, file=sys.stderr)
        return 2
    if args[0] == "check":
        path = args[1] if len(args) > 1 else DEFAULT_PATH
        cache, reason = load(path)
        out = {"trusted": cache is not None, "reason": reason,
               "thread_count": len(cache["threads"]) if cache else 0,
               "ts_list": sorted(cache["threads"]) if cache else []}
        json.dump(out, sys.stdout)
        print()
        return 0
    # get <ts> [path]
    if len(args) < 2:
        print("get requires a ts", file=sys.stderr)
        return 2
    ts = args[1]
    path = args[2] if len(args) > 2 else DEFAULT_PATH
    cache, reason = load(path)
    if cache is None:
        print(f"untrusted cache: {reason}", file=sys.stderr)
        return 1
    thread = cache["threads"].get(ts)
    if thread is None:
        print(f"miss: {ts}", file=sys.stderr)
        return 1
    json.dump(thread, sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
