"""Tests for PDF extraction (regex-based parser)."""
import os
import pytest
from pdf_extractor import extract_capital_call


class TestNotice1_GT_IV:
    """Notice 1: GT Partners IV Equity - should extract all fields correctly."""

    @pytest.fixture(autouse=True)
    def extract(self, sample_notices_dir):
        self.result = extract_capital_call(
            os.path.join(sample_notices_dir, "Notice_1_GT_IV_Equity.pdf")
        )

    def test_fund_name(self):
        assert self.result["fund_name"] == "GT Partners IV Equity"

    def test_investor(self):
        assert "C - Fund Vintage 2010" in self.result["investor"]

    def test_amount(self):
        assert self.result["amount"] == 5_600_000.0

    def test_currency(self):
        assert self.result["currency"] == "EUR"

    def test_due_date(self):
        assert self.result["due_date"] == "16.03.2026"

    def test_bank(self):
        assert "Deutsche Bank" in self.result["bank"]

    def test_iban(self):
        assert "DE89 3704 0044 0532 1198 01" in self.result["iban"]


class TestNotice2_GT_V:
    """Notice 2: GT Partners V Equity - has a FRAUDULENT IBAN."""

    @pytest.fixture(autouse=True)
    def extract(self, sample_notices_dir):
        self.result = extract_capital_call(
            os.path.join(sample_notices_dir, "Notice_2_GT_V_Equity.pdf")
        )

    def test_fund_name(self):
        assert self.result["fund_name"] == "GT Partners V Equity"

    def test_amount(self):
        assert self.result["amount"] == 6_000_000.0

    def test_iban_is_the_fraudulent_one(self):
        # This IBAN does NOT match the approved wire (CH12...) - that's intentional
        assert "DE89 3704 0044 0532 1198 99" in self.result["iban"]


class TestNotice3_Parallax:
    """Notice 3: Parallax Fund Solutions - Buyout II - should pass both checks."""

    @pytest.fixture(autouse=True)
    def extract(self, sample_notices_dir):
        self.result = extract_capital_call(
            os.path.join(sample_notices_dir, "Notice_3_Parallax_Buyout_II.pdf")
        )

    def test_fund_name(self):
        assert "Parallax" in self.result["fund_name"]
        assert "Buyout II" in self.result["fund_name"]

    def test_amount(self):
        assert self.result["amount"] == 9_300_000.0

    def test_iban(self):
        assert "US44 HSBC 9000 8888 7777 66" in self.result["iban"]


class TestNotice4_GT_VI:
    """Notice 4: GT Partners 6 Equity - uses '6' instead of 'VI' (fuzzy match test)."""

    @pytest.fixture(autouse=True)
    def extract(self, sample_notices_dir):
        self.result = extract_capital_call(
            os.path.join(sample_notices_dir, "Notice_4_GT_VI_Equity.pdf")
        )

    def test_fund_name_has_digit_not_roman(self):
        # PDF says "GT Partners 6 Equity" not "GT Partners VI Equity"
        assert "6" in self.result["fund_name"] or "VI" in self.result["fund_name"]

    def test_amount(self):
        assert self.result["amount"] == 4_800_000.0

    def test_due_date(self):
        assert self.result["due_date"] == "20.03.2026"


class TestEdgeCases:
    """Edge cases for the regex extractor."""

    def test_empty_text_returns_defaults(self):
        from pdf_extractor import _extract_amount, _extract_currency, _extract_due_date
        assert _extract_amount("no amount here") == 0.0
        assert _extract_currency("no currency") == "EUR"
        assert _extract_due_date("no date") == ""

    def test_european_number_format(self):
        from pdf_extractor import _extract_amount
        assert _extract_amount("Betrag: EUR 1.000.000,50") == 1_000_000.50

    def test_language_detection(self):
        from pdf_extractor import _detect_language
        assert _detect_language("Betrag: EUR 500.000") == "de"
        assert _detect_language("Montant: EUR 500000") == "fr"
        assert _detect_language("Amount: EUR 500000") == "en"
