"""
alerter.py — SMTP Email Alert Module
======================================
Sends structured HTML email alerts when a High-severity trigger is detected.
Configure via environment variables (see .env.example).
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logger = logging.getLogger(__name__)


def _build_html(alert) -> str:
    severity_color = {
        "High": "#ef4444",
        "Medium": "#f59e0b",
        "Low": "#10b981",
    }.get(alert.severity, "#6366f1")

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #09090b; color: #e4e4e7; margin: 0; padding: 0; }}
    .wrapper {{ max-width: 600px; margin: 0 auto; padding: 32px 24px; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 999px;
              font-size: 12px; font-weight: 700; text-transform: uppercase;
              letter-spacing: 0.08em; background: {severity_color}20;
              color: {severity_color}; border: 1px solid {severity_color}40; }}
    .card {{ background: #18181b; border: 1px solid #27272a; border-radius: 16px;
             padding: 24px; margin: 20px 0; }}
    .label {{ font-size: 10px; font-weight: 600; text-transform: uppercase;
              letter-spacing: 0.12em; color: #71717a; margin-bottom: 4px; }}
    .value {{ font-size: 15px; color: #f4f4f5; font-weight: 500; line-height: 1.5; }}
    .score {{ font-size: 36px; font-weight: 900;
              background: linear-gradient(135deg, #6366f1, #a855f7);
              -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .action {{ background: #6366f120; border: 1px solid #6366f140; border-radius: 12px;
               padding: 16px; margin-top: 16px; }}
    .footer {{ color: #52525b; font-size: 12px; text-align: center; margin-top: 32px; }}
    h1 {{ font-size: 24px; font-weight: 800; color: #f4f4f5; margin: 16px 0 8px; }}
    p {{ color: #a1a1aa; line-height: 1.6; margin: 0; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <p class="label">DataVex Strategic Alert</p>
    <h1>🚨 {alert.event_type} Detected</h1>
    <span class="badge">{alert.severity} Severity</span>

    <div class="card">
      <div class="label">Company</div>
      <div class="value" style="font-size:18px;font-weight:700;">{alert.company_name}</div>
      <div style="margin-top:4px;"><span style="color:#71717a;font-size:13px;">{alert.domain}</span></div>
    </div>

    <div class="card">
      <div class="label">What Happened</div>
      <div class="value">{alert.event_summary}</div>

      <div style="display:flex;gap:24px;margin-top:20px;">
        <div>
          <div class="label">Impact Score</div>
          <div class="score">{int(alert.impact_score)}</div>
        </div>
        <div>
          <div class="label">Confidence</div>
          <div class="value">{alert.confidence}</div>
        </div>
        <div>
          <div class="label">Detected</div>
          <div class="value" style="font-size:13px;">{alert.detected_at.strftime('%d %b %Y, %H:%M') if alert.detected_at else 'Now'} UTC</div>
        </div>
      </div>
    </div>

    <div class="action">
      <div class="label" style="color:#818cf8;">Suggested Action</div>
      <p style="color:#c7d2fe;margin-top:6px;">{alert.suggested_action}</p>
    </div>

    <div class="footer">
      <p>DataVex Strategic Enterprise Intelligence Engine</p>
      <p>Open your dashboard at <a href="http://localhost:5173" style="color:#6366f1;">http://localhost:5173</a></p>
    </div>
  </div>
</body>
</html>
"""


def send_alert_email(alert) -> bool:
    """
    Send a structured HTML email alert via SMTP.
    Returns True on success, False on failure/not-configured.

    Required env vars:
        SMTP_HOST     (e.g. smtp.gmail.com)
        SMTP_PORT     (default: 587)
        SMTP_USER     (your email)
        SMTP_PASS     (app password or API key)
        ALERT_TO      (recipient email)
    """
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    alert_to  = os.environ.get("ALERT_TO")

    if not all([smtp_host, smtp_user, smtp_pass, alert_to]):
        logger.info("[alerter] SMTP not configured — skipping email for %s", alert.company_name)
        return False

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    subject = f"🚨 Strategic Alert — {alert.company_name} | {alert.event_type} Detected"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = smtp_user
    msg["To"]      = alert_to

    # Plain text fallback
    plain = (
        f"DataVex Strategic Alert\n\n"
        f"Company: {alert.company_name} ({alert.domain})\n"
        f"Event: {alert.event_type} [{alert.severity}]\n"
        f"Summary: {alert.event_summary}\n"
        f"Impact Score: {int(alert.impact_score)}\n"
        f"Confidence: {alert.confidence}\n\n"
        f"Suggested Action:\n{alert.suggested_action}\n\n"
        f"View dashboard: http://localhost:5173\n"
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(_build_html(alert), "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, alert_to, msg.as_string())
        logger.info("[alerter] email sent → %s for %s", alert_to, alert.company_name)
        return True
    except Exception as e:
        logger.error("[alerter] SMTP error: %s", e)
        return False
