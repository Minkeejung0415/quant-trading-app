"""Simple reporting and alert stubs for daily operations."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path


def write_daily_report(path: str, lines: list[str]) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def send_email_alert(subject: str, body: str, smtp_host: str, smtp_port: int, username: str, password: str, to_email: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
        smtp.login(username, password)
        smtp.send_message(msg)
