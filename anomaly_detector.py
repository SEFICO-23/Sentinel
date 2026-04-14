"""
Statistical anomaly detection for capital call notices.
Uses z-scores and IQR analysis on historical patterns.
No external ML libraries -- pure Python stdlib (statistics module).
"""
from statistics import mean, stdev
from datetime import datetime
import database as db


def detect_anomalies(fund_name: str, amount: float, due_date: str = None) -> dict:
    """Score a capital call for anomalies based on historical patterns.

    Returns:
        {
            "overall_risk": "low" | "medium" | "high",
            "overall_score": 0-100 (0=normal, 100=extreme anomaly),
            "signals": [
                {
                    "type": "amount",
                    "severity": "low" | "medium" | "high",
                    "score": 0-100,
                    "message": "...",
                    "detail": "..."
                },
                ...
            ]
        }
    """
    signals = [
        _check_amount_anomaly(fund_name, amount),
        _check_timing_anomaly(fund_name, due_date),
        _check_frequency_anomaly(fund_name),
    ]

    overall_risk, overall_score = _compute_overall_risk(signals)

    return {
        "overall_risk": overall_risk,
        "overall_score": overall_score,
        "signals": signals,
    }


def _check_amount_anomaly(fund_name: str, amount: float) -> dict:
    """Check if amount deviates significantly from historical average."""
    history = db.get_executed_calls_for_fund(fund_name)
    amounts = [h["amount"] for h in history]

    if len(amounts) < 2:
        return {"type": "amount", "severity": "low", "score": 0,
                "message": "Insufficient history", "detail": "Less than 2 historical calls"}

    avg = mean(amounts)
    sd = stdev(amounts) if len(amounts) >= 3 else avg * 0.15

    if sd == 0:
        sd = avg * 0.1  # Prevent division by zero

    z = abs(amount - avg) / sd

    # Score: z=0 -> 0, z=1 -> 25, z=2 -> 50, z=3 -> 75, z>=4 -> 100
    score = min(100, int(z * 25))

    if z >= 3:
        severity = "high"
        msg = f"Amount EUR {amount:,.0f} is {z:.1f} std devs from average EUR {avg:,.0f}"
    elif z >= 2:
        severity = "medium"
        msg = f"Amount EUR {amount:,.0f} is notably different from average EUR {avg:,.0f}"
    else:
        severity = "low"
        msg = f"Amount EUR {amount:,.0f} is within normal range (avg EUR {avg:,.0f})"

    return {
        "type": "amount", "severity": severity, "score": score,
        "message": msg,
        "detail": f"Historical: {len(amounts)} calls, avg EUR {avg:,.0f}, std EUR {sd:,.0f}, z-score: {z:.2f}",
    }


def _check_timing_anomaly(fund_name: str, due_date: str = None) -> dict:
    """Check if call timing deviates from historical interval pattern."""
    history = db.get_executed_calls_for_fund(fund_name)

    if len(history) < 3:
        return {"type": "timing", "severity": "low", "score": 0,
                "message": "Insufficient history for timing analysis",
                "detail": "Need 3+ calls to establish interval pattern"}

    # Parse dates and calculate intervals
    dates = []
    for h in history:
        try:
            d = datetime.strptime(str(h["value_date"]).strip(), "%d.%m.%Y")
            dates.append(d)
        except (ValueError, AttributeError):
            continue

    dates.sort()
    intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]

    if not intervals:
        return {"type": "timing", "severity": "low", "score": 0,
                "message": "Could not parse historical dates", "detail": ""}

    avg_interval = mean(intervals)
    last_call = dates[-1]
    days_since_last = (datetime.now() - last_call).days

    # How many average intervals have passed?
    if avg_interval > 0:
        ratio = days_since_last / avg_interval
    else:
        ratio = 1.0

    # Score based on deviation from expected interval
    deviation = abs(ratio - 1.0)
    score = min(100, int(deviation * 50))

    if ratio < 0.3:
        severity = "high"
        msg = f"Call arrived very early: {days_since_last} days since last (avg interval: {avg_interval:.0f} days)"
    elif ratio > 2.5:
        severity = "medium"
        msg = f"Unusually long gap: {days_since_last} days since last call (avg: {avg_interval:.0f} days)"
    else:
        severity = "low"
        msg = f"Timing is normal: {days_since_last} days since last call (avg: {avg_interval:.0f} days)"

    return {
        "type": "timing", "severity": severity, "score": score,
        "message": msg,
        "detail": f"Historical intervals: {len(intervals)} gaps, avg {avg_interval:.0f} days, range {min(intervals)}-{max(intervals)} days",
    }


def _check_frequency_anomaly(fund_name: str) -> dict:
    """Check if there's an unusual burst of calls for this fund."""
    history = db.get_executed_calls_for_fund(fund_name)

    now = datetime.now()
    calls_30d = 0
    calls_90d = 0

    for h in history:
        try:
            d = datetime.strptime(str(h["value_date"]).strip(), "%d.%m.%Y")
            delta = (now - d).days
            if delta <= 30:
                calls_30d += 1
            if delta <= 90:
                calls_90d += 1
        except (ValueError, AttributeError):
            continue

    score = 0
    if calls_30d >= 3:
        severity = "high"
        score = 80
        msg = f"Burst: {calls_30d} calls in the last 30 days"
    elif calls_90d >= 4:
        severity = "medium"
        score = 50
        msg = f"Elevated frequency: {calls_90d} calls in the last 90 days"
    else:
        severity = "low"
        msg = f"Normal frequency: {calls_30d} calls in 30d, {calls_90d} in 90d"

    return {
        "type": "frequency", "severity": severity, "score": score,
        "message": msg,
        "detail": f"Last 30 days: {calls_30d} calls, last 90 days: {calls_90d} calls",
    }


def _compute_overall_risk(signals: list) -> tuple:
    max_score = max(s["score"] for s in signals) if signals else 0
    avg_score = sum(s["score"] for s in signals) / len(signals) if signals else 0
    # Overall = weighted toward max (catches single extreme anomaly)
    overall = int(max_score * 0.6 + avg_score * 0.4)

    if overall >= 60:
        return "high", overall
    if overall >= 30:
        return "medium", overall
    return "low", overall
