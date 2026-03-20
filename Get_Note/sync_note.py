import json
import re
import sys
import time
import inspect
from pathlib import Path
from urllib import request, error
from collections import namedtuple

# Compatibility shim for Python 3.11+ where inspect.getargspec is removed.
# The Evernote SDK still calls inspect.getargspec in some versions.
if not hasattr(inspect, "getargspec"):
    ArgSpec = namedtuple("ArgSpec", ["args", "varargs", "keywords", "defaults"])
    inspect.getargspec = inspect.getfullargspec

# Add current directory to path for Evernote SDK
sys.path.insert(0, str(Path(__file__).parent))

# Import Evernote SDK components
try:
    from evernote.api.client import EvernoteClient
    from evernote.api.client import Store as EvernoteStore
    from evernote.edam.notestore.NoteStore import Client as NoteStoreClient
    from evernote.edam.notestore import NoteStore
    from evernote.edam.type import ttypes as Types
    from evernote.edam.error import ttypes as Errors
except ImportError:
    print("Evernote SDK not found. Please install it.")
    # Don't exit, just skip Evernote sync
    pass

def parse_notes(file_path: Path):
    if not file_path.exists():
        print(f"Error: {file_path} not found.")
        return []

    content = file_path.read_text(encoding="utf-8")
    
    # Split by notebook separator: === Notebook Name ===
    sections = re.split(r'===\s*(.*?)\s*===', content)
    
    results = []
    
    # sections[0] is everything before the first '==='
    for i in range(1, len(sections), 2):
        notebook_full_name = sections[i].strip()
        notebook_content = sections[i+1].strip() if i+1 < len(sections) else ""
        
        if not notebook_content:
            continue

        # 1. Extract notebook name (keep only content inside 《 》)
        notebook_display_name = notebook_full_name
        book_match = re.search(r'《(.*?)》', notebook_full_name)
        if book_match:
            notebook_display_name = book_match.group(1)

        # 2. Extract Author from notebook name
        author = ""
        author_match = re.search(r'\d+-(.*?)·', notebook_full_name)
        if author_match:
            author = author_match.group(1)
        else:
            author = notebook_full_name.split('·')[0].split('-')[-1]

        # Split by "Title:" to handle multiple notes
        notes_raw = re.split(r'(?=Title:)', notebook_content)
        
        for note_raw in notes_raw:
            if not note_raw.strip():
                continue
                
            # 3. Note Title (remove date and number prefixes, keep rest)
            full_title = ""
            title_match = re.search(r'Title:\s*(.*)', note_raw)
            if title_match:
                full_title = title_match.group(1).strip()
            
            # 4. Link
            link = ""
            link_match = re.search(r'Link:\s*(.*)', note_raw)
            if link_match:
                link = link_match.group(1).strip()
            
            note_display_title = full_title
            if full_title:
                # First remove date prefix (e.g., "26.0318丨") and number prefix (e.g., "085丨")
                # Match pattern: YY.MMDD丨 followed by optional number丨
                cleaned_title = re.sub(r'^\d{2}\.\d{4}丨(\d+丨)?', '', full_title)
                cleaned_title = cleaned_title.strip()
                
                # Remove trailing quotes if present
                cleaned_title = cleaned_title.rstrip('"')
                
                # Apply the rule: find the first Chinese character from the beginning
                # Then check what's before it
                chinese_char_pattern = re.compile(r'[\u4e00-\u9fa5]')
                match = chinese_char_pattern.search(cleaned_title)
                
                if match:
                    start_pos = match.start()
                    # Check what's before the first Chinese character
                    if start_pos > 0:
                        prev_char = cleaned_title[start_pos - 1]
                        # If previous character is a space, start from the Chinese character
                        if prev_char.isspace():
                            start_pos = start_pos
                        # If previous character is a punctuation that should be included
                        elif prev_char in ['《', '"', '“', "'", "‘"]:
                            start_pos = start_pos - 1
                    
                    # Extract from start_pos to end
                    note_display_title = cleaned_title[start_pos:]
            
            # 4. Update Time (from Title)
            update_time = ""
            time_match = re.search(r'(\d{2}\.\d{4})', full_title)
            if time_match:
                update_time = time_match.group(1)
            
            # 5. Summary & Body logic
            summary = ""
            note_content = ""
            
            if "Summary:" in note_raw:
                # Find content between Summary: and the repeated title (where body starts)
                parts = note_raw.split("Summary:")
                if len(parts) > 1:
                    after_summary_label = parts[1]
                    # Use the last part of full_title for better matching
                    search_marker = note_display_title
                    
                    if search_marker in after_summary_label:
                        summary_and_rest = after_summary_label.split(search_marker, 1)
                        summary = summary_and_rest[0].strip()
                        body_and_comments = search_marker + summary_and_rest[1]
                        
                        # Split body and comments
                        if "用户留言" in body_and_comments:
                            note_content = body_and_comments.split("用户留言")[0].strip()
                        else:
                            note_content = body_and_comments.strip()
                    else:
                        summary = after_summary_label.split("\n\n")[0].strip()
                        note_content = after_summary_label.strip()
            else:
                # No Summary: found, process the entire note content
                # Remove Title line first
                lines = note_raw.split('\n')
                content_lines = []
                for line in lines:
                    if not line.strip().startswith('Title:'):
                        content_lines.append(line)
                
                # Join back and process
                content = '\n'.join(content_lines).strip()
                if content:
                    # Split body and comments
                    if "用户留言" in content:
                        note_content = content.split("用户留言")[0].strip()
                    else:
                        note_content = content

            # 6. User Comments
            user_comments = ""
            comments_match = re.search(r'用户留言\s*(.*)', note_raw, re.DOTALL)
            if comments_match:
                user_comments = comments_match.group(1).strip()

            results.append({
                "update_time": update_time,
                "notebook_name": notebook_display_name,
                "author": author,
                "note_title": note_display_title,
                "note_content": note_content,
                "user_comments": user_comments,
                "summary": summary,
                "link": link
            })
            
    return results

def get_feishu_tenant_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    req_body = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
    req = request.Request(url, data=req_body, method="POST", headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == 0:
                return data.get("tenant_access_token")
            else:
                print(f"Failed to get Feishu token: {data.get('msg')} (code: {data.get('code')})")
                return None
    except error.HTTPError as e:
        print(f"HTTP Error getting Feishu token: {e.code} {e.reason}")
        print(f"Response: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error getting Feishu token: {e}")
        return None

def sync_to_feishu(notes, config):
    if not notes:
        return
    
    fs_config = config.get("FEISHU_SYNC", {})
    if not fs_config.get("ENABLED", False):
        return

    print("Feishu sync is enabled. Starting sync...")
    
    app_id = fs_config.get("APP_ID")
    app_secret = fs_config.get("APP_SECRET")
    app_token = fs_config.get("APP_TOKEN")
    table_id = fs_config.get("TABLE_ID")
    
    # print(f"Fetching tenant_access_token for APP_ID: {app_id}")
    token = get_feishu_tenant_access_token(app_id, app_secret)
    if not token:
        print("Feishu sync aborted: Failed to get token.")
        return

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
    
    # Prepare records for Feishu Bitable
    records = []
    for note in notes:
        records.append({
            "fields": {
                    "时间": note["update_time"],
                    "课程": note["notebook_name"],
                    "作者": note["author"],
                    "标题": {"link": note["link"], "text": note["note_title"]},
                    "内容": note["note_content"],
                    "留言": note["user_comments"],
                    "AI总结": note["summary"]
                }
        })

    # Batch create (Feishu limits 500 records per batch)
    for i in range(0, len(records), 500):
        batch = records[i:i+500]
        req_body = json.dumps({"records": batch}).encode("utf-8")
        req = request.Request(url, data=req_body, method="POST", headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}"
        })
        try:
            with request.urlopen(req) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                if resp_data.get("code") == 0:
                    print(f"Successfully synced {len(batch)} records to Feishu.")
                else:
                    print(f"Feishu API error: {resp_data.get('msg')} (code: {resp_data.get('code')})")
        except error.HTTPError as e:
            print(f"HTTP Error syncing to Feishu: {e.code} {e.reason}")
            # Try to read the error message from Feishu
            try:
                err_msg = e.read().decode('utf-8')
                print(f"Feishu Error Response: {err_msg}")
            except:
                pass
        except Exception as e:
            print(f"Feishu sync request failed: {e}")

def today_title_prefix():
    """Generate today's title prefix."""
    return time.strftime("%y.%m%d", time.localtime())

def get_personal_note_store(client, service_host, dev_token):
    """Get personal note store from Evernote."""
    user_store = client.get_user_store()
    note_store_url = user_store.getNoteStoreUrl()
    return EvernoteStore(dev_token, NoteStoreClient, note_store_url)

def get_or_create_notebook(note_store, notebook_name):
    """Get or create a notebook with the given name."""
    try:
        notebooks = note_store.listNotebooks()
        for notebook in notebooks:
            if notebook.name == notebook_name:
                return notebook.guid
        
        # Create new notebook
        new_notebook = Types.Notebook()
        new_notebook.name = notebook_name
        created_notebook = note_store.createNotebook(new_notebook)
        print(f"Created notebook: {created_notebook.name}")
        return created_notebook.guid
    except Exception as e:
        print(f"Error getting/creating notebook: {e}")
        return None

def create_or_update_note(note_store, title, content, notebook_guid):
    """Create a new note or update existing note with the same title."""
    try:
        # Search for existing note with the same title
        filter = NoteStore.NoteFilter()
        filter.notebookGuid = notebook_guid
        spec = NoteStore.NotesMetadataResultSpec()
        spec.includeTitle = True
        
        notes_metadata = note_store.findNotesMetadata(filter, 0, 100, spec)
        
        existing_note_guid = None
        for note_meta in notes_metadata.notes:
            if note_meta.title == title:
                existing_note_guid = note_meta.guid
                break
        
        if existing_note_guid:
            # Update existing note - append content instead of replacing
            existing_note = note_store.getNote(existing_note_guid, True, False, False, False)
            
            # Extract existing content (remove XML wrapper)
            existing_content = existing_note.content
            # Find the content between <en-note> and </en-note>
            start_idx = existing_content.find('<en-note>')
            end_idx = existing_content.find('</en-note>')
            if start_idx != -1 and end_idx != -1:
                start_idx += len('<en-note>')
                existing_content = existing_content[start_idx:end_idx]
            
            # Append new content to existing content
            combined_content = existing_content + content
            
            # Update note with combined content
            existing_note.content = f'<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"><en-note>{combined_content}</en-note>'
            updated_note = note_store.updateNote(existing_note)
            print(f"Updated note (appended content): {updated_note.guid}")
            return updated_note
        else:
            # Create new note
            note = Types.Note()
            note.title = title
            note.content = f'<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"><en-note>{content}</en-note>'
            note.notebookGuid = notebook_guid
            created_note = note_store.createNote(note)
            print(f"Created note: {created_note.guid}")
            return created_note
    except Exception as e:
        print(f"Error creating/updating note: {e}")
        return None

def sync_to_evernote(notes, config):
    """Sync notes to Evernote."""
    if not notes:
        return
    
    # Check if Evernote SDK is available
    if not 'EvernoteClient' in globals():
        print("Evernote SDK not available. Skipping Evernote sync.")
        return
    
    # Check if DEV_TOKEN is configured
    dev_token = config.get("DEV_TOKEN", "")
    if not dev_token:
        print("DEV_TOKEN not found in config. Skipping Evernote sync.")
        return
    
    print("Evernote sync is enabled. Starting sync...")
    
    # Initialize Evernote client
    service_host = "app.yinxiang.com"
    client = EvernoteClient(token=dev_token, service_host=service_host, sandbox=False)
    personal_store = get_personal_note_store(client, service_host, dev_token)
    
    # Get or create "Holmes" notebook
    notebook_guid = get_or_create_notebook(personal_store, "Holmes")
    if not notebook_guid:
        print("Failed to get or create notebook. Skipping Evernote sync.")
        return
    
    # Get notebook names for full content sync from config (support list and fuzzy matching)
    full_content_notebooks = config.get("FULL_CONTENT_AUTHORS", ["万维钢"])
    
    # Ensure it's a list
    if not isinstance(full_content_notebooks, list):
        full_content_notebooks = [full_content_notebooks]

    # Separate notes into two groups
    summary_items = []
    full_content_items = []
    
    for note in notes:
        # Add all notes to summary_items (no author filtering)
        summary_items.append(note)
        
        # Check if author matches any keyword in full_content_notebooks for full content
        is_full_content = False
        for keyword in full_content_notebooks:
            if keyword in note.get('author', ''):
                is_full_content = True
                break
        
        if is_full_content:
            full_content_items.append(note)

    # Create or update note 1: All summaries
    if summary_items:
        note_title = f"{today_title_prefix()} Summary"
        
        content_parts = []
        for note in summary_items:
            # Create full title
            full_title = f"{note['update_time']}丨{note['note_title']}"
            content_parts.append(f"<div>{full_title}</div>")
            content_parts.append("<br/>")
            content_parts.append(f"<div>{note['summary'].replace('\n', '<br/>')}</div>")
            content_parts.append("<br/>")
            content_parts.append("<hr/>")
            content_parts.append("<br/>")
        
        note_content = "".join(content_parts)
        
        print(f"Creating/updating note: {note_title}")
        create_or_update_note(personal_store, note_title, note_content, notebook_guid)

    # Create or update note 2: Full content for specific notebook
    if full_content_items:
        note_title = f"{today_title_prefix()} All"
        
        content_parts = []
        for note in full_content_items:
            # Create full title
            full_title = f"{note['update_time']}丨{note['note_title']}"
            content_parts.append(f"<div>{full_title}</div>")
            content_parts.append("<br/>")
            content_parts.append(f"<div>{note['note_content'].replace('\n', '<br/>')}</div>")
            content_parts.append("<br/>")
            content_parts.append("<hr/>")
            content_parts.append("<br/>")
        
        note_content = "".join(content_parts)
        
        print(f"Creating/updating note: {note_title}")
        create_or_update_note(personal_store, note_title, note_content, notebook_guid)

    print("Evernote sync completed!")

def main():
    base_path = Path(__file__).parent
    input_file = base_path / "output" / "note_daily_full.txt"
    output_file = base_path / "output" / "note_processed.json"
    config_file = base_path / "config" / "config.json"
    
    # Load config
    config = {}
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")

    print(f"Processing {input_file}...")
    new_notes = parse_notes(input_file)
    
    if new_notes:
        # Load existing notes if file exists
        existing_notes = []
        if output_file.exists():
            try:
                existing_notes = json.loads(output_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Warning: Failed to load existing {output_file}: {e}")
        
        # Append new notes
        combined_notes = existing_notes + new_notes
        output_file.write_text(json.dumps(combined_notes, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Successfully appended {len(new_notes)} notes to {output_file} (Total: {len(combined_notes)})")
        
        # Sync new notes to Feishu if enabled
        sync_to_feishu(new_notes, config)
        
        # Sync new notes to Evernote
        sync_to_evernote(new_notes, config)
    else:
        print("No new notes parsed.")

if __name__ == "__main__":
    main()
