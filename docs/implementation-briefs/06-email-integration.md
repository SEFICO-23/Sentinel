# Brief 06: Email Integration (SMTP)

## Priority: WAVE 2 | Parallel-Safe | Depends on Wave 1 merge

## Context

After approving a capital call, the system generates an HTML email template but only offers it as a download. Treasury teams want to send the confirmation email directly from the app.

## What to Build

1. SMTP configuration in the sidebar (server, port, username, password)
2. A "Send Email" button that appears after approval alongside the download button
3. Recipient email input field
4. Delivery confirmation with error handling

## Implementation

### 1. Create `email_sender.py`

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_confirmation_email(
    smtp_server: str, smtp_port: int, smtp_user: str, smtp_password: str,
    to_email: str, subject: str, html_body: str, from_email: str = None
) -> tuple[bool, str]:
    """Send an HTML email. Returns (success, message)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email or smtp_user
        msg["To"] = to_email
        
        # Plain text fallback
        plain_text = html_body.replace("<br>", "\n").replace("&nbsp;", " ")
        plain_text = re.sub(r"<[^>]+>", "", plain_text)
        
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        
        return True, f"Email sent to {to_email}"
    except Exception as e:
        return False, f"Failed to send: {str(e)}"
```

### 2. SMTP settings in sidebar

Add an expandable SMTP configuration section in the sidebar:
```python
with st.expander("Email Settings"):
    smtp_server = st.text_input("SMTP Server", value="smtp.office365.com")
    smtp_port = st.number_input("Port", value=587)
    smtp_user = st.text_input("Email", placeholder="treasury@company.com")
    smtp_pass = st.text_input("Password", type="password")
```

Store in session state so they persist across reruns.

### 3. Send button after approval

After the email template is generated (post-approval), add:
```python
recipient = st.text_input("Recipient Email", placeholder="gp-ops@fundmanager.com")
if st.button("Send Email", disabled=not (recipient and smtp_configured)):
    success, message = send_confirmation_email(...)
    if success:
        st.success(message)
    else:
        st.error(message)
```

### 4. Store email status in database

Add `email_sent` (INTEGER, default 0) and `email_recipient` (TEXT) columns to `processed_calls` table. Update after successful send.

## Acceptance Criteria

- [ ] SMTP settings configurable in sidebar
- [ ] "Send Email" button appears after approval
- [ ] Recipient email is validated (basic format check)
- [ ] Success/failure feedback shown to user
- [ ] Email sent status tracked in database
- [ ] Graceful handling of SMTP errors (timeout, auth failure, etc.)
- [ ] Download button still works as fallback
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Create

- `email_sender.py`

## Files to Modify

- `app.py` (sidebar + post-approval section)
- `database.py` (add email tracking columns)

## Do NOT

- Make email sending mandatory (keep download as default)
- Store SMTP passwords in the database (session state only)
