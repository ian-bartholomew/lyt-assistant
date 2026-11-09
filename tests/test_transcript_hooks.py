import importlib.util
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class TranscriptHookTest(unittest.TestCase):
    def setUp(self):
        state_dir = TemporaryDirectory()
        self.addCleanup(state_dir.cleanup)
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_INVOKED_BY"}
        env["LYT_STATE_DIR"] = state_dir.name
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def extract(self, filename: str, lines: list[str]):
        with TemporaryDirectory() as directory:
            transcript = Path(directory) / "transcript.jsonl"
            transcript.write_text("\n".join(lines))
            module = load_script(filename, filename)
            return module.extract_conversation_context(transcript)

    def test_extracts_claude_messages_and_skips_malformed_lines(self):
        lines = [
            json.dumps({"message": {"role": "user", "content": ["hello"]}}),
            "",
            "not json",
            "null",
            json.dumps([1, 2]),
            json.dumps({"type": "response_item", "payload": None}),
            json.dumps({"message": "not a dict"}),
            json.dumps(
                {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": "hi"},
                            {"type": "tool_use", "name": "Bash"},
                            {"type": "text", "text": None},
                        ],
                    }
                }
            ),
        ]
        for filename in ("session-end.py", "pre-compact.py"):
            with self.subTest(filename=filename):
                context, count = self.extract(filename, lines)
                self.assertEqual(count, 2)
                self.assertEqual(context, "**User:** hello\n\n**Assistant:** hi\n")

    def test_extracts_codex_messages(self):
        entries = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Fix the hook"}],
                },
            },
            {
                "type": "event_msg",
                "payload": {"type": "agent_message", "message": "duplicate"},
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Fixed"}],
                },
            },
        ]

        with TemporaryDirectory() as directory:
            transcript = Path(directory) / "rollout.jsonl"
            transcript.write_text("\n".join(json.dumps(entry) for entry in entries))

            for filename in ("session-end.py", "pre-compact.py"):
                with self.subTest(filename=filename):
                    module = load_script(filename, filename)
                    context, count = module.extract_conversation_context(transcript)
                    self.assertEqual(count, 2)
                    self.assertEqual(context, "**User:** Fix the hook\n\n**Assistant:** Fixed\n")


if __name__ == "__main__":
    unittest.main()
