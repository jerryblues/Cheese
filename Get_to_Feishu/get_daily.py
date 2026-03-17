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
    config_path = Path(__file__).with_name("config.json")
    if not config_path.exists():
        print("FATAL: config.json not found.")
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

# Output files
NOTEBOOK_LIST = "notebook_list.json"
NOTE_DAILY_FULL = "note_daily_full.txt"
NOTE_DAILY_MAIN = "note_daily_main.txt"

# Debug/Output switches
PRINT_ENDPOINTS = False
PRINT_NOTE_TEXT_TO_CONSOLE = False
PRINT_DINGTALK_RESPONSE = False

# Filter rules
SKIP_TITLE_CONTAINS = "【"
MAX_NOTES_TO_SCAN_PER_NOTEBOOK = 5
# True: sync today's note; False: sync the latest available note
SYNC_TODAY_ONLY = True

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

def download_mp3_attachments(note, download_dir: str):
    """
    Find and download .mp3 resources from the note.
    """
    if not note or not getattr(note, "resources", None):
        return

    path = Path(download_dir)
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating download directory {download_dir}: {e}")
            return

    for res in note.resources:
        mime = getattr(res, "mime", "")
        filename = ""
        if getattr(res, "attributes", None):
            filename = getattr(res.attributes, "fileName", "")
        
        # Check if it's an MP3 by mime type or extension
        is_mp3 = "audio/mpeg" in mime or (filename and filename.lower().endswith(".mp3"))
        
        if is_mp3:
            if not filename:
                filename = f"attachment_{res.guid[:8]}.mp3"
            
            # Skip files with "[1.5倍速]" in the name
            if "[1.5倍速]" in filename:
                print(f"Skipping 1.5x speed file: {filename}")
                continue
            
            dest = path / filename
            if dest.exists():
                print(f"\nFile already exists, skipping: {filename}")
                continue
            
            print(f"\nDownloading MP3 attachment: {filename}...")
            if getattr(res, "data", None) and getattr(res.data, "body", None):
                try:
                    dest.write_bytes(res.data.body)
                    print(f"Saved to {dest}")
                except Exception as e:
                    print(f"Failed to save {filename}: {e}")


def today_title_prefix() -> str:
    # Example: "25.1210" for 2025-12-10
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

    prompt_template_path = Path(__file__).with_name("prompt.md")
    try:
        prompt_template = prompt_template_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        print(f"Warning: Failed to load prompt.md, using default prompt. Error: {e}")
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

    cache_file = Path(__file__).with_name(NOTEBOOK_LIST)
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
            fresh_item.lastSentTitle = old.lastSentTitle # key check
        cache_items[share_key] = fresh_item
    save_cache(cache_file, cache_items)

    if not cache_items:
        print("No shared (linked) notebooks found.")
        return

    outputs: list[str] = []
    main_contents: list[str] = []
    today_prefix = today_title_prefix()
    notification_sent = False

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
            print(f"\n{item.shareName} - no update")
            continue

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
            print(f"\n{item.shareName} - no update")
            continue

        latest_title = getattr(picked, "title", "") or ""
        latest_guid = getattr(picked, "guid", "") or ""

        # Fetch note with content and resources to check for MP3s
        # (We do this regardless of title cache to ensure MP3s are checked)
        note = shared_store.getNote(latest_guid, True, True, False, False) if latest_guid else None
        
        # Download MP3 attachments (logic inside checks if file already exists locally)
        if note:
            download_mp3_attachments(note, DOWNLOAD_DIR)

        # Skip LLM summary and notification if we have already processed this note title
        if item.lastSentTitle == latest_title:
            # Update cache timestamps even if content is same
            item.latestTitle = latest_title
            item.latestNoteGuid = latest_guid
            item.lastCheckedAt = now_ts()
            print(f"{item.shareName} - {latest_title} - no update (mp3 checked)")
            continue

        previous_title = item.latestTitle
        item.latestTitle = latest_title
        item.latestNoteGuid = latest_guid

        # Send notification to a separate webhook if it's a new today's note (keyword-only)
        if SYNC_TODAY_ONLY:
            if not notification_sent:
                print(f"New note detected: {latest_title}. Sending update notification...")
                post_dingtalk_text(DINGTALK_WEBHOOK_NOTIFICATION, "note updated", secret="")
                notification_sent = True

        plain = enml_to_text(getattr(note, "content", "") or "") if note else ""
        
        # 以“用户留言”为界，分割文章主体和留言部分
        parts = plain.split("用户留言", 1)
        main_content = parts[0].strip()
        user_comments = parts[1].strip() if len(parts) > 1 else ""

        summary = ""
        if main_content:
            print(f"\nSummarizing: {latest_title}...")
            summary = summarize_text(main_content) # 只总结主体内容

        # --- 钉钉消息格式 ---
        if summary:
            # 清理课程名称：去掉书名号，去掉￥符号及其后面的内容
            clean_share_name = item.shareName.replace("《", "").replace("》", "")
            if "￥" in clean_share_name:
                clean_share_name = clean_share_name.split("￥")[0].strip()
            
            dingtalk_msg = f"{latest_title} - {clean_share_name}\n\n{summary}"
            post_dingtalk_text(DINGTALK_WEBHOOK, dingtalk_msg)

        # --- 文件保存逻辑 ---
        # 1. 收集主体内容，用于写入 main_content.txt
        main_contents.append(main_content)

        # 2. 保持原有逻辑，将完整内容（包括摘要和留言）写入 aatest_shared_notes.txt
        if PRINT_NOTE_TEXT_TO_CONSOLE:
            print(f"\n=== {item.shareName} ===")
            print(f"Title: {latest_title}")
            if summary:
                print(f"Summary: {summary}")
            print(plain)

        # Still keep the full content for the local text file (optional)
        lines = [
            f"=== {item.shareName} ===",
            f"Title: {latest_title}",
        ]
        if summary:
            lines.append(f"Summary: {summary}\n")
        lines.extend([plain, ""])
        block = "\n".join(lines)
        outputs.append(block)

        # Update lastSentTitle only if we actually kept/saved this note today.
        item.lastSentTitle = latest_title
        item.lastSentAt = now_ts()
        
        print(f"{item.shareName} - {latest_title} - updated")


    if outputs:
        out_file = Path(__file__).with_name(NOTE_DAILY_FULL)
        out_file.write_text("\n".join(outputs).strip() + "\n", encoding="utf-8")

    if main_contents:
        main_content_file = Path(__file__).with_name(NOTE_DAILY_MAIN)
        main_content_file.write_text("\n\n---\n\n".join(main_contents).strip() + "\n", encoding="utf-8")

    save_cache(cache_file, cache_items)


if __name__ == "__main__":
    main()
