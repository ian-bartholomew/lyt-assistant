#!/usr/bin/env python3
"""Tests for meeting_action_items.py. Run: python3 test_meeting_action_items.py"""
import json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meeting_action_items as mai


def test_normalize():
    # bullet marker + checkbox + bold prefix + bare prefix strip sequentially
    assert mai.normalize("- [ ] **Ian:** Action: do the thing") == "do the thing"
    assert mai.normalize("  * **Team / Kareem:** Discuss sprint planning.") == "discuss sprint planning."
    assert mai.normalize("- [x] Send the survey  today") == "send the survey today"
    assert mai.normalize("- Plain bullet with no prefix") == "plain bullet with no prefix"


def test_key_for():
    k = mai.key_for("2026-05-11-platform-standup", mai.normalize(
        "- [ ] **Ian:** Write up the remaining IDP plan"))
    assert k.startswith("2026-05-11-platform-standup::")
    assert len(k.split("::")[1]) == 12


def test_extract_assignee():
    assert mai.extract_assignee("- [ ] **Ian:** do x") == "Ian"
    assert mai.extract_assignee("- [ ] **Team / Peter+Rafael:** scope it") == "Team / Peter+Rafael"
    assert mai.extract_assignee("- [ ] Matt: send survey") == "Matt"
    assert mai.extract_assignee("- [ ] no prefix here") == ""


def test_should_include_assignee():
    assert mai.should_include_assignee("") is True            # no prefix: everyone's
    assert mai.should_include_assignee("Ian") is True
    assert mai.should_include_assignee("Team / Peter+Rafael") is True   # any part matches
    assert mai.should_include_assignee("Ian/Matt") is True
    assert mai.should_include_assignee("Matt") is False
    assert mai.should_include_assignee("Equity Comp team") is False     # exact match only
    assert mai.should_include_assignee("Rashief") is False


def test_suggest_due():
    assert mai.suggest_due_from_text("ship by 2026-06-01 latest") == "2026-06-01"
    assert mai.suggest_due_from_text("get it done by EOW") == "Friday"
    assert mai.suggest_due_from_text("close out by end of month") == "end of month"
    assert mai.suggest_due_from_text("send today") == "today"
    assert mai.suggest_due_from_text("circle back tomorrow") == "tomorrow"
    assert mai.suggest_due_from_text("revisit next week") == "next week"
    assert mai.suggest_due_from_text("demo on friday") == "friday"
    assert mai.suggest_due_from_text("in 3 days please") == "in 3 days"
    assert mai.suggest_due_from_text("due June 1") == "jun 1"
    assert mai.suggest_due_from_text("deliver by 3/4") == "3/4"
    assert mai.suggest_due_from_text("completed 3/4 of the backlog") == ""   # fraction guard
    assert mai.suggest_due_from_text("nothing datelike here") == ""


def test_suggest_title():
    short = mai.suggest_title("Do the thing")
    assert short == "Do the thing"
    long = mai.suggest_title("Write up the remaining IDP plan three of four epics as a one-pager Confluence page so the team can continue")
    assert len(long) <= 71  # 70 + ellipsis char
    assert long.endswith("…")


def test_extract_action_items():
    md = """# Summary

## 1. Action Items

- [ ] **Ian:** First item
- [ ] **Matt:** Second item

## Next Section

- not an action item
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(md)
    bullets = mai.extract_action_items(Path(f.name))
    assert len(bullets) == 2
    assert "First item" in bullets[0]


def test_list_end_to_end():
    fixture_vault = HERE / "test-fixtures" / "vault"
    out = subprocess.run(
        [sys.executable, str(HERE / "meeting_action_items.py"),
         "--vault", str(fixture_vault), "list", "--since", "2026-06-01"],
        capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    raws = [p["raw"] for p in data["pending"]]
    # included: Ian, joint Team/, no-prefix
    assert any("quarterly report" in r for r in raws)
    assert any("ARM runner" in r for r in raws)
    assert any("no assignee prefix" in r for r in raws)
    # excluded: Matt, Equity Comp team (exact-match rule)
    assert not any("survey" in r for r in raws)
    assert not any("grants" in r for r in raws)
    assert data["filtered_count"] == 2
    # checked bullet auto-reported, not pending
    assert len(data["auto_checked"]) == 1
    assert "offsite room" in data["auto_checked"][0]["raw"]
    # state-deduped item absent
    assert not any("Already-handled" in r for r in raws)
    # suggestions: due inferred from "by Friday"
    rpt = next(p for p in data["pending"] if "quarterly report" in p["raw"])
    assert rpt["suggested"]["due"].lower() == "friday"
    assert rpt["suggested"]["priority"] == "p2"
    assert "From meeting: standup (2026-06-01)" in rpt["suggested"]["description"]


def test_list_is_pure():
    fixture_vault = HERE / "test-fixtures" / "vault"
    state_path = fixture_vault / ".lyt-assistant" / "_action-item-state.json"
    before = state_path.read_text()
    subprocess.run(
        [sys.executable, str(HERE / "meeting_action_items.py"),
         "--vault", str(fixture_vault), "list", "--since", "2026-06-01"],
        capture_output=True, text=True, check=True)
    assert state_path.read_text() == before, "list must never write state"


def test_apply_dry_run():
    import shutil
    with tempfile.TemporaryDirectory() as td_dir:
        vault = Path(td_dir) / "vault"
        shutil.copytree(HERE / "test-fixtures" / "vault", vault)
        listing = json.loads(subprocess.run(
            [sys.executable, str(HERE / "meeting_action_items.py"),
             "--vault", str(vault), "list", "--since", "2026-06-01"],
            capture_output=True, text=True, check=True).stdout)
        item = next(p for p in listing["pending"]
                    if "quarterly report" in p["raw"])
        payload = {
            "auto_checked": listing["auto_checked"],
            "decisions": [
                {"key": item["key"], "meeting_dir": item["meeting_dir"],
                 "raw": item["raw"], "action": "todo",
                 "title": item["suggested"]["title"],
                 "description": item["suggested"]["description"],
                 "due": item["suggested"]["due"],
                 "priority": item["suggested"]["priority"]},
                {"key": "k2", "meeting_dir": "2026-06-01-standup",
                 "raw": "- [ ] x", "action": "dismiss"},
                {"key": "k3", "meeting_dir": "2026-06-01-standup",
                 "raw": "- [ ] y", "action": "skip"},
            ],
        }
        out = subprocess.run(
            [sys.executable, str(HERE / "meeting_action_items.py"),
             "--vault", str(vault), "apply", "--dry-run"],
            input=json.dumps(payload), capture_output=True, text=True,
            check=True)
        results = {r["key"]: r["outcome"]
                   for r in json.loads(out.stdout)["results"]}
        assert results[item["key"]] == "created"
        assert results["k2"] == "dismissed"
        assert results["k3"] == "skipped"
        state = json.loads(
            (vault / ".lyt-assistant" / "_action-item-state.json").read_text())
        assert state["items"][item["key"]]["status"] == "todoed"
        assert state["items"]["k2"]["status"] == "dismissed"
        assert "k3" not in state["items"]          # skip writes nothing
        assert state["items"][listing["auto_checked"][0]["key"]]["status"] == "todoed"
        assert state["last_run"] is not None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"{len(fns)} tests passed")
