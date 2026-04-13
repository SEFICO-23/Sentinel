# Brief 11: Multi-Language PDF Support

## Priority: WAVE 3 | Parallel-Safe | Depends on Wave 2 merge

## Context

Real-world GP notices come in German, French, Italian, and other languages. The regex extractor only handles English field labels ("Amount:", "Due Date:", etc.). The LLM extractor handles this naturally, but we need regex patterns for the non-LLM path too.

## What to Build

1. **Multi-language regex patterns** for common field labels
2. **Language detection** hint in extraction results
3. **LLM prompt update** to explicitly handle multi-language notices

## Implementation

### 1. Expand regex patterns in `pdf_extractor.py`

```python
def _extract_amount(text: str) -> float:
    patterns = [
        r"Amount:\s*(?:EUR|USD|GBP|CHF)?\s*([\d,]+(?:\.\d+)?)",      # English
        r"Betrag:\s*(?:EUR|USD|GBP|CHF)?\s*([\d.,]+)",                # German
        r"Montant:\s*(?:EUR|USD|GBP|CHF)?\s*([\d.,]+)",               # French
        r"Importo:\s*(?:EUR|USD|GBP|CHF)?\s*([\d.,]+)",               # Italian
        r"Importe:\s*(?:EUR|USD|GBP|CHF)?\s*([\d.,]+)",               # Spanish
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Handle European number format (1.000.000,00 vs 1,000,000.00)
            num_str = match.group(1)
            if "," in num_str and "." in num_str:
                if num_str.rindex(",") > num_str.rindex("."):
                    num_str = num_str.replace(".", "").replace(",", ".")  # European
                else:
                    num_str = num_str.replace(",", "")  # US/UK
            else:
                num_str = num_str.replace(",", "")
            return float(num_str)
    return 0.0
```

Apply the same multi-language pattern approach to:
- `_extract_investor()`: "To:" / "An:" / "A:" / "Destinataire:"
- `_extract_due_date()`: "Due Date:" / "Fälligkeitsdatum:" / "Date d'échéance:" / "Scadenza:"
- `_extract_bank()`: "Bank:" / "Bankverbindung:" / "Banque:" / "Banca:"
- `_extract_iban()`: "IBAN:" (universal)

### 2. European number format handling

Key difference: EUR 1.000.000,00 (European) vs EUR 1,000,000.00 (US/UK). The parser must detect which format is used.

### 3. Update LLM prompt in `llm_extractor.py`

Add to the prompt:
```
The document may be in any language (English, German, French, Italian, Spanish, etc.).
Extract the data regardless of language. Always return field values in English.
For amounts, always return as a plain number (no thousands separators).
```

### 4. Language hint

Add a `language` field to the extraction result:
```python
def _detect_language(text: str) -> str:
    if re.search(r"Betrag|Fälligkeitsdatum|Bankverbindung", text, re.IGNORECASE):
        return "de"
    if re.search(r"Montant|Date d.échéance|Banque", text, re.IGNORECASE):
        return "fr"
    if re.search(r"Importo|Scadenza|Banca", text, re.IGNORECASE):
        return "it"
    return "en"
```

## Acceptance Criteria

- [ ] German capital call notices extract correctly
- [ ] French capital call notices extract correctly
- [ ] European number format (1.000.000,00) handled correctly
- [ ] Language hint shown in extraction results
- [ ] LLM prompt updated for multi-language support
- [ ] Existing English PDFs still work perfectly
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `pdf_extractor.py` (multi-language regex patterns)
- `llm_extractor.py` (prompt update)

## Do NOT

- Add translation libraries or heavy NLP dependencies
- Change the database schema
- Modify app.py
