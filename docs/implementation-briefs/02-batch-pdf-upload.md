# Brief 02: Batch PDF Upload

## Priority: WAVE 1 | Parallel-Safe | No Dependencies

## Context

Project Sentinel currently processes one PDF at a time. At quarter-end, treasury teams receive 10-20 capital call notices simultaneously. They need to upload all at once and see a summary of pass/fail results.

## What to Build

A batch processing mode on the "Process Capital Call" page that:
1. Accepts multiple PDF uploads simultaneously
2. Extracts and validates each one
3. Shows a summary table with pass/fail status per file
4. Allows selective approval of passing calls

## Implementation

### 1. Modify the upload section in `app.py`

Replace the single file uploader with a multi-file option:
```python
uploaded_files = st.file_uploader(
    "Upload PDF Notices",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)
```

### 2. Batch processing logic

When multiple files are uploaded:
```python
if uploaded_files and len(uploaded_files) > 1:
    st.markdown("### Batch Processing Results")
    results = []
    progress = st.progress(0)
    for i, file in enumerate(uploaded_files):
        extracted = extract_smart(file_bytes=file.read(), filename=file.name)
        validation = run_full_validation(extracted, ct, wires)
        results.append({"filename": file.name, "validation": validation, "extracted": extracted})
        progress.progress((i + 1) / len(uploaded_files))
    
    # Summary table
    summary_df = pd.DataFrame([{
        "File": r["filename"],
        "Fund": r["validation"]["fund_name_matched"] or r["validation"]["fund_name_extracted"],
        "Amount": f"EUR {r['validation']['amount']:,.0f}",
        "Commitment": "PASS" if r["validation"]["commitment_check"]["passed"] else "FAIL",
        "Wire": "PASS" if r["validation"]["wire_check"]["passed"] else "FAIL",
        "Status": r["validation"]["overall_status"],
    } for r in results])
    
    # Color-code the status column
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # Show counts
    approved = [r for r in results if r["validation"]["overall_status"] == "APPROVED"]
    rejected = [r for r in results if r["validation"]["overall_status"] != "APPROVED"]
    st.metric("Ready to Approve", len(approved))
    st.metric("Rejected", len(rejected))
    
    # Bulk approve button (with reviewer selection, same as single-file flow)
```

### 3. Single file fallback

When only one file is uploaded, use the existing single-file processing flow unchanged.

### 4. Bulk approval

For approved calls, show a "Approve All Passing Calls" button that:
- Requires reviewer selection (same 4-eye check)
- Processes each approved call through `db.execute_capital_call()`
- Shows a final summary of what was executed

## Acceptance Criteria

- [ ] Multiple PDFs can be uploaded at once
- [ ] Progress bar shows during processing
- [ ] Summary table shows pass/fail for each file
- [ ] Individual files can be expanded to see full validation details
- [ ] Bulk approve processes all passing calls with reviewer selection
- [ ] Already-processed files are skipped (using `db.is_file_already_processed()`)
- [ ] Single-file upload still works exactly as before
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `app.py` (Process Capital Call page)

## Do NOT

- Change the database schema
- Modify `database.py`, `validation_engine.py`, or `pdf_extractor.py`
- Remove the single-file processing flow
