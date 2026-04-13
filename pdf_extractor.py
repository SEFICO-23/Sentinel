"""
PDF Capital Call Notice extractor.
Uses regex-based extraction (no LLM API key required) with fallback patterns
to handle different PDF formats (Capital Call, Drawdown, etc.).
"""
import re
import pdfplumber


def extract_capital_call(pdf_path: str) -> dict:
    """Extract structured data from a capital call PDF notice."""
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    result = {
        "raw_text": text,
        "fund_name": _extract_fund_name(text),
        "investor": _extract_investor(text),
        "amount": _extract_amount(text),
        "currency": _extract_currency(text),
        "due_date": _extract_due_date(text),
        "bank": _extract_bank(text),
        "swift": _extract_swift(text),
        "iban": _extract_iban(text),
        "language": _detect_language(text),
    }
    return result


def _extract_fund_name(text: str) -> str:
    """Extract fund name from the PDF text.

    Strategy: First look for a line containing a known call-type keyword
    (Capital Call, Drawdown, Kapitalabruf, Appel de Capitaux, etc.) and
    extract the fund name portion. Falls back to the first non-trivial line.
    """
    # Multi-language call-type suffixes to strip
    call_types = r"(Capital Call|Drawdown|Draw\s?down|Notice|Kapitalabruf|Appel de Capitaux|Richiesta di Capitale)"
    # Lines to skip (headers, confidentiality notices, page markers)
    skip_patterns = re.compile(r"^(CONFIDENTIAL|STRICTLY|Page \d|Date[:\s]|Document Ref|CAPITAL CALL NOTICE$|DRAWDOWN NOTICE$)", re.IGNORECASE)

    # Pass 1: Find a line with a call-type keyword
    for line in text.split("\n"):
        line = line.strip()
        if not line or skip_patterns.match(line):
            continue
        if re.search(call_types, line, re.IGNORECASE):
            name = re.split(r"\s*[-–]\s*" + call_types, line, flags=re.IGNORECASE)[0].strip()
            if name and not skip_patterns.match(name):
                return name

    # Pass 2: Fallback to first non-trivial line (>5 chars, not a skip pattern)
    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 5 or skip_patterns.match(line):
            continue
        name = re.split(r"\s*[-–]\s*" + call_types, line, flags=re.IGNORECASE)[0].strip()
        if name:
            return name
    return ""


def _extract_investor(text: str) -> str:
    patterns = [
        r"To:\s*(.+)",                  # English
        r"An:\s*(.+)",                  # German
        r"Destinataire:\s*(.+)",        # French
        r"A:\s*(.+)",                   # Italian / Spanish
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


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


def _extract_currency(text: str) -> str:
    patterns = [
        r"Amount:\s*(EUR|USD|GBP|CHF)",
        r"Betrag:\s*(EUR|USD|GBP|CHF)",
        r"Montant:\s*(EUR|USD|GBP|CHF)",
        r"Importo:\s*(EUR|USD|GBP|CHF)",
        r"Importe:\s*(EUR|USD|GBP|CHF)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return "EUR"


def _extract_due_date(text: str) -> str:
    patterns = [
        r"Due\s*Date:\s*([\d./-]+)",                    # English
        r"F(?:ä|ae|a)lligkeitsdatum:\s*([\d./-]+)",      # German (ä, ae, a variants)
        r"Date\s+d['\u2019](?:[eé]ch[eé]ance):\s*([\d./-]+)",  # French
        r"Scadenza:\s*([\d./-]+)",                       # Italian
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _extract_bank(text: str) -> str:
    patterns = [
        r"Bank:\s*(.+)",               # English
        r"Bankverbindung:\s*(.+)",     # German
        r"Banque:\s*(.+)",             # French
        r"Banca:\s*(.+)",              # Italian
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def _extract_swift(text: str) -> str:
    match = re.search(r"(?:SWIFT|BIC|Swift/BIC)[\s:]+([A-Z]{6}[A-Z0-9]{2,5})", text, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _extract_iban(text: str) -> str:
    match = re.search(r"IBAN:\s*(.+)", text)
    if match:
        return match.group(1).strip()
    # Fallback: look for IBAN-like pattern
    match = re.search(r"([A-Z]{2}\d{2}\s[\w\s]{10,})", text)
    return match.group(1).strip() if match else ""


def _detect_language(text: str) -> str:
    """Detect document language based on known capital call field labels."""
    if re.search(r"Betrag|F[äa]lligkeitsdatum|Bankverbindung", text, re.IGNORECASE):
        return "de"
    if re.search(r"Montant|Date d.échéance|Banque", text, re.IGNORECASE):
        return "fr"
    if re.search(r"Importo|Scadenza|Banca", text, re.IGNORECASE):
        return "it"
    return "en"


def extract_from_bytes(file_bytes: bytes, filename: str) -> dict:
    """Extract from uploaded file bytes (for Streamlit file_uploader)."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        return extract_capital_call(tmp_path)
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    import sys, json
    for path in sys.argv[1:]:
        result = extract_capital_call(path)
        del result["raw_text"]
        print(f"\n{path}:")
        print(json.dumps(result, indent=2))
