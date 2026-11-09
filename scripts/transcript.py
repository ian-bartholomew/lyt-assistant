"""Conversation transcript extraction shared by lifecycle hooks."""

from __future__ import annotations

import json
from pathlib import Path


def extract_conversation_context(
    transcript_path: Path, max_turns: int = 30, max_context_chars: int = 15_000
) -> tuple[str, int]:
    """Extract recent user and assistant messages from Claude or Codex JSONL."""
    turns: list[str] = []

    with open(transcript_path, encoding="utf-8") as transcript:
        for line in transcript:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get("type") == "response_item":
                message = entry.get("payload", {})
                if message.get("type") != "message":
                    continue
            else:
                message = entry.get("message", entry)

            role = message.get("role", "") if isinstance(message, dict) else ""
            if role not in ("user", "assistant"):
                continue

            content = message.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict)
                    and block.get("type") in ("text", "input_text", "output_text")
                )

            if isinstance(content, str) and content.strip():
                label = "User" if role == "user" else "Assistant"
                turns.append(f"**{label}:** {content.strip()}\n")

    recent = turns[-max_turns:]
    context = "\n".join(recent)
    if len(context) > max_context_chars:
        context = context[-max_context_chars:]
        boundary = context.find("\n**")
        if boundary > 0:
            context = context[boundary + 1 :]

    return context, len(recent)
