"""
Validation engine for Project Sentinel.
Performs commitment checks and wire instruction verification with fuzzy matching.
"""
from rapidfuzz import fuzz
import re


def normalize_iban(iban: str) -> str:
    """Remove all whitespace from IBAN for comparison."""
    return re.sub(r"\s+", "", iban).upper()


def normalize_fund_name(name: str) -> str:
    """Normalize fund names for fuzzy matching.
    Handles roman numeral vs digit differences (VI vs 6), extra whitespace, etc.
    """
    roman_to_digit = {
        "I": "1", "II": "2", "III": "3", "IV": "4", "V": "5",
        "VI": "6", "VII": "7", "VIII": "8", "IX": "9", "X": "10",
    }
    name = name.strip().upper()
    # Replace roman numerals with digits (whole word only, longest first)
    for roman in sorted(roman_to_digit.keys(), key=len, reverse=True):
        name = re.sub(rf"\b{roman}\b", roman_to_digit[roman], name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name)
    return name


def match_fund_name(extracted_name: str, known_funds: list[str], threshold: int = 70) -> tuple[str | None, int]:
    """Find the best matching fund name from the known list.
    Returns (matched_name, score) or (None, 0) if no match above threshold.
    """
    norm_extracted = normalize_fund_name(extracted_name)
    best_match = None
    best_score = 0
    for known in known_funds:
        norm_known = normalize_fund_name(known)
        score = fuzz.ratio(norm_extracted, norm_known)
        if score > best_score:
            best_score = score
            best_match = known
    if best_score >= threshold:
        return best_match, best_score
    return None, 0


def validate_commitment(amount: float, remaining_commitment: float) -> dict:
    """Check if the capital call amount is within the remaining open commitment."""
    if amount <= 0:
        return {
            "check": "Commitment Check",
            "passed": False,
            "amount_requested": amount,
            "remaining_commitment": remaining_commitment,
            "utilization_pct": 0,
            "overage": 0,
            "message": "FAIL: Invalid or missing amount (EUR 0 or negative). Cannot proceed.",
        }
    passed = amount <= remaining_commitment
    utilization = (amount / remaining_commitment * 100) if remaining_commitment > 0 else 0
    return {
        "check": "Commitment Check",
        "passed": passed,
        "amount_requested": amount,
        "remaining_commitment": remaining_commitment,
        "utilization_pct": round(utilization, 1),
        "overage": max(0, amount - remaining_commitment),
        "message": (
            f"PASS: EUR {amount:,.0f} is within remaining commitment of EUR {remaining_commitment:,.0f} "
            f"({utilization:.1f}% utilization)"
            if passed else
            f"FAIL: EUR {amount:,.0f} exceeds remaining commitment of EUR {remaining_commitment:,.0f} "
            f"by EUR {amount - remaining_commitment:,.0f}"
        ),
    }


def validate_wire(extracted_iban: str, approved_iban: str, fund_name: str) -> dict:
    """Compare the IBAN on the PDF against the approved wire instructions."""
    norm_extracted = normalize_iban(extracted_iban)
    norm_approved = normalize_iban(approved_iban)
    passed = norm_extracted == norm_approved
    return {
        "check": "Wire Verification",
        "passed": passed,
        "extracted_iban": extracted_iban,
        "approved_iban": approved_iban,
        "fund_name": fund_name,
        "message": (
            f"PASS: IBAN matches approved wire instructions for {fund_name}"
            if passed else
            f"FAIL: IBAN mismatch for {fund_name}. "
            f"PDF shows '{extracted_iban}' but approved is '{approved_iban}'. "
            f"POTENTIAL FRAUD RISK - escalate immediately."
        ),
    }


def run_full_validation(extracted: dict, commitment_df, wires_df=None) -> dict:
    """Run all validation checks against a single extracted capital call notice.

    Args:
        wires_df: Wire instructions DataFrame. If None, loads from database.
    """
    if wires_df is None:
        import database as db
        wires_df = db.get_approved_wires_df()

    fund_name_raw = extracted["fund_name"]
    amount = extracted["amount"]
    iban = extracted["iban"]

    # Step 1: Match fund name
    known_funds = commitment_df["Fund Name"].tolist()
    matched_fund, match_score = match_fund_name(fund_name_raw, known_funds)

    result = {
        "fund_name_extracted": fund_name_raw,
        "fund_name_matched": matched_fund,
        "fund_match_score": match_score,
        "amount": amount,
        "currency": extracted.get("currency", "EUR"),
        "due_date": extracted.get("due_date", ""),
        "investor": extracted.get("investor", ""),
        "commitment_check": None,
        "wire_check": None,
        "overall_status": "UNKNOWN",
    }

    if matched_fund is None:
        result["overall_status"] = "FUND NOT FOUND"
        result["commitment_check"] = {
            "check": "Commitment Check",
            "passed": False,
            "message": f"Could not match fund name '{fund_name_raw}' to any known fund.",
        }
        result["wire_check"] = {
            "check": "Wire Verification",
            "passed": False,
            "message": f"Cannot verify wire - fund not identified.",
        }
        return result

    # Step 2: Commitment check
    fund_row = commitment_df[commitment_df["Fund Name"] == matched_fund].iloc[0]
    remaining = fund_row["Remaining Open Commitment"]
    result["commitment_check"] = validate_commitment(amount, remaining)

    # Step 3: Wire check
    # Match fund in wires table (also needs fuzzy matching)
    wire_funds = wires_df["Fund Name"].tolist()
    wire_match, _ = match_fund_name(matched_fund, wire_funds, threshold=60)
    if wire_match:
        approved_iban = wires_df[wires_df["Fund Name"] == wire_match]["IBAN / Account Number"].iloc[0]
        result["wire_check"] = validate_wire(iban, approved_iban, matched_fund)
    else:
        result["wire_check"] = {
            "check": "Wire Verification",
            "passed": False,
            "message": f"No approved wire instructions found for '{matched_fund}'.",
        }

    # Overall status
    if result["commitment_check"]["passed"] and result["wire_check"]["passed"]:
        result["overall_status"] = "APPROVED"
    elif not result["commitment_check"]["passed"] and not result["wire_check"]["passed"]:
        result["overall_status"] = "REJECTED - DUAL FAILURE"
    elif not result["wire_check"]["passed"]:
        result["overall_status"] = "REJECTED - WIRE MISMATCH"
    else:
        result["overall_status"] = "REJECTED - OVER COMMITMENT"

    return result
