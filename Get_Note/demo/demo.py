"""
Sync latest notes from a specific Yinxiang shared notebook.

This is a demo version that syncs only one notebook defined in config.json.
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
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import namedtuple
from urllib import request
from openai import OpenAI

# Compatibility shim for Python 3.11+
if not hasattr(inspect, "getargspec"):
    ArgSpec = namedtuple("ArgSpec", ["args", "varargs", "keywords", "defaults"])
    def getargspec(func):
        spec = inspect.getfullargspec(func)
        return ArgSpec(spec.args, spec.varargs, spec.varkw, spec.defaults)
    inspect.getargspec = getargspec

from evernote.api.client import EvernoteClient
from evernote.api.client import Store as EvernoteStore
from evernote.edam.notestore.NoteStore import Client as NoteStoreClient
from evernote.edam.notestore import NoteStore
from evernote.edam.type import ttypes as Types
from evernote.edam.error import ttypes as Errors

# --- CONFIGURATION ---

def load_config():
    # Go up one level to find the config file
    config_path = Path(__file__).parent.parent / "config.json"
    if not config_path.exists():
        print("FATAL: config.json not found in parent directory.")
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
DEMO_NOTEBOOK = config.get("DEMO_NOTEBOOK", {})

# LLM Configuration
active_llm_key = config.get("ACTIVE_LLM", "qwen")
llm_configs = config.get("LLM_CONFIGS", {})
active_llm_config = llm_configs.get(active_llm_key, {})

LLM_API_KEY = active_llm_config.get("API_KEY", "")
LLM_MODEL = active_llm_config.get("MODEL", "qwen-max")
LLM_BASE_URL = active_llm_config.get("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# Output files (local to this script's directory)
NOTE_DAILY_FULL = "demo_note_full.txt"
NOTE_DAILY_MAIN = "demo_note_main.txt"

# Debug/Output switches
PRINT_ENDPOINTS = False
PRINT_NOTE_TEXT_TO_CONSOLE = False
PRINT_DINGTALK_RESPONSE = False

# Filter rules
SKIP_TITLE_CONTAINS = "【"
MAX_NOTES_TO_SCAN_PER_NOTEBOOK = 10
# True: sync today's note; False: sync the latest available note
SYNC_TODAY_ONLY = True

# --- END CONFIGURATION ---


@dataclass
class SharedNotebookCacheItem:
    shareName: str
    shareKey: str
    linkedNoteStoreUrl: str
    latestTitle: str = ""
    latestNoteGuid: str = ""
    lastSentTitle: str = ""
    lastCheckedAt: int = 0
    lastSentAt: int = 0
    archivedNote: bool = False
    mp3Downloaded: bool = False


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
        
    payload = {
        "updatedAt": int(time.time()),
        "syncedDates": synced_dates,
        "items": {k: asdict(v) for k, v in items.items()},
    }
    cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def now_ts() -> int:
    return int(time.time())

def ensure_utf8_console() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def enml_to_text(enml: str) -> str:
    if not enml:
        return ""
    s = enml.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"(?is)^\s*<\?xml[^>]*\?>\s*", "", s)
    s = re.sub(r"(?is)^\s*<!DOCTYPE[^>]*>\s*", "", s)
    s = re.sub(r"(?is)<br\s*/?>", "\n", s)
    s = re.sub(r"(?is)</(div|p|tr|h1|h2|h3|h4|h5|h6)>", "\n", s)
    s = re.sub(r"(?is)<li[^>]*>", "- ", s)
    s = re.sub(r"(?is)</li>", "\n", s)
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", s)
    s = re.sub(r"(?is)<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def fetch_latest_from_store(note_store, notebook_guid: str):
    note_filter = NoteStore.NoteFilter(order=Types.NoteSortOrder.UPDATED, ascending=False)
    if notebook_guid:
        note_filter.notebookGuid = notebook_guid
    spec = NoteStore.NotesMetadataResultSpec(includeTitle=True)
    return note_store.findNotesMetadata(note_filter, 0, MAX_NOTES_TO_SCAN_PER_NOTEBOOK, spec)

def get_shared_note_store(client: EvernoteClient, linked_note_store_url: str, share_key: str):
    bootstrap_store = EvernoteStore(client.token, NoteStoreClient, linked_note_store_url)
    auth = bootstrap_store.authenticateToSharedNotebook(share_key)
    note_store_url = getattr(auth, "noteStoreUrl", None) or linked_note_store_url
    if PRINT_ENDPOINTS:
        print(f"\nShared notebook auth flow:\n- bootstrap noteStoreUrl: {linked_note_store_url}\n- effective shared noteStoreUrl: {note_store_url}")
    return EvernoteStore(auth.authenticationToken, NoteStoreClient, note_store_url)

def get_latest_note_plain_text(note_store, note_guid: str) -> str:
    note = note_store.getNote(note_guid, True, False, False, False)
    return enml_to_text(getattr(note, "content", "") or "")

def download_mp3_attachments(note, download_dir: str) -> bool:
    """
    Find and download .mp3 resources from the note.
    Returns True if at least one MP3 was found and ensured (downloaded or exists),
    or if no MP3s were present at all.
    """
    if not note or not getattr(note, "resources", None):
        return True

    path = Path(download_dir)
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating download directory {download_dir}: {e}")
            return False

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
                # print(f"\nFile already exists, skipping: {filename}")
                continue
            
            print(f"\nDownloading MP3 attachment: {filename}...")
            if getattr(res, "data", None) and getattr(res.data, "body", None):
                try:
                    dest.write_bytes(res.data.body)
                    print(f"Saved to {dest}")
                except Exception as e:
                    print(f"Failed to save {filename}: {e}")
                    all_success = False
            else:
                all_success = False

    return all_success if has_mp3 else True

def today_title_prefix() -> str:
    return time.strftime("%y.%m%d", time.localtime())

def extract_title_date_prefix(title: str) -> str:
    m = re.match(r"^(\d{2}\.\d{4})", title or "")
    return m.group(1) if m else ""

def summarize_text(text: str) -> str:
    if not LLM_API_KEY or not text:
        return ""
    
    # Truncate extremely long text to avoid timeouts
    if len(text) > 30000:
        text = text[:30000] + "...(内容过长，已截断)"

    prompt_template_path = Path(__file__).parent.parent / "prompt.md"
    try:
        prompt_template = prompt_template_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        print(f"Warning: Failed to load prompt.md, using default. Error: {e}")
        prompt_template = "请为以下文章写一个200字左右的总结和摘要："
    
    max_retries = 3
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
            if "timeout" in str(e).lower() and attempt < max_retries - 1:
                print(f"LLM ({active_llm_key}) summarization timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                time.sleep(2)
                continue
            print(f"\nLLM ({active_llm_key}) summarization failed: {e}")
            break
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
        url = f"{url}{'&' if '?' in url else '?'}timestamp={ts}&sign={sign}"
    
    body = json.dumps({"msgtype": "text", "text": {"content": content}}, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with request.urlopen(req, timeout=20) as resp:
            if PRINT_DINGTALK_RESPONSE:
                print(f"\nDingTalk response:\n{resp.read().decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"\nDingTalk webhook send failed (ignored): {e}")

def main():
    ensure_utf8_console()

    if not DEV_TOKEN or not DEMO_NOTEBOOK.get("shareKey"):
        print("FATAL: DEV_TOKEN and DEMO_NOTEBOOK must be configured in config.json")
        sys.exit(1)

    client = EvernoteClient(token=DEV_TOKEN, service_host="app.yinxiang.com", sandbox=False)
    
    # Load cache for persistence
    cache_file = Path(__file__).parent / "demo_notebook_cache.json"
    cache_items, synced_dates = load_cache(cache_file)
    
    today_prefix = today_title_prefix()
    if SYNC_TODAY_ONLY and today_prefix in synced_dates:
        print(f"{today_prefix} already synced")
        return

    share_key = DEMO_NOTEBOOK["shareKey"]
    if share_key in cache_items:
        item = cache_items[share_key]
        # Always update store URL and name from config
        item.shareName = DEMO_NOTEBOOK.get("shareName", item.shareName)
        item.linkedNoteStoreUrl = DEMO_NOTEBOOK.get("noteStoreUrl", item.linkedNoteStoreUrl)
    else:
        item = SharedNotebookCacheItem(
            shareName=DEMO_NOTEBOOK.get("shareName", "Demo Notebook"),
            shareKey=share_key,
            linkedNoteStoreUrl=DEMO_NOTEBOOK["noteStoreUrl"],
            lastSentAt=now_ts() # Initialize for new
        )
        cache_items[share_key] = item

    if item.archivedNote:
        print(f"Skipping archived notebook: {item.shareName}")
        return

    notification_sent = False
    all_active_synced_today = True

    try:
        shared_store = get_shared_note_store(client, item.linkedNoteStoreUrl, item.shareKey)
        notes_md = fetch_latest_from_store(shared_store, "")
    except Exception as e:
        print(f"\nFailed to read shared notebook '{item.shareName}' ({item.shareKey}): {e}")
        return

    item.lastCheckedAt = now_ts()
    if not getattr(notes_md, "notes", None):
        print(f"\n{item.shareName} - no update")
        all_active_synced_today = False
        # Still need to save cache for lastCheckedAt
        save_cache(cache_file, cache_items, synced_dates)
        return

    # Pick the latest note that matches the criteria
    picked = None
    for n in notes_md.notes:
        t = getattr(n, "title", "") or ""
        
        # 1. Skip index notes
        if SKIP_TITLE_CONTAINS and SKIP_TITLE_CONTAINS in t:
            continue
        
        # 2. Extract and check date prefix
        date_prefix = extract_title_date_prefix(t)
        if not date_prefix:
            continue # Only process notes with yy.mmdd format
        
        # 3. If SYNC_TODAY_ONLY is True, check if it matches today
        if SYNC_TODAY_ONLY and date_prefix != today_prefix:
            continue
        
        # Found a candidate!
        picked = n
        break

    if picked is None:
        print(f"\n{item.shareName} - no update (today's note not found)")
        all_active_synced_today = False
        save_cache(cache_file, cache_items, synced_dates)
        return

    latest_title = getattr(picked, "title", "") or ""
    latest_guid = getattr(picked, "guid", "") or ""

    # Check if we should skip resource check/download
    if not item.mp3Downloaded or item.lastSentTitle != latest_title:
        # Fetch note with content and resources to check for MP3s
        # (We do this if mp3 is not downloaded OR if title is new)
        note = shared_store.getNote(latest_guid, True, True, False, False) if latest_guid else None
        
        # Download MP3 attachments (logic inside checks if file already exists locally)
        if note:
            # If we have a new title, reset mp3Downloaded and re-check
            if item.lastSentTitle != latest_title:
                item.mp3Downloaded = False
            
            download_success = download_mp3_attachments(note, DOWNLOAD_DIR)
            item.mp3Downloaded = download_success
    else:
        # Already downloaded and title matches, skip note fetch
        note = None

    # Skip processing if we have already sent/processed this note title
    if item.lastSentTitle == latest_title:
        # Update cache even if content is same
        item.latestTitle = latest_title
        item.latestNoteGuid = latest_guid
        save_cache(cache_file, cache_items, synced_dates)
        print(f"- {item.shareName} - {latest_title} - no update (mp3 checked)")
        return

    if SYNC_TODAY_ONLY:
        # Send notification to a separate webhook if it's a new today's note (keyword-only)
        if not notification_sent:
            print(f"New today's note detected: {latest_title}. Sending update notification...")
            post_dingtalk_text(DINGTALK_WEBHOOK_NOTIFICATION, "note updated", secret="")
            notification_sent = True

    plain = enml_to_text(getattr(note, "content", "") or "") if note else ""
    parts = plain.split("用户留言", 1)
    main_content = parts[0].strip()
    
    summary = ""
    if main_content:
        print(f"\nSummarizing: {latest_title}...")
        summary = summarize_text(main_content)

    if summary:
        clean_share_name = item.shareName.replace("《", "").replace("》", "").split("￥")[0].strip()
        dingtalk_msg = f"{latest_title} - {clean_share_name}\n\n{summary}"
        post_dingtalk_text(DINGTALK_WEBHOOK, dingtalk_msg)

    if PRINT_NOTE_TEXT_TO_CONSOLE:
        print(f"\n=== {item.shareName} ===\nTitle: {latest_title}")
        if summary:
            print(f"Summary: {summary}")
        print(plain)

    # Save output files locally
    lines = [f"=== {item.shareName} ===", f"Title: {latest_title}"]
    if summary:
        lines.append(f"Summary: {summary}\n")
    lines.extend([plain, ""])
    
    out_file = Path(__file__).with_name(NOTE_DAILY_FULL)
    out_file.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    main_content_file = Path(__file__).with_name(NOTE_DAILY_MAIN)
    main_content_file.write_text(main_content.strip() + "\n", encoding="utf-8")
    
    # Update cache
    item.lastSentTitle = latest_title
    item.latestTitle = latest_title
    item.latestNoteGuid = latest_guid
    item.lastSentAt = now_ts()

    # Update archivedNote status
    thirty_days_sec = 30 * 24 * 3600
    current_time = now_ts()
    if not item.archivedNote and item.lastSentAt > 0 and (current_time - item.lastSentAt) > thirty_days_sec:
        item.archivedNote = True
        print(f"Archiving inactive notebook: {item.shareName}")

    # Mark today as synced if SYNC_TODAY_ONLY is on and all active were synced
    if SYNC_TODAY_ONLY and all_active_synced_today:
        if today_prefix not in synced_dates:
            synced_dates.append(today_prefix)
            print(f"Marked {today_prefix} as synced")

    save_cache(cache_file, cache_items, synced_dates)
    
    print(f"{item.shareName} - {latest_title} - updated")


if __name__ == "__main__":
    main()
