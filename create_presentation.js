const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

let pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Calibrium AG";
pres.title = "Project Sentinel - Treasury Operations Automation";

// ── Brand Constants ──
const NAVY = "1E3161";
const NAVY_DARK = "0B1929";
const SAGE = "DDE9E8";
const WHITE = "FFFFFF";
const TEXT_DARK = "1E3161";
const TEXT_LIGHT = "5A6B7F";
const TEXT_WHITE = "E8EDF2";
const GREEN = "27AE60";
const RED = "E74C3C";
const AMBER = "F39C12";
const BORDER = "E0E0E0";

const FONT_TITLE = "Georgia";
const FONT_BODY = "Calibri";

// Logo as base64
const logoPath = path.join(__dirname, "assets", "calibrium_logo_white.png");
const logoData = "image/png;base64," + fs.readFileSync(logoPath).toString("base64");
const logoDarkPath = path.join(__dirname, "assets", "calibrium_logo.png");
const logoDarkData = "image/png;base64," + fs.readFileSync(logoDarkPath).toString("base64");

// ═══════════════════════════════════════════
// SLIDE 1: TITLE
// ═══════════════════════════════════════════
let s1 = pres.addSlide();
s1.background = { color: NAVY };
s1.addImage({ data: logoData, x: 0.7, y: 0.5, w: 2.2, h: 0.55 });
s1.addText("Project Sentinel", {
  x: 0.7, y: 1.6, w: 8.5, h: 1.2,
  fontSize: 44, fontFace: FONT_TITLE, color: WHITE, bold: true, margin: 0,
});
s1.addText("Treasury Operations Automation", {
  x: 0.7, y: 2.7, w: 8, h: 0.6,
  fontSize: 22, fontFace: FONT_BODY, color: SAGE, margin: 0,
});
s1.addText("Private Equity Capital Call Processing", {
  x: 0.7, y: 3.3, w: 8, h: 0.5,
  fontSize: 16, fontFace: FONT_BODY, color: TEXT_WHITE, margin: 0,
});
s1.addShape(pres.shapes.RECTANGLE, {
  x: 0.7, y: 4.2, w: 1.5, h: 0.05, fill: { color: SAGE },
});
s1.addText("Calibrium AG  |  April 2026", {
  x: 0.7, y: 4.6, w: 5, h: 0.4,
  fontSize: 12, fontFace: FONT_BODY, color: TEXT_WHITE, italic: true, margin: 0,
});

// ═══════════════════════════════════════════
// SLIDE 2: THE PROBLEM
// ═══════════════════════════════════════════
let s2 = pres.addSlide();
s2.background = { color: WHITE };
s2.addText("The Problem", {
  x: 0.7, y: 0.4, w: 8, h: 0.7,
  fontSize: 36, fontFace: FONT_TITLE, color: TEXT_DARK, bold: true, margin: 0,
});
s2.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.1, w: 1.2, h: 0.04, fill: { color: NAVY } });

const problems = [
  { title: "Manual Processing", desc: "Treasury teams handle 10-20 capital call PDFs per quarter manually, copying data into spreadsheets" },
  { title: "No Validation", desc: "Commitment checks and wire verification done ad-hoc, creating fraud exposure" },
  { title: "Format Chaos", desc: "Each GP sends notices in different formats, languages, and layouts" },
  { title: "Audit Gaps", desc: "No centralized trail of who approved what, when, and why" },
];

problems.forEach((p, i) => {
  const y = 1.6 + i * 1.0;
  s2.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.7, y: y, w: 8.6, h: 0.85,
    fill: { color: i % 2 === 0 ? SAGE : WHITE },
    rectRadius: 0.08,
    line: { color: BORDER, width: 0.5 },
  });
  s2.addShape(pres.shapes.OVAL, {
    x: 1.0, y: y + 0.2, w: 0.45, h: 0.45,
    fill: { color: RED },
  });
  s2.addText(String(i + 1), {
    x: 1.0, y: y + 0.2, w: 0.45, h: 0.45,
    fontSize: 16, fontFace: FONT_BODY, color: WHITE, bold: true, align: "center", valign: "middle",
  });
  s2.addText(p.title, {
    x: 1.7, y: y + 0.08, w: 7, h: 0.35,
    fontSize: 16, fontFace: FONT_BODY, color: TEXT_DARK, bold: true, margin: 0,
  });
  s2.addText(p.desc, {
    x: 1.7, y: y + 0.42, w: 7.3, h: 0.35,
    fontSize: 12, fontFace: FONT_BODY, color: TEXT_LIGHT, margin: 0,
  });
});

// ═══════════════════════════════════════════
// SLIDE 3: THE SOLUTION
// ═══════════════════════════════════════════
let s3 = pres.addSlide();
s3.background = { color: NAVY };
s3.addImage({ data: logoData, x: 8.5, y: 0.3, w: 1.2, h: 0.3 });
s3.addText("The Solution: Project Sentinel", {
  x: 0.7, y: 0.4, w: 8, h: 0.7,
  fontSize: 32, fontFace: FONT_TITLE, color: WHITE, bold: true, margin: 0,
});

const solutions = [
  { title: "Upload PDF", desc: "Drag-and-drop single or batch upload", icon: "1" },
  { title: "AI Extracts Data", desc: "Regex + Claude API dual-mode parsing", icon: "2" },
  { title: "Auto-Validate", desc: "Commitment & wire checks run instantly", icon: "3" },
  { title: "4-Eye Approve", desc: "Reviewer confirms, system executes", icon: "4" },
  { title: "Track & Report", desc: "Full audit trail, Excel exports", icon: "5" },
];

solutions.forEach((s, i) => {
  const x = 0.4 + i * 1.9;
  s3.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x, y: 1.5, w: 1.7, h: 3.5,
    fill: { color: "132338" }, rectRadius: 0.1,
    shadow: { type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.3 },
  });
  s3.addShape(pres.shapes.OVAL, {
    x: x + 0.55, y: 1.8, w: 0.6, h: 0.6,
    fill: { color: SAGE },
  });
  s3.addText(s.icon, {
    x: x + 0.55, y: 1.8, w: 0.6, h: 0.6,
    fontSize: 20, fontFace: FONT_BODY, color: NAVY, bold: true, align: "center", valign: "middle",
  });
  s3.addText(s.title, {
    x: x + 0.1, y: 2.6, w: 1.5, h: 0.5,
    fontSize: 14, fontFace: FONT_BODY, color: WHITE, bold: true, align: "center", margin: 0,
  });
  s3.addText(s.desc, {
    x: x + 0.1, y: 3.1, w: 1.5, h: 1.0,
    fontSize: 11, fontFace: FONT_BODY, color: TEXT_WHITE, align: "center", margin: 0,
  });
});

s3.addShape(pres.shapes.LINE, {
  x: 1.65, y: 3.0, w: 7.0, h: 0,
  line: { color: SAGE, width: 1, dashType: "dash" },
});

// ═══════════════════════════════════════════
// SLIDE 4: VALIDATION ENGINE
// ═══════════════════════════════════════════
let s4 = pres.addSlide();
s4.background = { color: WHITE };
s4.addText("Validation Engine", {
  x: 0.7, y: 0.4, w: 8, h: 0.7,
  fontSize: 36, fontFace: FONT_TITLE, color: TEXT_DARK, bold: true, margin: 0,
});
s4.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.1, w: 1.2, h: 0.04, fill: { color: NAVY } });
s4.addText("Every notice runs through automated risk controls before a human sees it", {
  x: 0.7, y: 1.3, w: 8, h: 0.4,
  fontSize: 14, fontFace: FONT_BODY, color: TEXT_LIGHT, italic: true, margin: 0,
});

// Validation results table
const valData = [
  [
    { text: "Notice", options: { fill: { color: NAVY }, color: WHITE, bold: true, fontSize: 11, fontFace: FONT_BODY } },
    { text: "Fund", options: { fill: { color: NAVY }, color: WHITE, bold: true, fontSize: 11, fontFace: FONT_BODY } },
    { text: "Amount", options: { fill: { color: NAVY }, color: WHITE, bold: true, fontSize: 11, fontFace: FONT_BODY } },
    { text: "Commitment", options: { fill: { color: NAVY }, color: WHITE, bold: true, fontSize: 11, fontFace: FONT_BODY } },
    { text: "Wire", options: { fill: { color: NAVY }, color: WHITE, bold: true, fontSize: 11, fontFace: FONT_BODY } },
    { text: "Result", options: { fill: { color: NAVY }, color: WHITE, bold: true, fontSize: 11, fontFace: FONT_BODY } },
  ],
  [
    { text: "Notice 1", options: { fontSize: 10 } },
    { text: "GT Partners IV", options: { fontSize: 10 } },
    { text: "EUR 5.6M", options: { fontSize: 10 } },
    { text: "FAIL", options: { fontSize: 10, color: RED, bold: true } },
    { text: "PASS", options: { fontSize: 10, color: GREEN, bold: true } },
    { text: "REJECTED", options: { fontSize: 10, color: RED, bold: true, fill: { color: "FDEDEE" } } },
  ],
  [
    { text: "Notice 2", options: { fontSize: 10 } },
    { text: "GT Partners V", options: { fontSize: 10 } },
    { text: "EUR 6.0M", options: { fontSize: 10 } },
    { text: "PASS", options: { fontSize: 10, color: GREEN, bold: true } },
    { text: "FAIL", options: { fontSize: 10, color: RED, bold: true } },
    { text: "REJECTED", options: { fontSize: 10, color: RED, bold: true, fill: { color: "FDEDEE" } } },
  ],
  [
    { text: "Notice 3", options: { fontSize: 10 } },
    { text: "Parallax Buyout II", options: { fontSize: 10 } },
    { text: "EUR 9.3M", options: { fontSize: 10 } },
    { text: "PASS", options: { fontSize: 10, color: GREEN, bold: true } },
    { text: "PASS", options: { fontSize: 10, color: GREEN, bold: true } },
    { text: "APPROVED", options: { fontSize: 10, color: GREEN, bold: true, fill: { color: "E8F8EF" } } },
  ],
  [
    { text: "Notice 4", options: { fontSize: 10 } },
    { text: "GT Partners VI", options: { fontSize: 10 } },
    { text: "EUR 4.8M", options: { fontSize: 10 } },
    { text: "PASS", options: { fontSize: 10, color: GREEN, bold: true } },
    { text: "PASS", options: { fontSize: 10, color: GREEN, bold: true } },
    { text: "APPROVED", options: { fontSize: 10, color: GREEN, bold: true, fill: { color: "E8F8EF" } } },
  ],
];

s4.addTable(valData, {
  x: 0.7, y: 1.9, w: 8.6,
  colW: [1.1, 1.8, 1.2, 1.3, 1.0, 1.2],
  border: { pt: 0.5, color: BORDER },
  rowH: [0.45, 0.4, 0.4, 0.4, 0.4],
  fontFace: FONT_BODY,
});

// Key findings
s4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.7, y: 4.2, w: 4.1, h: 1.1,
  fill: { color: "FDEDEE" }, rectRadius: 0.08,
});
s4.addText([
  { text: "Notice 1: ", options: { bold: true, color: RED } },
  { text: "EUR 5.6M exceeds EUR 3.9M remaining commitment", options: { color: TEXT_DARK } },
], { x: 0.9, y: 4.3, w: 3.8, h: 0.4, fontSize: 11, fontFace: FONT_BODY, margin: 0 });
s4.addText([
  { text: "Notice 2: ", options: { bold: true, color: RED } },
  { text: "IBAN mismatch - potential wire fraud signal", options: { color: TEXT_DARK } },
], { x: 0.9, y: 4.7, w: 3.8, h: 0.4, fontSize: 11, fontFace: FONT_BODY, margin: 0 });

s4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 5.2, y: 4.2, w: 4.1, h: 1.1,
  fill: { color: "E8F8EF" }, rectRadius: 0.08,
});
s4.addText([
  { text: "Fuzzy Matching: ", options: { bold: true, color: GREEN } },
  { text: '"GT Partners 6" correctly matched to "GT Partners VI" via Roman numeral normalization', options: { color: TEXT_DARK } },
], { x: 5.4, y: 4.3, w: 3.8, h: 0.9, fontSize: 11, fontFace: FONT_BODY, margin: 0 });


// ═══════════════════════════════════════════
// SLIDE 5: KEY FEATURES
// ═══════════════════════════════════════════
let s5 = pres.addSlide();
s5.background = { color: WHITE };
s5.addText("Key Features", {
  x: 0.7, y: 0.4, w: 8, h: 0.7,
  fontSize: 36, fontFace: FONT_TITLE, color: TEXT_DARK, bold: true, margin: 0,
});
s5.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.1, w: 1.2, h: 0.04, fill: { color: NAVY } });

const features = [
  ["AI Extraction", "Regex + Claude API\ndual-mode parsing"],
  ["Batch Upload", "Process 10-20 PDFs\nat once"],
  ["4-Eye Approval", "Role-based with\n2-step confirmation"],
  ["Dark / Light Mode", "Full theme support\nacross all pages"],
  ["Wire Management", "Dual-auth workflow\nfor banking changes"],
  ["Commitment Amend", "Formal increase\nrequest workflow"],
  ["Portfolio Metrics", "TVPI / DPI tracking\nwith cash flows"],
  ["Audit Trail", "Filter, search, export\nwith PDF archive"],
  ["Multi-Language", "EN / DE / FR / IT / ES\nPDF support"],
  ["Due Date Alerts", "Color-coded urgency\nwith countdowns"],
  ["Excel Export", "Multi-sheet reports\nfor offline analysis"],
  ["Duplicate Detection", "Exact + fuzzy match\nwith override"],
];

features.forEach((f, i) => {
  const col = i % 4;
  const row = Math.floor(i / 4);
  const x = 0.5 + col * 2.35;
  const y = 1.5 + row * 1.35;
  s5.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x, y: y, w: 2.15, h: 1.15,
    fill: { color: row === 1 ? SAGE : WHITE },
    rectRadius: 0.08,
    line: { color: BORDER, width: 0.5 },
    shadow: { type: "outer", color: "000000", blur: 4, offset: 1, angle: 135, opacity: 0.08 },
  });
  s5.addText(f[0], {
    x: x + 0.1, y: y + 0.1, w: 1.95, h: 0.4,
    fontSize: 13, fontFace: FONT_BODY, color: NAVY, bold: true, margin: 0,
  });
  s5.addText(f[1], {
    x: x + 0.1, y: y + 0.5, w: 1.95, h: 0.55,
    fontSize: 10, fontFace: FONT_BODY, color: TEXT_LIGHT, margin: 0,
  });
});

// ═══════════════════════════════════════════
// SLIDE 6: SECURITY & RISK CONTROLS
// ═══════════════════════════════════════════
let s6 = pres.addSlide();
s6.background = { color: NAVY };
s6.addImage({ data: logoData, x: 8.5, y: 0.3, w: 1.2, h: 0.3 });
s6.addText("Security & Risk Controls", {
  x: 0.7, y: 0.4, w: 8, h: 0.7,
  fontSize: 32, fontFace: FONT_TITLE, color: WHITE, bold: true, margin: 0,
});

const controls = [
  { title: "Commitment Check", desc: "Validates amount against remaining open commitment before approval" },
  { title: "Wire Verification", desc: "IBAN normalized and compared against approved wire instructions database" },
  { title: "Duplicate Detection", desc: "Exact + fuzzy matching prevents re-processing of same capital call" },
  { title: "4-Eye Principle", desc: "Reviewer must be a different person with reviewer/admin role" },
  { title: "XSS Prevention", desc: "All PDF-sourced strings HTML-escaped before rendering in the UI" },
  { title: "Zero-Amount Guard", desc: "Missing or unparseable amounts blocked from silent approval" },
  { title: "Wire Change Audit", desc: "Dual-authorization workflow for any banking detail modifications" },
  { title: "SMTP Isolation", desc: "Email passwords stored in session memory only, never persisted to DB" },
];

controls.forEach((c, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const x = 0.5 + col * 4.7;
  const y = 1.4 + row * 1.0;
  s6.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x, y: y, w: 4.5, h: 0.85,
    fill: { color: "132338" }, rectRadius: 0.08,
  });
  s6.addShape(pres.shapes.OVAL, {
    x: x + 0.15, y: y + 0.2, w: 0.45, h: 0.45,
    fill: { color: GREEN },
  });
  s6.addText("S", {
    x: x + 0.15, y: y + 0.2, w: 0.45, h: 0.45,
    fontSize: 16, fontFace: FONT_BODY, color: WHITE, bold: true, align: "center", valign: "middle",
  });
  s6.addText(c.title, {
    x: x + 0.75, y: y + 0.08, w: 3.5, h: 0.35,
    fontSize: 13, fontFace: FONT_BODY, color: WHITE, bold: true, margin: 0,
  });
  s6.addText(c.desc, {
    x: x + 0.75, y: y + 0.42, w: 3.5, h: 0.35,
    fontSize: 10, fontFace: FONT_BODY, color: TEXT_WHITE, margin: 0,
  });
});


// ═══════════════════════════════════════════
// SLIDE 7: TECH STACK & ARCHITECTURE
// ═══════════════════════════════════════════
let s7 = pres.addSlide();
s7.background = { color: WHITE };
s7.addText("Architecture & Tech Stack", {
  x: 0.7, y: 0.4, w: 8, h: 0.7,
  fontSize: 36, fontFace: FONT_TITLE, color: TEXT_DARK, bold: true, margin: 0,
});
s7.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.1, w: 1.2, h: 0.04, fill: { color: NAVY } });

// Left: Architecture diagram as text blocks
const archLayers = [
  { label: "Streamlit Web UI", sub: "Dashboard / Process / Audit / Wire Mgmt", color: NAVY },
  { label: "Smart Extractor", sub: "Regex (primary) + Claude API (fallback)", color: "2A4080" },
  { label: "Validation Engine", sub: "Commitment + Wire + Fuzzy Match + Duplicate", color: "2A4080" },
  { label: "SQLite Database", sub: "WAL mode / Atomic transactions / Full audit", color: NAVY },
];

archLayers.forEach((a, i) => {
  const y = 1.5 + i * 0.95;
  s7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.7, y: y, w: 4.5, h: 0.8,
    fill: { color: a.color }, rectRadius: 0.08,
    shadow: { type: "outer", color: "000000", blur: 4, offset: 1, angle: 135, opacity: 0.1 },
  });
  s7.addText(a.label, {
    x: 0.9, y: y + 0.08, w: 4, h: 0.35,
    fontSize: 14, fontFace: FONT_BODY, color: WHITE, bold: true, margin: 0,
  });
  s7.addText(a.sub, {
    x: 0.9, y: y + 0.4, w: 4, h: 0.3,
    fontSize: 10, fontFace: FONT_BODY, color: TEXT_WHITE, margin: 0,
  });
  if (i < archLayers.length - 1) {
    s7.addShape(pres.shapes.LINE, {
      x: 2.95, y: y + 0.8, w: 0, h: 0.15,
      line: { color: BORDER, width: 2 },
    });
  }
});

// Right: Tech stack
const stack = [
  ["Python 3.10+", "Core language"],
  ["Streamlit", "Web UI framework"],
  ["SQLite (WAL)", "Persistent database"],
  ["Plotly", "Interactive charts"],
  ["pdfplumber", "PDF text extraction"],
  ["rapidfuzz", "Fuzzy string matching"],
  ["Claude API", "LLM extraction (optional)"],
  ["openpyxl", "Excel read/write"],
];

s7.addText("Tech Stack", {
  x: 5.8, y: 1.5, w: 3.5, h: 0.4,
  fontSize: 16, fontFace: FONT_BODY, color: NAVY, bold: true, margin: 0,
});

stack.forEach((t, i) => {
  const y = 2.0 + i * 0.42;
  s7.addText(t[0], {
    x: 5.8, y: y, w: 1.8, h: 0.35,
    fontSize: 11, fontFace: FONT_BODY, color: TEXT_DARK, bold: true, margin: 0,
  });
  s7.addText(t[1], {
    x: 7.6, y: y, w: 2, h: 0.35,
    fontSize: 10, fontFace: FONT_BODY, color: TEXT_LIGHT, margin: 0,
  });
});

// Test stats
s7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 5.8, y: 4.4, w: 3.8, h: 0.9,
  fill: { color: SAGE }, rectRadius: 0.08,
});
s7.addText([
  { text: "50 Tests Passing", options: { bold: true, fontSize: 16, color: NAVY } },
  { text: "\nExtraction + Validation + Database coverage", options: { fontSize: 10, color: TEXT_LIGHT, breakLine: true } },
], { x: 6.0, y: 4.5, w: 3.4, h: 0.7, fontFace: FONT_BODY, margin: 0 });


// ═══════════════════════════════════════════
// SLIDE 8: ROADMAP
// ═══════════════════════════════════════════
let s8 = pres.addSlide();
s8.background = { color: WHITE };
s8.addText("Roadmap & Future Outlook", {
  x: 0.7, y: 0.4, w: 8, h: 0.7,
  fontSize: 36, fontFace: FONT_TITLE, color: TEXT_DARK, bold: true, margin: 0,
});
s8.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.1, w: 1.2, h: 0.04, fill: { color: NAVY } });

const roadmap = [
  { phase: "Now", color: GREEN, items: ["OCR for scanned PDFs", "Multi-currency + FX rates", "SMTP email sending", "Excel export reports"] },
  { phase: "Next", color: AMBER, items: ["SSO / Azure AD auth", "Cash position forecasting", "Slack/Teams notifications", "Regulatory audit PDF export"] },
  { phase: "Future", color: NAVY, items: ["GP Portal API integration", "ML anomaly detection", "SWIFT MT103 generation", "Mobile push approvals"] },
];

roadmap.forEach((r, i) => {
  const x = 0.5 + i * 3.15;
  s8.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x, y: 1.5, w: 2.95, h: 3.8,
    fill: { color: WHITE }, rectRadius: 0.1,
    line: { color: BORDER, width: 0.5 },
    shadow: { type: "outer", color: "000000", blur: 4, offset: 1, angle: 135, opacity: 0.08 },
  });
  s8.addShape(pres.shapes.RECTANGLE, {
    x: x, y: 1.5, w: 2.95, h: 0.55,
    fill: { color: r.color }, rectRadius: 0,
  });
  // Round only top corners by overlaying a shape
  s8.addText(r.phase, {
    x: x, y: 1.5, w: 2.95, h: 0.55,
    fontSize: 18, fontFace: FONT_BODY, color: WHITE, bold: true, align: "center", valign: "middle",
  });
  r.items.forEach((item, j) => {
    s8.addShape(pres.shapes.OVAL, {
      x: x + 0.25, y: 2.3 + j * 0.72, w: 0.25, h: 0.25,
      fill: { color: r.color },
    });
    s8.addText(item, {
      x: x + 0.65, y: 2.25 + j * 0.72, w: 2.1, h: 0.35,
      fontSize: 12, fontFace: FONT_BODY, color: TEXT_DARK, margin: 0,
    });
  });
});


// ═══════════════════════════════════════════
// SLIDE 9: METRICS & KPIs
// ═══════════════════════════════════════════
let s9 = pres.addSlide();
s9.background = { color: NAVY };
s9.addImage({ data: logoData, x: 8.5, y: 0.3, w: 1.2, h: 0.3 });
s9.addText("By the Numbers", {
  x: 0.7, y: 0.4, w: 8, h: 0.7,
  fontSize: 32, fontFace: FONT_TITLE, color: WHITE, bold: true, margin: 0,
});

const metrics = [
  { num: "EUR 255M", label: "Total Commitments\nTracked" },
  { num: "12", label: "Funds Across\n3 Vintages" },
  { num: "34+", label: "Historical\nPayments" },
  { num: "50", label: "Automated\nTests Passing" },
  { num: "5", label: "Languages\nSupported" },
  { num: "15", label: "Features\nDelivered" },
];

metrics.forEach((m, i) => {
  const col = i % 3;
  const row = Math.floor(i / 3);
  const x = 0.7 + col * 3.1;
  const y = 1.4 + row * 2.0;
  s9.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x, y: y, w: 2.8, h: 1.7,
    fill: { color: "132338" }, rectRadius: 0.1,
    shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.25 },
  });
  s9.addText(m.num, {
    x: x, y: y + 0.2, w: 2.8, h: 0.7,
    fontSize: 36, fontFace: FONT_TITLE, color: SAGE, bold: true, align: "center", margin: 0,
  });
  s9.addText(m.label, {
    x: x, y: y + 0.95, w: 2.8, h: 0.6,
    fontSize: 12, fontFace: FONT_BODY, color: TEXT_WHITE, align: "center", margin: 0,
  });
});


// ═══════════════════════════════════════════
// SLIDE 10: CLOSING / LIVE DEMO
// ═══════════════════════════════════════════
let s10 = pres.addSlide();
s10.background = { color: NAVY };
s10.addImage({ data: logoData, x: 3.4, y: 0.8, w: 3.2, h: 0.8 });
s10.addText("Live Demo", {
  x: 0.7, y: 2.0, w: 8.6, h: 1.0,
  fontSize: 48, fontFace: FONT_TITLE, color: WHITE, bold: true, align: "center", margin: 0,
});
s10.addShape(pres.shapes.RECTANGLE, {
  x: 4.2, y: 3.0, w: 1.6, h: 0.05, fill: { color: SAGE },
});
s10.addText("http://localhost:8501", {
  x: 2, y: 3.4, w: 6, h: 0.5,
  fontSize: 20, fontFace: "Consolas", color: SAGE, align: "center", margin: 0,
});
s10.addText("Project Sentinel  |  Treasury Operations Automation", {
  x: 2, y: 4.2, w: 6, h: 0.4,
  fontSize: 14, fontFace: FONT_BODY, color: TEXT_WHITE, align: "center", italic: true, margin: 0,
});
s10.addText("github.com/SEFICO-23/Sentinel", {
  x: 2, y: 4.8, w: 6, h: 0.3,
  fontSize: 12, fontFace: FONT_BODY, color: TEXT_WHITE, align: "center", margin: 0,
});

// Save
const outPath = path.join(__dirname, "Project_Sentinel_Presentation.pptx");
pres.writeFile({ fileName: outPath }).then(() => {
  console.log("Presentation saved to: " + outPath);
});
