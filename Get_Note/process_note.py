import json
import re
import sys
from pathlib import Path
from urllib import request, error

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
                "summary": summary
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
    
    print(f"Fetching tenant_access_token for APP_ID: {app_id}")
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
                "标题": note["note_title"],
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
    else:
        print("No new notes parsed.")

if __name__ == "__main__":
    main()
