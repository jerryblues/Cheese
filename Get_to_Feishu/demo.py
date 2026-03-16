"""
Sync latest notes from Yinxiang shared (linked) notebooks.

Features:
- Cache shared notebook list and each notebook's latest note title.
- Optionally compare titles and only send updates.
- Optionally push to DingTalk via webhook.
- Convert ENML to plain text.
"""

from __future__ import annotations

import json
import sys
import inspect
import re
import html
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from collections import namedtuple

# Compatibility shim for Python 3.11+ where inspect.getargspec is removed.
# The Evernote SDK still calls inspect.getargspec in some versions.
if not hasattr(inspect, "getargspec"):
    ArgSpec = namedtuple("ArgSpec", ["args", "varargs", "keywords", "defaults"])

    def getargspec(func):  # type: ignore
        spec = inspect.getfullargspec(func)
        return ArgSpec(spec.args, spec.varargs, spec.varkw, spec.defaults)

    inspect.getargspec = getargspec  # type: ignore[attr-defined]

from evernote.api.client import EvernoteClient
from evernote.api.client import Store as EvernoteStore
from evernote.edam.notestore.NoteStore import Client as NoteStoreClient
from evernote.edam.notestore import NoteStore
from evernote.edam.type import ttypes as Types
from evernote.edam.error import ttypes as Errors

# Get your developer token from:
# https://app.yinxiang.com/api/DeveloperToken.action
DEV_TOKEN = "S=s10:U=1030989:E=19d18c7ea90:C=19cf4bb6600:P=1cd:A=en-devtoken:V=2:H=6628f588ea7f6ab10fb68e2f3cf794a6"

# LLM API key (reserved for future summary feature; not implemented yet)
LLM_API_KEY = ""

CACHE_PATH = "shared_notebooks_cache.json"

# Output/debug switches
PRINT_ENDPOINTS = True
PRINT_NOTE_TEXT_TO_CONSOLE = False

# Output file (one file for all notebooks)
OUTPUT_TEXT_PATH = "latest_shared_notes.txt"

# Filter rules
# If a note title contains this string, treat it as a "directory/index" note and skip it.
SKIP_TITLE_CONTAINS = "【"
# When searching for the "latest non-directory note", fetch up to this many notes.
MAX_NOTES_TO_SCAN_PER_NOTEBOOK = 10

# Only keep notes for today's date.
# Title prefix example: "25.1210丨100｜..."
ONLY_KEEP_TODAY = True


@dataclass
class SharedNotebookCacheItem:
    shareName: str
    linkedGuid: str
    shareKey: str
    linkedNoteStoreUrl: str
    latestTitle: str = ""
    latestNoteGuid: str = ""
    lastSentTitle: str = ""
    lastCheckedAt: int = 0
    lastSentAt: int = 0


def now_ts() -> int:
    return int(time.time())


def ensure_utf8_console() -> None:
    # Avoid UnicodeEncodeError on Windows consoles (e.g. GBK default).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def enml_to_text(enml: str) -> str:
    """
    Convert ENML/HTML-ish content to readable plain text (best-effort).
    """
    if not enml:
        return ""

    s = enml
    s = s.replace("\r\n", "\n").replace("\r", "\n")

    # Remove XML/DOCTYPE headers
    s = re.sub(r"(?is)^\s*<\?xml[^>]*\?>\s*", "", s)
    s = re.sub(r"(?is)^\s*<!DOCTYPE[^>]*>\s*", "", s)

    # Replace common block tags with newlines
    s = re.sub(r"(?is)<br\s*/?>", "\n", s)
    s = re.sub(r"(?is)</(div|p|tr|h1|h2|h3|h4|h5|h6)>", "\n", s)
    s = re.sub(r"(?is)<li[^>]*>", "- ", s)
    s = re.sub(r"(?is)</li>", "\n", s)

    # Drop non-text tags entirely
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", s)

    # Strip remaining tags
    s = re.sub(r"(?is)<[^>]+>", "", s)

    # Decode entities
    s = html.unescape(s)

    # Normalize whitespace/newlines
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def load_cache(cache_file: Path) -> dict[str, SharedNotebookCacheItem]:
    if not cache_file.exists():
        return {}
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return {}
    items: dict[str, SharedNotebookCacheItem] = {}
    for share_key, raw in (data.get("items") or {}).items():
        if not isinstance(raw, dict):
            continue
        try:
            items[share_key] = SharedNotebookCacheItem(**raw)
        except Exception:
            continue
    return items


def save_cache(cache_file: Path, items: dict[str, SharedNotebookCacheItem]) -> None:
    payload = {
        "updatedAt": now_ts(),
        "items": {k: asdict(v) for k, v in items.items()},
    }
    cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def get_personal_note_store(client: EvernoteClient, service_host: str):
    user_store = client.get_user_store()
    note_store_url = user_store.getNoteStoreUrl()
    if PRINT_ENDPOINTS:
        print("EDAM endpoints:")
        print(f"- user store url: https://{service_host}/edam/user")
        print(f"- personal note store url (from UserStore.getNoteStoreUrl): {note_store_url}")
    return EvernoteStore(DEV_TOKEN, NoteStoreClient, note_store_url)


def refresh_shared_notebooks(note_store) -> dict[str, SharedNotebookCacheItem]:
    linked = note_store.listLinkedNotebooks()
    out: dict[str, SharedNotebookCacheItem] = {}
    for ln in linked or []:
        share_key = getattr(ln, "shareKey", "") or ""
        if not share_key:
            continue
        out[share_key] = SharedNotebookCacheItem(
            shareName=getattr(ln, "shareName", "(no name)") or "(no name)",
            linkedGuid=getattr(ln, "guid", "") or "",
            shareKey=share_key,
            linkedNoteStoreUrl=getattr(ln, "noteStoreUrl", "") or "",
        )
    return out


def fetch_latest_from_store(note_store, notebook_guid: str):
    # Build filter: optionally limit to a specific notebook
    note_filter = NoteStore.NoteFilter()
    if notebook_guid:
        note_filter.notebookGuid = notebook_guid
    # Sort by updated time descending (latest first)
    note_filter.order = Types.NoteSortOrder.UPDATED
    note_filter.ascending = False

    # Only fetch one note (the latest)
    spec = NoteStore.NotesMetadataResultSpec()
    spec.includeTitle = True

    return note_store.findNotesMetadata(
        note_filter,
        0,  # offset
        MAX_NOTES_TO_SCAN_PER_NOTEBOOK,  # maxNotes
        spec,
    )


def get_shared_note_store(client: EvernoteClient, linked_note_store_url: str, share_key: str):
    bootstrap_store = EvernoteStore(client.token, NoteStoreClient, linked_note_store_url)
    auth = bootstrap_store.authenticateToSharedNotebook(share_key)
    note_store_url = getattr(auth, "noteStoreUrl", None) or linked_note_store_url
    if PRINT_ENDPOINTS:
        print("\nShared notebook auth flow:")
        print(f"- bootstrap noteStoreUrl: {linked_note_store_url}")
        print(f"- auth.noteStoreUrl: {getattr(auth, 'noteStoreUrl', None)}")
        print(f"- effective shared noteStoreUrl: {note_store_url}")
    return EvernoteStore(auth.authenticationToken, NoteStoreClient, note_store_url)


def get_latest_note_plain_text(note_store, note_guid: str) -> str:
    note = note_store.getNote(
        note_guid,
        True,   # withContent
        False,  # withResourcesData
        False,  # withResourcesRecognition
        False,  # withResourcesAlternateData
    )
    return enml_to_text(getattr(note, "content", "") or "")


def today_title_prefix() -> str:
    # Example: "25.1210" for 2025-12-10
    return time.strftime("%y.%m%d", time.localtime())


def extract_title_date_prefix(title: str) -> str:
    m = re.match(r"^(\d{2}\.\d{4})", title or "")
    return m.group(1) if m else ""


def main():
    ensure_utf8_console()

    if not DEV_TOKEN:
        print("Missing required configuration.")
        print("Please fill in at least:")
        print("  DEV_TOKEN  (your developer token)")
        sys.exit(1)

    service_host = "app.yinxiang.com"
    client = EvernoteClient(token=DEV_TOKEN, service_host=service_host, sandbox=False)
    personal_store = get_personal_note_store(client, service_host)

    cache_file = Path(__file__).with_name(CACHE_PATH)
    cache_items = load_cache(cache_file)

    # Always refresh shared notebook list every run
    fresh = refresh_shared_notebooks(personal_store)
    # merge into cache to keep latestTitle fields; lastSentTitle will be updated below
    for share_key, fresh_item in fresh.items():
        old = cache_items.get(share_key)
        if old:
            fresh_item.latestTitle = old.latestTitle
            fresh_item.latestNoteGuid = old.latestNoteGuid
            fresh_item.lastCheckedAt = old.lastCheckedAt
            fresh_item.lastSentAt = old.lastSentAt
        cache_items[share_key] = fresh_item
    save_cache(cache_file, cache_items)

    if not cache_items:
        print("No shared (linked) notebooks found.")
        return

    outputs: list[str] = []
    today_prefix = today_title_prefix()

    for share_key, item in sorted(cache_items.items(), key=lambda kv: kv[1].shareName):
        if not item.linkedNoteStoreUrl or not item.shareKey:
            continue

        try:
            shared_store = get_shared_note_store(client, item.linkedNoteStoreUrl, item.shareKey)
            notes_md = fetch_latest_from_store(shared_store, "")
        except Exception as e:
            print(f"\nFailed to read shared notebook '{item.shareName}' ({share_key}): {e}")
            continue

        item.lastCheckedAt = now_ts()
        if not getattr(notes_md, "notes", None):
            continue

        # Pick the latest note that is not a "directory/index" note.
        picked = None
        for n in notes_md.notes:
            t = getattr(n, "title", "") or ""
            if SKIP_TITLE_CONTAINS and SKIP_TITLE_CONTAINS in t:
                continue
            picked = n
            break

        if picked is None:
            continue

        latest_title = getattr(picked, "title", "") or ""
        latest_guid = getattr(picked, "guid", "") or ""

        previous_title = item.latestTitle
        item.latestTitle = latest_title
        item.latestNoteGuid = latest_guid

        # Keep only today's notes (based on the title prefix like "25.1210").
        if ONLY_KEEP_TODAY:
            if extract_title_date_prefix(latest_title) != today_prefix:
                item.lastSentTitle = ""
                continue

        plain = get_latest_note_plain_text(shared_store, latest_guid) if latest_guid else ""

        if PRINT_NOTE_TEXT_TO_CONSOLE:
            print(f"\n=== {item.shareName} ===")
            print(f"Title: {latest_title}")
            print(plain)

        outputs.append(
            "\n".join(
                [
                    f"=== {item.shareName} ===",
                    f"Title: {latest_title}",
                    plain,
                    "",
                ]
            )
        )

        # Update lastSentTitle only if we actually kept/saved this note today.
        item.lastSentTitle = latest_title
        item.lastSentAt = now_ts()

    if outputs:
        out_file = Path(__file__).with_name(OUTPUT_TEXT_PATH)
        out_file.write_text("\n".join(outputs).strip() + "\n", encoding="utf-8")

    save_cache(cache_file, cache_items)


if __name__ == "__main__":
    main()
