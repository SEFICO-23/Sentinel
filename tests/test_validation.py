"""Tests for the validation engine (commitment + wire checks)."""
import os
import pytest
import pandas as pd
from pdf_extractor import extract_capital_call
from validation_engine import (
    normalize_iban,
    normalize_fund_name,
    match_fund_name,
    validate_commitment,
    validate_wire,
    run_full_validation,
)
from data_loader import load_commitment_tracker, load_approved_wires


@pytest.fixture
def ct():
    return load_commitment_tracker()


@pytest.fixture
def wires():
    return load_approved_wires()


# ── Unit Tests ──

class TestNormalizeIBAN:
    def test_removes_whitespace(self):
        assert normalize_iban("DE89 3704 0044 0532 1198 01") == "DE89370400440532119801"

    def test_uppercase(self):
        assert normalize_iban("gb29 scbl 4005") == "GB29SCBL4005"

    def test_already_clean(self):
        assert normalize_iban("DE89370400440532119801") == "DE89370400440532119801"


class TestNormalizeFundName:
    def test_roman_to_digit(self):
        assert "6" in normalize_fund_name("GT Partners VI Equity")

    def test_digit_stays(self):
        assert "6" in normalize_fund_name("GT Partners 6 Equity")

    def test_both_normalize_same(self):
        assert normalize_fund_name("GT Partners VI Equity") == normalize_fund_name("GT Partners 6 Equity")

    def test_roman_iv(self):
        assert "4" in normalize_fund_name("GT Partners IV Equity")


class TestMatchFundName:
    def test_exact_match(self):
        funds = ["GT Partners IV Equity", "GT Partners V Equity"]
        match, score = match_fund_name("GT Partners IV Equity", funds)
        assert match == "GT Partners IV Equity"
        assert score == 100.0

    def test_roman_vs_digit_match(self):
        funds = ["GT Partners VI Equity"]
        match, score = match_fund_name("GT Partners 6 Equity", funds)
        assert match == "GT Partners VI Equity"
        assert score >= 90

    def test_no_match_below_threshold(self):
        funds = ["GT Partners IV Equity"]
        match, score = match_fund_name("Completely Different Fund", funds, threshold=70)
        assert match is None


class TestValidateCommitment:
    def test_within_limit(self):
        result = validate_commitment(1_000_000, 5_000_000)
        assert result["passed"] == True
        assert result["overage"] == 0

    def test_exceeds_limit(self):
        result = validate_commitment(5_000_000, 3_000_000)
        assert result["passed"] == False
        assert result["overage"] == 2_000_000

    def test_exact_limit(self):
        result = validate_commitment(3_000_000, 3_000_000)
        assert result["passed"] == True

    def test_zero_amount_fails(self):
        result = validate_commitment(0, 5_000_000)
        assert result["passed"] == False


class TestValidateWire:
    def test_matching_iban(self):
        result = validate_wire("DE89 3704 0044 0532 1198 01", "DE89 3704 0044 0532 1198 01", "Fund A")
        assert result["passed"] == True

    def test_mismatched_iban(self):
        result = validate_wire("DE89 3704 0044 0532 1198 99", "CH12 0070 0111 2223 3344 5", "Fund B")
        assert result["passed"] == False
        assert "FRAUD" in result["message"]

    def test_whitespace_normalization(self):
        result = validate_wire("DE89370400440532119801", "DE89 3704 0044 0532 1198 01", "Fund C")
        assert result["passed"] == True


# ── Integration Tests (full pipeline) ──

class TestFullValidation:
    """Test the complete extraction -> validation pipeline for all 4 notices."""

    def test_notice_1_fails_commitment(self, sample_notices_dir, ct, wires):
        """Notice 1: EUR 5.6M exceeds EUR 3.9M remaining commitment."""
        ext = extract_capital_call(os.path.join(sample_notices_dir, "Notice_1_GT_IV_Equity.pdf"))
        val = run_full_validation(ext, ct, wires)
        assert val["overall_status"] == "REJECTED - OVER COMMITMENT"
        assert val["commitment_check"]["passed"] == False
        assert val["wire_check"]["passed"] == True

    def test_notice_2_fails_wire(self, sample_notices_dir, ct, wires):
        """Notice 2: IBAN mismatch (fraud signal)."""
        ext = extract_capital_call(os.path.join(sample_notices_dir, "Notice_2_GT_V_Equity.pdf"))
        val = run_full_validation(ext, ct, wires)
        assert val["overall_status"] == "REJECTED - WIRE MISMATCH"
        assert val["commitment_check"]["passed"] == True
        assert val["wire_check"]["passed"] == False

    def test_notice_3_approved(self, sample_notices_dir, ct, wires):
        """Notice 3: Both checks pass."""
        ext = extract_capital_call(os.path.join(sample_notices_dir, "Notice_3_Parallax_Buyout_II.pdf"))
        val = run_full_validation(ext, ct, wires)
        assert val["overall_status"] == "APPROVED"
        assert val["commitment_check"]["passed"] == True
        assert val["wire_check"]["passed"] == True

    def test_notice_4_approved_with_fuzzy_match(self, sample_notices_dir, ct, wires):
        """Notice 4: Fuzzy matches 'GT Partners 6' to 'GT Partners VI'."""
        ext = extract_capital_call(os.path.join(sample_notices_dir, "Notice_4_GT_VI_Equity.pdf"))
        val = run_full_validation(ext, ct, wires)
        assert val["overall_status"] == "APPROVED"
        assert val["fund_name_matched"] == "GT Partners VI Equity"
        assert val["fund_match_score"] >= 90
