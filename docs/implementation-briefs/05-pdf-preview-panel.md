# Brief 05: PDF Preview Panel

## Priority: WAVE 1 | Parallel-Safe | No Dependencies

## Context

When reviewing a capital call notice, the reviewer needs to visually verify the extracted data against the original PDF. Currently they must open the PDF separately. A side-by-side view improves the 4-eye review workflow.

## What to Build

On the "Process Capital Call" page, after upload and extraction, show the original PDF alongside the extracted data in a two-column layout.

## Implementation

### 1. Display PDF in Streamlit

Streamlit doesn't have a native PDF viewer, but we can embed it using an iframe with base64-encoded data:

```python
import base64

def display_pdf(file_bytes: bytes):
    """Render a PDF in the browser using an iframe."""
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    pdf_display = f'''
    <iframe src="data:application/pdf;base64,{b64}" 
            width="100%" height="600" 
            style="border: 1px solid var(--border); border-radius: 8px;">
    </iframe>
    '''
    st.markdown(pdf_display, unsafe_allow_html=True)
```

### 2. Side-by-side layout

After the file is uploaded and extracted, use a two-column layout:
```python
if uploaded:
    # Store bytes before read() consumes them
    file_bytes = uploaded.read()
    uploaded.seek(0)  # Reset for potential re-read
    
    col_pdf, col_data = st.columns([1, 1])
    
    with col_pdf:
        st.markdown('<div class="section-header">Original Notice</div>', unsafe_allow_html=True)
        display_pdf(file_bytes)
    
    with col_data:
        st.markdown('<div class="section-header">Extracted Data</div>', unsafe_allow_html=True)
        # ... existing extraction display code ...
```

### 3. Handle the file bytes

Important: `uploaded.read()` can only be called once. The current code calls it in the extraction step. You need to:
1. Read the bytes once at the top: `file_bytes = uploaded.read()`
2. Pass `file_bytes` to the extractor
3. Pass `file_bytes` to the PDF viewer

### 4. Collapsible PDF viewer

Wrap the PDF preview in an expander so it doesn't dominate the page:
```python
with st.expander("View Original PDF", expanded=True):
    display_pdf(file_bytes)
```

### 5. Theme support

The iframe border should use `var(--border)` from the CSS custom properties. In dark mode, the PDF itself will still render with its original white background (this is expected -- PDFs don't have dark mode).

## Acceptance Criteria

- [ ] PDF is displayed inline after upload (no separate window needed)
- [ ] Reviewer can see the PDF and extracted data simultaneously
- [ ] PDF viewer has a reasonable height (500-600px) with scroll for longer documents
- [ ] Collapsible via expander to save screen space
- [ ] Does not break the existing extraction/validation flow
- [ ] Works in both light and dark mode
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `app.py` (Process Capital Call page)

## Do NOT

- Add new pip dependencies
- Change the database schema
- Modify any other files
- Convert the PDF to images (unnecessary complexity)
