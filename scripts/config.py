"""Path constants and configuration for the LYT Assistant knowledge base."""

import json
import os
from pathlib import Path
from datetime import datetime, timezone


# ── Plugin paths (where the code lives) ─────────────────────────────
COMPILER_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = COMPILER_DIR / "scripts"
AGENTS_FILE = COMPILER_DIR / "lib" / "agents-schema.md"


# ── State directory (writable, outside plugin cache) ────────────────

def _resolve_state_dir() -> Path:
    """Resolve the writable state directory.

    Resolution order:
    1. LYT_STATE_DIR environment variable
    2. ~/.local/share/lyt-assistant/ (XDG-compatible default)
    """
    env_val = os.environ.get("LYT_STATE_DIR", "").strip()
    if env_val:
        p = Path(env_val).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    default = Path.home() / ".local" / "share" / "lyt-assistant"
    default.mkdir(parents=True, exist_ok=True)
    return default


STATE_DIR = _resolve_state_dir()
STATE_FILE = STATE_DIR / "state.json"
REPORTS_DIR = STATE_DIR / "reports"
FLUSH_LOG = STATE_DIR / "flush.log"
COMPILE_LOG = STATE_DIR / "compile.log"


# ── Vault resolution ─────────────────────────────────────────────────

def _resolve_vault_dir() -> Path:
    """Resolve the vault directory from env var, config file, or fallback.

    Resolution order:
    1. MEMORY_VAULT_DIR environment variable
    2. State dir vault-config.json (user-writable location)
    3. scripts/vault-config.json (dev mode fallback)
    4. Fallback to COMPILER_DIR (original single-repo layout)
    """
    # 1. Environment variable
    env_val = os.environ.get("MEMORY_VAULT_DIR", "").strip()
    if env_val:
        return Path(env_val).expanduser().resolve()

    # 2. Config file in state dir (preferred for installed plugins)
    for config_dir in [STATE_DIR, SCRIPTS_DIR]:
        config_file = config_dir / "vault-config.json"
        if config_file.exists():
            try:
                data = json.loads(config_file.read_text(encoding="utf-8"))
                vault_path = data.get("vault_dir", "").strip()
                if vault_path:
                    return Path(vault_path).expanduser().resolve()
            except (json.JSONDecodeError, OSError):
                pass

    # 3. Fallback to compiler dir (original layout)
    return COMPILER_DIR


VAULT_DIR = _resolve_vault_dir()


# ── Vault paths (where the data lives) ───────────────────────────────

# Wiki structure — adapts to vault layout
# External vault: wiki/ with _index.md, _log.md, _indexes/
# Fallback (no vault configured): knowledge/ with index.md, log.md
_is_external_vault = VAULT_DIR != COMPILER_DIR

if _is_external_vault:
    # External vault uses the Karpathy three-layer architecture:
    #   raw/   (source)  →  wiki/  (compiled)  →  projects/  (active work)
    RAW_DIR = VAULT_DIR / "raw"
    DAILY_DIR = RAW_DIR / "daily"
    CLIPPINGS_DIR = RAW_DIR / "clippings"
    SUPPORT_LEARNINGS_DIR = RAW_DIR / "support_learnings"
    INTERNAL_LEARNINGS_DIR = RAW_DIR / "internal_learnings"
    DAILY_NOTES_DIR = RAW_DIR / "daily_notes"
    DOCS_DIR = RAW_DIR / "docs"
    WIKI_DIR = VAULT_DIR / "wiki"
    INDEX_FILE = WIKI_DIR / "_index.md"
    LOG_FILE = WIKI_DIR / "_log.md"
else:
    RAW_DIR = VAULT_DIR
    DAILY_DIR = VAULT_DIR / "daily"
    CLIPPINGS_DIR = VAULT_DIR / "clippings"
    SUPPORT_LEARNINGS_DIR = VAULT_DIR / "support_learnings"
    INTERNAL_LEARNINGS_DIR = VAULT_DIR / "internal_learnings"
    DAILY_NOTES_DIR = VAULT_DIR / "daily_notes"
    DOCS_DIR = VAULT_DIR / "docs"
    WIKI_DIR = VAULT_DIR / "knowledge"
    INDEX_FILE = WIKI_DIR / "index.md"
    LOG_FILE = WIKI_DIR / "log.md"

CONCEPTS_DIR = WIKI_DIR / "concepts"
GUIDES_DIR = WIKI_DIR / "guides"
COMPANY_DIR = WIKI_DIR / "company"
LEARNING_DIR = WIKI_DIR / "learning"
QA_DIR = WIKI_DIR / "qa"
CONNECTIONS_DIR = WIKI_DIR / "connections"
INDEXES_DIR = WIKI_DIR / "_indexes"
MEETINGS_DIR = VAULT_DIR / "meetings"

# Article subdirectories to scan — external vault has more folders
if _is_external_vault:
    ARTICLE_SUBDIRS = [CONCEPTS_DIR, GUIDES_DIR, COMPANY_DIR, LEARNING_DIR, QA_DIR]
else:
    ARTICLE_SUBDIRS = [CONCEPTS_DIR, CONNECTIONS_DIR, QA_DIR]

# ── Timezone ───────────────────────────────────────────────────────────
TIMEZONE = "America/Chicago"


def now_iso() -> str:
    """Current time in ISO 8601 format."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def today_iso() -> str:
    """Current date in ISO 8601 format."""
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
