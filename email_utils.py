# -*- coding: utf-8 -*-
"""
Standalone replacement for the AppDaemon `commonfunctions.sendEmail` helper.
Reads SMTP credentials from environment variables so nothing is hardcoded
in source control:

    SMTP_HOST       e.g. smtp.gmail.com
    SMTP_PORT       e.g. 587
    SMTP_USER       login/username
    SMTP_PASSWORD   login password / app password
    SMTP_FROM       "From" address (defaults to SMTP_USER)
    SMTP_USE_TLS    "true"/"false" (default "true")
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("fkf.email")


def send_email(subject: str, html_body: str, recipients: list[str]) -> None:
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM", user)
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"

    if not host or not user or not password:
        logger.error(
            "SMTP not configured (need SMTP_HOST, SMTP_USER, SMTP_PASSWORD). "
            "Skipping email send for subject=%r",
            subject,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "Szelektív hulladék" #sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            if use_tls:
                server.starttls()
            server.login(user, password)
            server.sendmail(sender, recipients, msg.as_string())
        logger.info("Email sent: %r to %s", subject, recipients)
    except Exception:
        logger.exception("Failed to send email: %r to %s", subject, recipients)
