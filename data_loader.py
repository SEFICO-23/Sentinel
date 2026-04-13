"""
Data loader for Project Sentinel.
Reads the Excel workbook and provides clean DataFrames for each sheet.
"""
import pandas as pd
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "IO_Case_study_Capital_Calls.xlsx")


def load_commitment_tracker(path: str = DATA_FILE) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Commitment Tracker", header=None)
    df = raw.iloc[3:].reset_index(drop=True)
    df.columns = ["_drop", "Investor", "Fund Name", "Total Commitment",
                   "Total Funded YTD", "Remaining Open Commitment"]
    df = df[["Investor", "Fund Name", "Total Commitment",
             "Total Funded YTD", "Remaining Open Commitment"]]
    for col in ["Total Commitment", "Total Funded YTD", "Remaining Open Commitment"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Fund Name"] = df["Fund Name"].str.strip()
    df["Investor"] = df["Investor"].str.strip()
    df = df[df["Fund Name"] != "Fund Name"].reset_index(drop=True)
    return df


def load_upcoming_calls(path: str = DATA_FILE) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Upcoming Capital Calls", header=None)
    df = raw.iloc[3:].reset_index(drop=True)
    df.columns = ["_drop", "Investor", "Fund Name", "Amount", "Due Date"]
    df = df[["Investor", "Fund Name", "Amount", "Due Date"]]
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Fund Name"] = df["Fund Name"].str.strip()
    df = df[df["Fund Name"] != "Fund Name"].reset_index(drop=True)
    return df


def load_executed_calls(path: str = DATA_FILE) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Executed Capital Calls", header=None)
    df = raw.iloc[3:].reset_index(drop=True)
    df.columns = ["_drop", "Investor", "Fund Name", "Capital Call Amount Paid", "Value Date"]
    df = df[["Investor", "Fund Name", "Capital Call Amount Paid", "Value Date"]]
    df["Capital Call Amount Paid"] = pd.to_numeric(df["Capital Call Amount Paid"], errors="coerce")
    df["Fund Name"] = df["Fund Name"].str.strip()
    df = df[df["Fund Name"] != "Fund Name"].reset_index(drop=True)
    return df


def load_approved_wires(path: str = DATA_FILE) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Approved wire instructions", header=None)
    df = raw.iloc[2:].reset_index(drop=True)
    df.columns = ["_drop", "Fund Name", "Beneficiary Bank", "Swift/BIC",
                   "IBAN / Account Number", "Currency"]
    df = df[["Fund Name", "Beneficiary Bank", "Swift/BIC",
             "IBAN / Account Number", "Currency"]]
    df["Fund Name"] = df["Fund Name"].str.strip()
    df["IBAN / Account Number"] = df["IBAN / Account Number"].astype(str).str.strip()
    df = df[df["Fund Name"] != "Fund Name"].reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=== Commitment Tracker ===")
    print(load_commitment_tracker().to_string())
    print("\n=== Upcoming Calls ===")
    print(load_upcoming_calls().to_string())
    print("\n=== Executed Calls ===")
    print(load_executed_calls().to_string())
    print("\n=== Approved Wires ===")
    print(load_approved_wires().to_string())
