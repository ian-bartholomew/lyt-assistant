#!/usr/bin/env python3
"""Run: python3 test_fes_support_cache.py"""
import json, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).parent
HELPER = HERE / "fes_support_cache.py"


def run_check(path):
    out = subprocess.run([sys.executable, str(HELPER), "check", str(path)],
                         capture_output=True, text=True)
    return json.loads(out.stdout)


def make_cache(path, age_seconds=0, corrupt=False, threads=None):
    if corrupt:
        path.write_text("{ not json")
        return
    import datetime
    gen = (datetime.datetime.now(datetime.timezone.utc)
           - datetime.timedelta(seconds=age_seconds)).isoformat()
    path.write_text(json.dumps({
        "generated_at": gen, "channel_id": "C06PUG6V6NT",
        "window_oldest": "1780902000",
        "threads": threads if threads is not None else {
            "1781011575.151529": {
                "parent": {"author": "Joey", "ts": "1781011575.151529",
                           "text": "migrations failing"},
                "replies": [{"author": "Peter", "ts": "1781012589.977669",
                             "text": "looking"}]}}}))


def test_trusted_fresh():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "cache.json"
        make_cache(p)
        r = run_check(p)
        assert r["trusted"] is True
        assert r["thread_count"] == 1
        assert "1781011575.151529" in r["ts_list"]


def test_untrusted_stale():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "cache.json"
        make_cache(p, age_seconds=7 * 3600)
        r = run_check(p)
        assert r["trusted"] is False and "stale" in r["reason"]


def test_untrusted_malformed():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "cache.json"
        make_cache(p, corrupt=True)
        r = run_check(p)
        assert r["trusted"] is False and "parse" in r["reason"]


def test_untrusted_missing():
    r = run_check("/nonexistent/cache.json")
    assert r["trusted"] is False and "missing" in r["reason"]


def test_untrusted_bad_shape():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "cache.json"
        make_cache(p, threads={"123.456": {"parent": {"no_ts": True}}})
        r = run_check(p)
        assert r["trusted"] is False and "shape" in r["reason"]


def test_get_hit_and_miss():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "cache.json"
        make_cache(p)
        hit = subprocess.run(
            [sys.executable, str(HELPER), "get", "1781011575.151529", str(p)],
            capture_output=True, text=True)
        assert hit.returncode == 0
        assert json.loads(hit.stdout)["parent"]["author"] == "Joey"
        miss = subprocess.run(
            [sys.executable, str(HELPER), "get", "999.000", str(p)],
            capture_output=True, text=True)
        assert miss.returncode == 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"{len(fns)} tests passed")
