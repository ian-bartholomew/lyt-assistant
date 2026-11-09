import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class TranscriptHookTest(unittest.TestCase):
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
