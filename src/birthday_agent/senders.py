from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Protocol

from .models import Contact


class MessageSender(Protocol):
    def send(self, contact: Contact, message: str) -> None: ...


class PreviewSender:
    def send(self, contact: Contact, message: str) -> None:
        print(f"\n--- Preview for {contact.name} <{contact.email}> ---")
        print(message)
        print("--- End preview ---\n")


class SmtpSender:
    REQUIRED = ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "FROM_ADDRESS"]

    def __init__(self):
        missing = [name for name in self.REQUIRED if not os.getenv(name, "").strip()]
        if missing:
            raise RuntimeError(
                "SMTP delivery is not configured. Missing: " + ", ".join(missing)
            )
        self.host = os.environ["SMTP_HOST"]
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.environ["SMTP_USERNAME"]
        self.password = os.environ["SMTP_PASSWORD"]
        self.from_address = os.environ["FROM_ADDRESS"]

    def send(self, contact: Contact, message: str) -> None:
        if not contact.email:
            raise ValueError(f"No email address configured for {contact.name}.")

        email = EmailMessage()
        email["From"] = self.from_address
        email["To"] = contact.email
        email["Subject"] = f"Happy Birthday, {contact.name}! 🎂"
        email.set_content(message)

        context = ssl.create_default_context()
        with smtplib.SMTP(self.host, self.port, timeout=30) as server:
            server.starttls(context=context)
            server.login(self.username, self.password)
            server.send_message(email)

