"""
Sync latest notes from Yinxiang shared (linked) notebooks.

Features:
- to be updated
"""

from __future__ import annotations

import json
import sys
import inspect
import re
import html
import time
import hmac
import base64
import hashlib
import urllib.parse
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import namedtuple
from urllib import request
from openai import OpenAI

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

# --- CONFIGURATION ---

def load_config():
    # config.json moved to config/ folder
    config_path = Path(__file__).parent / "config" / "config.json"
    if not config_path.exists():
        print(f"FATAL: config.json not found at {config_path}")
        sys.exit(1)
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FATAL: Failed to load config.json: {e}")
        sys.exit(1)

config = load_config()

# Secrets (from config.json)
DEV_TOKEN = config.get("DEV_TOKEN", "")
DINGTALK_WEBHOOK = config.get("DINGTALK_WEBHOOK", "")
DINGTALK_SECRET = config.get("DINGTALK_SECRET", "")
DINGTALK_WEBHOOK_NOTIFICATION = config.get("DINGTALK_WEBHOOK_NOTIFICATION", "")
DOWNLOAD_DIR = config.get("DOWNLOAD_DIR", "D:\\Get")

# LLM Configuration
active_llm_key = config.get("ACTIVE_LLM", "qwen")
llm_configs = config.get("LLM_CONFIGS", {})
active_llm_config = llm_configs.get(active_llm_key, {})

LLM_API_KEY = active_llm_config.get("API_KEY", "")
LLM_MODEL = active_llm_config.get("MODEL", "qwen-max")
LLM_BASE_URL = active_llm_config.get("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# Output files (moved to output/ folder)
OUTPUT_DIR = Path(__file__).parent / "output"
NOTEBOOK_LIST = OUTPUT_DIR / "notebook_list.json"
NOTE_DAILY_FULL = OUTPUT_DIR / "note_daily_full.txt"
NOTE_DAILY_MAIN = OUTPUT_DIR / "note_daily_main.txt"

# Debug/Output switches
PRINT_ENDPOINTS = False
PRINT_NOTE_TEXT_TO_CONSOLE = False
PRINT_DINGTALK_RESPONSE = False

# Filter rules
SKIP_TITLE_CONTAINS = "目录】"
MAX_NOTES_TO_SCAN_PER_NOTEBOOK = 5
# True: sync today's note; False: sync the latest available note
SYNC_TODAY_ONLY = False

# --- END CONFIGURATION ---


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
    archivedNote: bool = False
    syncedNotes: dict[str, bool] = None # {title: mp3Downloaded}

    def __post_init__(self):
        if self.syncedNotes is None:
            self.syncedNotes = {}
        # Migration from legacy syncedNoteTitles list if exists (handled during load_cache)
        if self.lastSentTitle and self.lastSentTitle not in self.syncedNotes:
            self.syncedNotes[self.lastSentTitle] = True # Assume old ones were fully synced


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


def load_cache(cache_file: Path) -> tuple[dict[str, SharedNotebookCacheItem], list[str]]:
    if not cache_file.exists():
        return {}, []
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return {}, []
    items: dict[str, SharedNotebookCacheItem] = {}
    for share_key, raw in (data.get("items") or {}).items():
        if not isinstance(raw, dict):
            continue
        
        # Convert string timestamps back to integers
        if isinstance(raw.get("lastCheckedAt"), str):
            try:
                # Try to parse the string timestamp back to integer
                # If it's a readable format, convert to timestamp
                # Otherwise, use current time
                raw["lastCheckedAt"] = int(time.mktime(time.strptime(raw["lastCheckedAt"], "%Y-%m-%d %H:%M:%S")))
            except Exception:
                raw["lastCheckedAt"] = now_ts()
        if isinstance(raw.get("lastSentAt"), str):
            try:
                raw["lastSentAt"] = int(time.mktime(time.strptime(raw["lastSentAt"], "%Y-%m-%d %H:%M:%S")))
            except Exception:
                raw["lastSentAt"] = now_ts()
        
        # Migration from syncedNoteTitles (list) to syncedNotes (dict)
        legacy_titles = raw.pop("syncedNoteTitles", [])
        if "syncedNotes" not in raw:
            raw["syncedNotes"] = {t: True for t in legacy_titles}
        
        try:
            items[share_key] = SharedNotebookCacheItem(**raw)
        except Exception:
            continue
    synced_dates = data.get("syncedDates") or []
    return items, synced_dates


def save_cache(cache_file: Path, items: dict[str, SharedNotebookCacheItem], synced_dates: list[str]) -> None:
    # Only keep the last 10 dates
    if len(synced_dates) > 10:
        synced_dates = synced_dates[-10:]
    
    # Process items for saving
    processed_items = {}
    for k, v in items.items():
        item_dict = asdict(v)
        
        # Convert timestamps to readable format (UTC+8)
        if item_dict.get("lastCheckedAt"):
            item_dict["lastCheckedAt"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item_dict["lastCheckedAt"]))
        if item_dict.get("lastSentAt"):
            item_dict["lastSentAt"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item_dict["lastSentAt"]))
        
        # Update linkedNoteStoreUrl to use web format
        latest_note_guid = item_dict.get("latestNoteGuid", "")
        if latest_note_guid:
            item_dict["linkedNoteStoreUrl"] = f"https://app.yinxiang.com/shard/s21/nl/25729210/{latest_note_guid}"
        
        # Limit syncedNotes to last 10 items (FIFO)
        synced_notes = item_dict.get("syncedNotes", {})
        if len(synced_notes) > 10:
            # Convert to list, keep last 10, then convert back to dict
            sorted_notes = list(synced_notes.items())
            item_dict["syncedNotes"] = dict(sorted_notes[-10:])
        
        processed_items[k] = item_dict
    
    payload = {
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "syncedDates": synced_dates,
        "items": processed_items,
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
    current_time = now_ts()
    for ln in linked or []:
        share_key = getattr(ln, "shareKey", "") or ""
        if not share_key:
            continue
        out[share_key] = SharedNotebookCacheItem(
            shareName=getattr(ln, "shareName", "(no name)") or "(no name)",
            linkedGuid=getattr(ln, "guid", "") or "",
            shareKey=share_key,
            linkedNoteStoreUrl=getattr(ln, "noteStoreUrl", "") or "",
            lastSentAt=current_time # Initialize to now for new notebooks
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

def download_mp3_attachments(note, download_dir: str) -> tuple[bool, bool]:
    """
    Find and download .mp3 resources from the note.
    Returns (download_success, has_mp3)
    - download_success: True if all MP3s were successfully downloaded or already exist
    - has_mp3: True if at least one MP3 was found
    """
    if not note or not getattr(note, "resources", None):
        return True, False # No resources, but consider it "done" for this check

    path = Path(download_dir)
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating download directory {download_dir}: {e}")
            return False, False

    has_mp3 = False
    all_success = True
    for res in note.resources:
        mime = getattr(res, "mime", "")
        filename = ""
        if getattr(res, "attributes", None):
            filename = getattr(res.attributes, "fileName", "")
        
        # Check if it's an MP3 by mime type or extension
        is_mp3 = "audio/mpeg" in mime or (filename and filename.lower().endswith(".mp3"))
        
        if is_mp3:
            has_mp3 = True
            if not filename:
                filename = f"attachment_{res.guid[:8]}.mp3"
            
            # Skip files with "[1.5倍速]" in the name
            if "[1.5倍速]" in filename:
                # print(f"Skipping 1.5x speed file: {filename}")
                continue
            
            dest = path / filename
            if dest.exists():
                # print(f"File already exists, skipping: {filename}")
                continue
            
            # print(f"    Downloading MP3 attachment: {filename}...")
            if getattr(res, "data", None) and getattr(res.data, "body", None):
                try:
                    dest.write_bytes(res.data.body)
                    print(f"    Saved to {dest}")
                except Exception as e:
                    print(f"Failed to save {filename}: {e}")
                    all_success = False
            else:
                all_success = False

    return all_success, has_mp3


def today_title_prefix() -> str:
    # Example: "25.1210" for 2025-12-10
    # return "26.0317"
    return time.strftime("%y.%m%d", time.localtime())


def extract_title_date_prefix(title: str) -> str:
    m = re.match(r"^(\d{2}\.\d{4})", title or "")
    return m.group(1) if m else ""


def summarize_text(text: str) -> str:
    """
    Summarize the given text using an LLM (OpenAI-compatible API).
    """
    if not LLM_API_KEY or not text:
        return ""

    # Truncate extremely long text to avoid timeouts
    if len(text) > 30000:
        text = text[:30000] + "...(内容过长，已截断)"

    prompt_template_path = Path(__file__).parent / "config" / "prompt.md"
    try:
        prompt_template = prompt_template_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        print(f"Warning: Failed to load prompt.md, using default prompt. Error: {e}")
        prompt_template = "请为以下文章写一个200字左右的总结和摘要："

    max_retries = 3
    error_message = ""
    for attempt in range(max_retries):
        try:
            # Branch 1: Use OpenAI client (e.g., for megallm or deepseek)
            if active_llm_key != "qwen":
                client = OpenAI(
                    base_url=LLM_BASE_URL,
                    api_key=LLM_API_KEY
                )
                response = client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {"role": "system", "content": "你是一个擅长提炼文章精华的助手。"},
                        {"role": "user", "content": f"{prompt_template}\n\n{text}"}
                    ],
                    temperature=0.7,
                    timeout=120
                )
                return response.choices[0].message.content.strip()
            
            # Branch 2: Use urllib.request (original qwen branch)
            else:
                url = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"
                prompt = f"{prompt_template}\n\n{text}"
                body = json.dumps({
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个擅长提炼文章精华的助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                }, ensure_ascii=False).encode("utf-8")

                req = request.Request(
                    url,
                    data=body,
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "Authorization": f"Bearer {LLM_API_KEY}"
                    },
                    method="POST",
                )
                with request.urlopen(req, timeout=120) as resp:
                    resp_body = resp.read().decode("utf-8", errors="replace")
                    data = json.loads(resp_body)
                    summary = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return summary.strip()

        except Exception as e:
            error_message = str(e)
            if "timeout" in error_message.lower() and attempt < max_retries - 1:
                print(f"LLM ({active_llm_key}) summarization timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                time.sleep(2)
                continue
            print(f"\nLLM ({active_llm_key}) summarization failed: {error_message}")
            break
    # Return error message as summary if all attempts failed
    if error_message:
        return f"LLM error: {error_message}"
    return ""


def post_dingtalk_text(webhook: str, content: str, secret: str = None) -> None:
    if not webhook:
        return
    url = webhook
    # Use provided secret or fall back to DINGTALK_SECRET
    effective_secret = secret if secret is not None else DINGTALK_SECRET
    
    if effective_secret:
        ts = str(int(time.time() * 1000))
        string_to_sign = f"{ts}\n{effective_secret}".encode("utf-8")
        hmac_code = hmac.new(effective_secret.encode("utf-8"), string_to_sign, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}timestamp={ts}&sign={sign}"
    body = json.dumps({"msgtype": "text", "text": {"content": content}}, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as resp:
            resp_body = resp.read().decode("utf-8", errors="replace")
            if PRINT_DINGTALK_RESPONSE:
                print("\nDingTalk response:")
                print(resp_body)
    except Exception as e:
        # Optional feature: do not fail the whole run if DingTalk fails.
        print(f"\nDingTalk webhook send failed (ignored): {e}")


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

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = NOTEBOOK_LIST
    cache_items, synced_dates = load_cache(cache_file)

    today_prefix = today_title_prefix()
    if SYNC_TODAY_ONLY and today_prefix in synced_dates:
        print(f"{today_prefix} already synced")
        return

    # Always refresh shared notebook list every run
    fresh = refresh_shared_notebooks(personal_store)
    # merge into cache to keep history fields
    for share_key, fresh_item in fresh.items():
        old = cache_items.get(share_key)
        if old:
            fresh_item.latestTitle = old.latestTitle
            fresh_item.latestNoteGuid = old.latestNoteGuid
            fresh_item.lastCheckedAt = old.lastCheckedAt
            fresh_item.lastSentAt = old.lastSentAt
            fresh_item.lastSentTitle = old.lastSentTitle
            fresh_item.syncedNotes = getattr(old, "syncedNotes", {})
            fresh_item.archivedNote = old.archivedNote
        cache_items[share_key] = fresh_item
    save_cache(cache_file, cache_items, synced_dates)

    if not cache_items:
        print("No shared (linked) notebooks found.")
        return

    outputs: list[str] = []
    main_contents: list[str] = []
    notification_sent = False

    # Track if all active notebooks have today's note synced
    all_active_synced_today = True

    # Debug: Print all notebooks
    print(f"\nProcessing {len(cache_items)} notebooks:")
    for share_key, item in sorted(cache_items.items(), key=lambda kv: kv[1].shareName):
        print(f"  - {item.shareName} (shareKey: {share_key})")
    
    for share_key, item in sorted(cache_items.items(), key=lambda kv: kv[1].shareName):
        try:
            print(f"\nProcessing notebook: {item.shareName} (shareKey: {share_key})")
            if not item.linkedNoteStoreUrl or not item.shareKey:
                print(f"  Skipped: missing linkedNoteStoreUrl or shareKey")
                continue
            
            # Skip archived notebooks
            if item.archivedNote:
                print(f"  Skipped: archived")
                continue

            try:
                shared_store = get_shared_note_store(client, item.linkedNoteStoreUrl, item.shareKey)
                # Use empty string to get all notes, then filter on client side
                notes_md = fetch_latest_from_store(shared_store, "")
            except Exception as e:
                print(f"\nFailed to read shared notebook '{item.shareName}' ({share_key}): {e}")
                all_active_synced_today = False
                continue
            
            try:
                item.lastCheckedAt = now_ts()
                if not getattr(notes_md, "notes", None):
                    print(f"\n{item.shareName} - no update")
                    all_active_synced_today = False
                    continue

                # Debug: Print number of notes found
                print(f"\n{item.shareName} - found {len(notes_md.notes)} notes")

                # Process notes (from newest to oldest in API result)
                to_sync_notes = []
                
                for n in notes_md.notes:
                    t = getattr(n, "title", "") or ""
                    # print(f"  - Note: {t}")
                    
                    # 1. Skip index notes
                    if SKIP_TITLE_CONTAINS and SKIP_TITLE_CONTAINS in t:
                        # print(f"    Skipped: contains {SKIP_TITLE_CONTAINS}")
                        continue
                    
                    # 2. Extract and check date prefix (yy.mmdd)
                    date_prefix = extract_title_date_prefix(t)
                    if not date_prefix:
                        # print(f"    Skipped: no date prefix")
                        continue
                    
                    
                    
                    # 4. Check sync status
                    is_synced = t in item.syncedNotes
                    mp3_status = item.syncedNotes.get(t, False)

                    # Skip if already downloaded or marked as no_mp3
                    if mp3_status in ["downloaded", "no_mp3"]:
                        # Fully done, stop if this is the lastSentTitle
                        if t == item.lastSentTitle:
                            print(f"    Stopping: reached last sent title")
                            break
                        print(f"    Skipped: already synced")
                        continue

                    to_sync_notes.append(n)
                    print(f"    Added to sync list")

                print(f"  Total notes to sync: {len(to_sync_notes)}")

                if not to_sync_notes:
                    continue

                # Process from oldest to newest (to maintain order in outputs)
                to_sync_notes.reverse()

                for picked in to_sync_notes:
                    try:
                        latest_title = getattr(picked, "title", "") or ""
                        latest_guid = getattr(picked, "guid", "") or ""
                        
                        print(f"  Processing note: {latest_title} (guid: {latest_guid})")
                        
                        is_synced = latest_title in item.syncedNotes
                        mp3_status = item.syncedNotes.get(latest_title, False)
                        download_success = False

                        # 1. If MP3 not done, try downloading (even if text is synced)
                        if mp3_status not in ["downloaded", "no_mp3"]:
                            print(f"    Fetching note with resources for MP3 download: {latest_title}")
                            try:
                                # 获取包含资源数据的笔记
                                note = shared_store.getNote(latest_guid, True, True, False, False)
                                print(f"    Downloading MP3 attachments for: {latest_title}")
                                download_success, has_mp3 = download_mp3_attachments(note, DOWNLOAD_DIR)
                                
                                # Update status based on result
                                if has_mp3:
                                    item.syncedNotes[latest_title] = "downloaded"
                                else:
                                    # Check if this is the second time we've checked and found no MP3
                                    if isinstance(mp3_status, int):
                                        if mp3_status >= 1:
                                            # Second check with no MP3, mark as no_mp3
                                            item.syncedNotes[latest_title] = "no_mp3"
                                        else:
                                            # First check with no MP3, increment counter
                                            item.syncedNotes[latest_title] = mp3_status + 1
                                    else:
                                        # First check with no MP3, start counter
                                        item.syncedNotes[latest_title] = 1
                            except Exception as e:
                                print(f"    Error downloading MP3 attachments: {e}")
                                # On error, don't increment counter, just leave as is or set to 0
                                if not isinstance(mp3_status, (int, str)):
                                    item.syncedNotes[latest_title] = 0
                            
                            # If text was already synced, we are done with this note
                            if is_synced:
                                print(f"{item.shareName} - {latest_title} - MP3 catch-up {'successful' if download_success else 'failed'}")
                                continue
                        else:
                            # 文本已同步但MP3未完成，获取包含资源的笔记
                            print(f"    Fetching note for text: {latest_title}")
                            try:
                                note = shared_store.getNote(latest_guid, True, False, False, False)
                            except Exception as e:
                                print(f"    Error fetching note: {e}")
                                continue

                        # 2. Process Text (only if not synced)
                        print(f"    Processing text for: {latest_title}")
                        try:
                            plain = enml_to_text(getattr(note, "content", "") or "")
                        except Exception as e:
                            print(f"    Error processing text: {e}")
                            continue
                        
                        parts = plain.split("用户留言", 1)
                        main_content = parts[0].strip()

                        summary = ""
                        if main_content:
                            print(f"    Summarizing: {latest_title}...")
                            summary = summarize_text(main_content)

                        # --- DingTalk Notification ---
                        if summary:
                            clean_share_name = item.shareName.replace("《", "").replace("》", "")
                            if "￥" in clean_share_name:
                                clean_share_name = clean_share_name.split("￥")[0].strip()
                            
                            dingtalk_msg = f"{latest_title} - {clean_share_name}\n\n{summary}"
                            post_dingtalk_text(DINGTALK_WEBHOOK, dingtalk_msg)

                        # --- File Saving ---
                        print(f"    Saving note: {latest_title}")
                        main_contents.append(main_content)
                        
                        lines = [
                            f"=== {item.shareName} ===",
                            f"Title: {latest_title}",
                            f"Link: https://app.yinxiang.com/shard/s21/nl/25729210/{latest_guid}" if latest_guid else "Link: https://app.yinxiang.com/shard/s21/nl/25729210",
                        ]
                        if summary:
                            lines.append(f"Summary: {summary}\n")
                        lines.extend([plain, ""])
                        block = "\n".join(lines)
                        outputs.append(block)

                        # Mark text as synced (MP3 status already updated above)
                        item.lastSentTitle = latest_title
                        item.lastSentAt = now_ts()
                        item.latestTitle = latest_title
                        item.latestNoteGuid = latest_guid
                        
                        print(f"{item.shareName} - {latest_title} - Text + MP3 updated")
                    except Exception as e:
                        print(f"\nError processing note '{latest_title}': {e}")
                        import traceback
                        traceback.print_exc()
                        continue

                # Send notification once if there are new notes to sync
                if to_sync_notes and not notification_sent:
                    print(f"\nNew notes detected. Sending update notification...")
                    post_dingtalk_text(DINGTALK_WEBHOOK_NOTIFICATION, "note updated", secret="")
                    notification_sent = True
            except Exception as e:
                print(f"\nError processing notebook '{item.shareName}' ({share_key}): {e}")
                import traceback
                traceback.print_exc()
                continue
        except Exception as e:
            print(f"\nError processing notebook '{item.shareName}' ({share_key}): {e}")
            import traceback
            traceback.print_exc()
            continue

    # Finalize and save
    if outputs:
        out_file = NOTE_DAILY_FULL
        out_file.write_text("\n".join(outputs).strip() + "\n", encoding="utf-8")
        
        # Trigger sync_note.py since new notes were written
        processor_path = Path(__file__).parent / "sync_note.py"
        if processor_path.exists():
            print(f"\nTriggering {processor_path.name}...")
            try:
                subprocess.run([sys.executable, str(processor_path)], check=True)
                # print(f"Triggering {processor_path.name} done")
            except subprocess.CalledProcessError as e:
                print(f"Error: Processor script failed: {e}")
        else:
            print(f"Warning: Processor script not found at {processor_path}")

    if main_contents:
        main_content_file = NOTE_DAILY_MAIN
        main_content_file.write_text("\n\n---\n\n".join(main_contents).strip() + "\n", encoding="utf-8")

    # Update archivedNote status for all notebooks
    thirty_days_sec = 30 * 24 * 3600
    current_time = now_ts()
    for item in cache_items.values():
        if item.archivedNote:
            continue
        # User said: "如果这个笔记本最近30天，lastSentTitle 都为空"
        # This means no new note has been sent for 30 days.
        if (current_time - item.lastSentAt) > thirty_days_sec:
            item.archivedNote = True
            print(f"Archiving inactive notebook: {item.shareName}")



    save_cache(cache_file, cache_items, synced_dates)
    print(f"\nAll Set!\n")


if __name__ == "__main__":
    main()
