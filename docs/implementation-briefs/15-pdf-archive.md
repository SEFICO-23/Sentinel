# Brief 15: PDF Archive

## Priority: WAVE 3 | Parallel-Safe | Depends on Wave 2 merge

## Context

Uploaded PDFs are currently ephemeral -- once the page reruns, the file is gone. For audit and compliance purposes, the original PDF should be archived and retrievable from the audit log.

## What to Build

1. **PDF storage** on the filesystem (organized by date/fund)
2. **Link from audit log** to download the original PDF
3. **Archive browser** to search and download archived PDFs

## Implementation

### 1. Create archive directory structure

```
Project Sentinel/
└── archive/
    └── capital_calls/
        └── 2026/
            └── 03/
                ├── Notice_1_GT_IV_Equity.pdf
                ├── Notice_3_Parallax_Buyout_II.pdf
                └── ...
```

### 2. Archive function

```python
import os
import shutil
from datetime import datetime

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "archive", "capital_calls")

def archive_pdf(file_bytes: bytes, filename: str) -> str:
    """Save PDF to archive. Returns the archive path."""
    now = datetime.now()
    dir_path = os.path.join(ARCHIVE_DIR, str(now.year), f"{now.month:02d}")
    os.makedirs(dir_path, exist_ok=True)
    
    # Add timestamp to avoid collisions
    safe_name = f"{now.strftime('%Y%m%d_%H%M%S')}_{filename}"
    file_path = os.path.join(dir_path, safe_name)
    
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    
    return file_path
```

### 3. Store archive path in database

Add `archive_path` column to `processed_calls`:
```sql
ALTER TABLE processed_calls ADD COLUMN archive_path TEXT;
```

Or add it to the CREATE TABLE if running fresh. Update `execute_capital_call()`, `log_rejection()`, and `log_escalation()` to accept and store the archive path.

### 4. Archive on upload

In `app.py`, after successful extraction:
```python
archive_path = archive_pdf(file_bytes, uploaded.name)
# Pass archive_path to db.execute_capital_call() or db.log_rejection() etc.
```

### 5. Download from audit log

In the Audit Log page, within each entry's expander:
```python
if action.get("archive_path") and os.path.exists(action["archive_path"]):
    with open(action["archive_path"], "rb") as f:
        st.download_button(
            "Download Original PDF",
            data=f.read(),
            file_name=action.get("filename", "notice.pdf"),
            mime="application/pdf",
        )
```

### 6. Archive browser (optional page)

Add a simple page or section that lists all archived PDFs:
```python
# Walk the archive directory
# Show as a table with filename, date, fund, size
# Download button for each
```

## Acceptance Criteria

- [ ] PDFs saved to `archive/capital_calls/YYYY/MM/` on upload
- [ ] Archive path stored in `processed_calls` table
- [ ] Original PDF downloadable from audit log
- [ ] Filenames include timestamp to prevent collisions
- [ ] Archive directory created automatically
- [ ] Works for all three actions: EXECUTED, REJECTED, ESCALATED
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `database.py` (add archive_path column, update mutation functions)
- `app.py` (archive on upload, download from audit log)

## Do NOT

- Store PDFs as BLOBs in SQLite (filesystem is more efficient)
- Delete source PDFs from the original directory
- Add compression (PDFs are already compressed)
