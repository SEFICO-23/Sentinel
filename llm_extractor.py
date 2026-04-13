"""
LLM-powered PDF extraction for Project Sentinel.
Uses Claude API when available, falls back to regex-based extraction.
Handles unstructured, multi-format, and noisy capital call notices.
"""
import os
import json
import re
from pdf_extractor import extract_capital_call, extract_from_bytes as regex_extract_from_bytes

# Claude API availability
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


EXTRACTION_PROMPT = """You are a financial document parser specialized in Private Equity capital call notices.

Extract the following fields from this capital call notice text. Return ONLY a valid JSON object with these exact keys:

{
  "fund_name": "The name of the fund issuing the capital call",
  "investor": "The entity the call is addressed to (after 'To:')",
  "amount": 0.00,
  "currency": "EUR",
  "due_date": "DD.MM.YYYY",
  "bank": "Beneficiary bank name",
  "iban": "Full IBAN or account number as written"
}

Rules:
- The document may be in any language (English, German, French, Italian, Spanish, etc.).
  Extract the data regardless of language. Always return field values in English.
- For amounts, always return as a plain number (no thousands separators).
- amount must be a number (no commas, no currency symbol)
- If a field is not found, use null
- For fund_name, use the full official name (e.g., "GT Partners VI Equity" not "GT 6")
- Preserve the IBAN exactly as written including spaces
- due_date must be in DD.MM.YYYY format

Document text:
---
{text}
---

JSON:"""


def extract_with_llm(text: str, api_key: str = None) -> dict | None:
    """Extract capital call data using Claude API."""
    if not ANTHROPIC_AVAILABLE:
        return None

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None

    try:
        client = Anthropic(api_key=key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(text=text)
            }]
        )

        raw = response.content[0].text.strip()
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "fund_name": data.get("fund_name", ""),
                "investor": data.get("investor", ""),
                "amount": float(data.get("amount", 0) or 0),
                "currency": data.get("currency", "EUR") or "EUR",
                "due_date": data.get("due_date", ""),
                "bank": data.get("bank", ""),
                "iban": data.get("iban", ""),
                "raw_text": text,
                "extraction_method": "llm",
            }
    except Exception:
        return None
    return None


def extract_smart(pdf_path: str = None, file_bytes: bytes = None,
                  filename: str = "", api_key: str = None) -> dict:
    """Smart extraction: try regex first, use LLM if data is incomplete.

    Returns the extracted data dict with an 'extraction_method' field
    indicating which method was used ('regex', 'llm', or 'regex+llm').
    """
    # Step 1: Regex extraction
    if file_bytes:
        regex_result = regex_extract_from_bytes(file_bytes, filename)
    elif pdf_path:
        regex_result = extract_capital_call(pdf_path)
    else:
        raise ValueError("Either pdf_path or file_bytes must be provided")

    regex_result["extraction_method"] = "regex"

    # Step 2: Check completeness
    required_fields = ["fund_name", "amount", "due_date", "iban"]
    missing = [f for f in required_fields if not regex_result.get(f)]
    amount_missing = regex_result.get("amount", 0) <= 0

    if not missing and not amount_missing:
        # Regex got everything -- confidence is high
        regex_result["extraction_confidence"] = "high"
        return regex_result

    # Step 3: Try LLM if regex is incomplete
    text = regex_result.get("raw_text", "")
    llm_result = extract_with_llm(text, api_key) if text else None

    if llm_result is None:
        # LLM not available or failed -- return regex result with warning
        regex_result["extraction_confidence"] = "low" if (missing or amount_missing) else "high"
        regex_result["missing_fields"] = missing
        return regex_result

    # Step 4: Merge -- LLM fills gaps, regex takes priority for fields it found
    merged = {**regex_result}
    for field in required_fields + ["investor", "bank", "currency"]:
        if not merged.get(field) or (field == "amount" and merged.get("amount", 0) <= 0):
            if llm_result.get(field):
                merged[field] = llm_result[field]

    merged["extraction_method"] = "regex+llm"
    merged["extraction_confidence"] = "high" if not any(
        not merged.get(f) for f in required_fields
    ) else "medium"
    return merged


def check_api_available(api_key: str = None) -> bool:
    """Check if Claude API is configured and reachable."""
    if not ANTHROPIC_AVAILABLE:
        return False
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    return bool(key)


if __name__ == "__main__":
    import sys
    for path in sys.argv[1:]:
        result = extract_smart(pdf_path=path)
        display = {k: v for k, v in result.items() if k != "raw_text"}
        print(f"\n{path}:")
        print(json.dumps(display, indent=2, default=str))
