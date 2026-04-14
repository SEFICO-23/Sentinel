# Project Sentinel - Presentation Script

**Duration:** ~15-20 minutes (presentation) + 10 minutes (live demo) + Q&A
**Audience:** Internal team / Management

---

## SLIDE 1: Title

> Good morning/afternoon everyone. Today I'm presenting **Project Sentinel** -- a Treasury Operations Automation tool we built to solve a very real problem in our Private Equity capital call processing.

> The goal was simple: take a manual, error-prone workflow and turn it into an automated, auditable, and fraud-resistant system.

**[Pause, advance]**

---

## SLIDE 2: The Problem

> Let me start with why we built this. Our treasury team faces four key challenges:

> **First -- Manual Processing.** Every quarter we receive 10 to 20 capital call PDFs from different GPs. Today, someone manually opens each PDF, copies the fund name, amount, IBAN, and due date into a spreadsheet. That's slow, and it's where mistakes happen.

> **Second -- No Systematic Validation.** When a capital call comes in, we need to check two things: is the amount within our remaining commitment, and is the IBAN correct? Right now that's done ad-hoc. If someone is busy or distracted, a check might be skipped entirely.

> **Third -- Format Chaos.** Every GP sends notices differently. Some are in English, some in German, some in French. Some put the amount at the top, some at the bottom. Some use European number format with dots and commas swapped. There's no standard.

> **Fourth -- Audit Gaps.** If a regulator asks "who approved this EUR 5 million wire transfer on March 16th, and what checks were performed?" -- today we'd struggle to answer that cleanly.

**[Pause, advance]**

---

## SLIDE 3: The Solution

> Project Sentinel solves all four of these in a single platform. Here's the workflow in five steps:

> **Step 1 -- Upload.** The user drags and drops a PDF capital call notice into the web interface. They can upload one at a time or batch-process up to 20 at once.

> **Step 2 -- AI Extraction.** The system automatically extracts the key fields: fund name, amount, currency, due date, IBAN, and bank details. It uses a fast regex parser for well-structured PDFs, and falls back to the Claude AI API for messy or unusual formats.

> **Step 3 -- Auto-Validate.** Two automated checks run instantly. The commitment check verifies the amount is within the fund's remaining open commitment. The wire verification compares the IBAN on the PDF against our approved wire instructions database.

> **Step 4 -- 4-Eye Approval.** If both checks pass, a second person -- a reviewer or admin -- must confirm the execution. The system enforces that the reviewer is a different person from the submitter. There's a two-step confirmation to prevent accidental clicks on multi-million euro payments.

> **Step 5 -- Track and Report.** Everything is logged: who uploaded it, what the validation results were, who approved it, when. The full audit trail is searchable, filterable, and exportable to Excel.

**[Pause, advance]**

---

## SLIDE 4: Validation Engine

> Let me show you how the validation engine works with our test data. We tested with four real-format capital call notices, and the system correctly identified two that should be rejected.

> **Notice 1 -- GT Partners IV.** The GP is requesting EUR 5.6 million, but our remaining open commitment is only EUR 3.9 million. The system flags this immediately: "amount exceeds remaining commitment by EUR 1.7 million." This could be an administrative error on the GP side, or it could mean we need to increase our commitment. Either way, we catch it before anyone sends money.

> **Notice 2 -- GT Partners V.** This is the more dangerous one. The commitment check passes -- EUR 6 million is within our EUR 12 million remaining. But the wire verification catches something critical: the IBAN on the PDF is a **German** account number, while our approved records show a **Swiss** account. Different country, different bank. The system flags this as a potential fraud risk and blocks execution immediately.

> **Notice 3 and 4 both pass** all checks and are approved for execution.

> There's one subtle detail worth mentioning: Notice 4's PDF says "GT Partners **6** Equity" with the digit 6, but our database has "GT Partners **VI** Equity" with a Roman numeral. The system's fuzzy matching engine normalizes Roman numerals to digits before comparison, so it correctly matches them with a 100% confidence score.

**[If asked: "What happens when a notice fails?"]**
> Two paths. For a commitment failure, the analyst can submit a formal amendment request to increase the commitment -- that goes through its own 4-eye approval. For a wire mismatch, the system shows the GP's contact details for immediate escalation, and the incident is logged in the audit trail.

**[Pause, advance]**

---

## SLIDE 5: Key Features

> Beyond the core workflow, we've built 12 additional features that make this production-ready:

> Starting from the top left: **AI Extraction** with the dual-mode parser I mentioned. **Batch Upload** for quarter-end processing. **4-Eye Approval** with role-based access control. And **Dark/Light Mode** because our team works late sometimes.

> On the second row: **Wire Management** with a dual-authorization workflow for updating banking details -- because changing an IBAN should be just as controlled as approving a payment. **Commitment Amendments** for when a GP call exceeds the limit. **Portfolio Metrics** including TVPI and DPI tracking. And a full **Audit Trail** with search, filter, and PDF archive.

> Bottom row: **Multi-Language PDF support** -- the regex parser handles German, French, Italian, and Spanish notices. **Due Date Alerts** with color-coded urgency badges. **Excel Export** for multi-sheet reports. And **Duplicate Detection** that catches both exact matches and near-duplicates.

**[No need to read every feature -- highlight 3-4 that matter most to your audience]**

**[Pause, advance]**

---

## SLIDE 6: Security & Risk Controls

> Security was not an afterthought. We built eight risk controls into the system from day one.

> The **Commitment Check** and **Wire Verification** are the two automated gates. **Duplicate Detection** prevents re-processing of the same capital call, even if it arrives under a different filename.

> The **4-Eye Principle** is enforced at the database level, not just the UI -- even if someone tried to bypass the interface, the system would reject a self-approved transaction.

> On the technical side: all data extracted from PDFs is **HTML-escaped** before rendering, preventing cross-site scripting attacks. This matters because a malicious counterparty could theoretically craft a PDF with embedded script tags in the fund name field.

> **Zero-Amount Guard** prevents silent approval when the PDF parser fails to extract an amount. **Wire Change Audit** requires dual authorization for any banking detail modifications. And SMTP passwords are **never stored in the database** -- they live in browser session memory only.

**[If asked: "Is this SOX/regulatory compliant?"]**
> The system provides the technical controls for compliance -- full audit trail, dual authorization, immutable logging, role separation. Formal certification would require additional procedural documentation and possibly external audit, but the technical foundation is there.

**[Pause, advance]**

---

## SLIDE 7: Architecture & Tech Stack

> The architecture is deliberately simple and self-contained. No cloud infrastructure, no microservices, no external database server.

> At the top: **Streamlit** provides the web interface. It's a Python framework designed for data applications -- fast to develop, easy to maintain.

> The **Smart Extractor** layer runs regex patterns first (free, fast, no API key needed), and only calls the Claude API when regex returns incomplete data. This means the system works fully offline for well-structured PDFs.

> The **Validation Engine** performs commitment checks, wire verification, fuzzy fund name matching, and duplicate detection.

> At the bottom: **SQLite** with WAL mode. Write-Ahead Logging means we get concurrent read/write safety without needing a database server. All mutations are atomic -- if anything fails during a capital call execution, the entire transaction rolls back cleanly.

> On the right you can see the full tech stack. Everything is open-source Python except the optional Claude API integration. And we have **50 automated tests** covering extraction, validation, and database operations.

**[If asked: "Why SQLite instead of PostgreSQL?"]**
> For a treasury team of 5-10 people processing 20-40 capital calls per quarter, SQLite with WAL mode handles the concurrency perfectly. It's zero-configuration, ships with Python, and the database file can be backed up with a simple file copy. If we scale to hundreds of concurrent users, we'd migrate to PostgreSQL -- but the database layer is abstracted so that's a configuration change, not a rewrite.

**[If asked: "Why not a cloud-hosted solution?"]**
> Security. Capital call notices contain banking details, IBANs, and wire instructions. Keeping the system on-premise means the data never leaves our network. A cloud deployment is possible but would require additional security review.

**[Pause, advance]**

---

## SLIDE 8: Roadmap

> We've organized future development into three phases.

> **Now -- things we can add immediately:**
> OCR for scanned PDFs, so we can handle notices that arrive as scanned images rather than digital PDFs. Multi-currency support with live FX rates, since some GPs send notices in USD or GBP. Direct SMTP email sending instead of just generating templates. And Excel export reports, which are already partially built.

> **Next -- medium-term priorities:**
> Real authentication via Azure AD or SSO, replacing the current user selector dropdown. Cash position forecasting based on commitment schedules. Slack or Teams notifications when a capital call is due or fails validation. And regulatory-compliant PDF audit reports for external auditors.

> **Future -- our long-term vision:**
> Direct API integration with GP systems like eFront or Investran, so we receive capital calls electronically instead of parsing PDFs. Machine learning anomaly detection to flag unusual call patterns. SWIFT MT103 payment message generation for straight-through processing. And mobile push notifications for reviewers who need to approve on the go.

**[Pause, advance]**

---

## SLIDE 9: By the Numbers

> Some quick metrics to put this in perspective:

> We're tracking **EUR 255 million** in total commitments across **12 funds** in **3 vintage years** (2010, 2015, 2019).

> The system has processed **34+ historical payments** and has **50 automated tests** covering every critical path.

> The PDF parser supports **5 languages** out of the box, and we've delivered **15 distinct features** in total.

**[Keep this slide brief -- the numbers speak for themselves]**

**[Pause, advance]**

---

## SLIDE 10: Live Demo

> Now let me show you the actual system.

**[Switch to browser at http://localhost:8501]**

### Demo Flow (5-10 minutes):

**1. Dashboard Overview (~1 min)**
> "This is the main dashboard. You can see KPI cards at the top -- EUR 255 million in total commitments, EUR 118 million funded, EUR 137 million remaining. The red banner at the top is a due date alert telling us 4 capital calls are due within 3 days."

> "The vintage filter lets me narrow the view -- if I select 'C - Fund Vintage 2015' I see only those 5 funds."

**2. Process a Good Notice (~2 min)**
> "Let me upload Notice 3 -- Parallax Buyout II."

> [Upload the PDF]

> "On the left you can see the original PDF. On the right, the system has extracted all the fields: fund name, EUR 9.3 million, due date March 18th, the IBAN. It identified this as an English document using the regex parser with high confidence."

> "Both checks passed -- commitment check shows 60.8% utilization, wire verification confirms the IBAN matches our approved records."

> "Now I need a reviewer. I'm logged in as Sebastian Mueller -- let me select Anna Schmidt as the second pair of eyes. I click 'Confirm & Execute'... confirmation dialog... 'Yes, Execute Now'."

> "Done. The commitment tracker is updated, the record is moved to executed, and an email template is generated."

**3. Process a Bad Notice (~2 min)**
> "Now let me show what happens with a problematic notice. Notice 2 -- GT Partners V."

> [Upload the PDF]

> "The commitment check passes -- EUR 6 million is within the EUR 12 million remaining. But look at the wire verification: **FAIL**. The IBAN on the PDF is DE89... -- a German account. But our approved records show CH12... -- a Swiss account. The system flags this as a potential fraud risk."

> "Notice it also shows the GP contact for immediate escalation -- Claire Dubois at GT Partners, with her email and phone number."

**4. Batch Upload (~1 min)**
> "For quarter-end, you don't want to process one at a time. Let me upload all 4 notices together."

> [Select all 4 PDFs]

> "The progress bar runs through all four. Here's the summary table: Notice 3 and 4 are ready to approve, Notice 1 and 2 are rejected. I can expand each one to see the full validation details."

**5. Dark Mode (~10 sec)**
> "And for those late-night quarter-end sessions..."

> [Toggle dark mode]

> "Full dark mode support across every page."

**6. Audit Log (~30 sec)**
> "Finally, the audit log. Everything we just did is recorded here -- I can filter by status, fund, reviewer, or date range. And I can download the full audit trail as an Excel file."

---

## Q&A Cheat Sheet

### "How long did this take to build?"
> The core system (extraction, validation, approval workflow, database) was built in one intensive sprint. The 15 additional features (batch upload, wire management, amendments, portfolio tracking, etc.) were developed in parallel across three waves.

### "What happens if the PDF parser fails?"
> Two fallbacks. First, the system tries the Claude AI API for a second extraction attempt. If that also fails (or isn't configured), the system shows a clear error message and blocks processing -- it never silently approves incomplete data.

### "Can we use this with real data?"
> Yes. Delete the `sentinel.db` file, replace the Excel with your actual commitment tracker, and the system re-seeds from your data on first launch. The PDF parser works with any standard capital call format.

### "What about compliance / audit requirements?"
> Every action is logged with timestamp, user identity, validation results, and reviewer approval. The audit log is searchable and exportable. Wire instruction changes require dual authorization. The system enforces segregation of duties between submitter and reviewer.

### "Is the Claude API required?"
> No. The regex parser handles well-structured PDFs in 5 languages without any API key. The Claude API is an optional enhancement for truly unstructured or unusual document formats.

### "How secure is the data?"
> All data stays on-premise in a SQLite database file. SMTP passwords are never written to disk. PDF-sourced content is HTML-escaped to prevent XSS attacks. The 4-eye principle is enforced at the database layer, not just the UI.

### "Can it handle other document types (Excel notices, emails)?"
> Not currently -- it's designed for PDF capital call notices. Adding Excel or email parsing would be a future enhancement, and the modular architecture makes that straightforward.

### "What's the cost?"
> Zero. All dependencies are open-source. The Claude API is optional and pay-per-use (roughly $0.01-0.03 per PDF extraction). The system runs entirely on a single laptop or server.

### "Can multiple people use it simultaneously?"
> Yes. SQLite with WAL mode supports multiple concurrent readers and writers. Streamlit handles multiple browser sessions. For a team of 5-10 people, this works perfectly.

### "Why Streamlit instead of React or a proper frontend?"
> Speed of development and maintainability. Streamlit lets a Python-fluent treasury team maintain and extend the application without needing frontend developers. If we needed to scale to a customer-facing product, we'd migrate to React -- but for an internal operations tool, Streamlit is the right choice.
