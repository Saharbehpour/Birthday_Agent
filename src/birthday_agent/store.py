from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .models import Contact


REQUIRED_COLUMNS = {"name", "birthday", "email"}


class CsvContactStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> list[Contact]:
        if not self.path.exists():
            raise FileNotFoundError(f"Contacts file not found: {self.path}")

        with self.path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - columns
            if missing:
                raise ValueError(
                    "Contacts CSV is missing required columns: "
                    + ", ".join(sorted(missing))
                )

            contacts: list[Contact] = []
            for row_number, row in enumerate(reader, start=2):
                birthday = (row.get("birthday") or "").strip()
                try:
                    month, day = (int(part) for part in birthday.split("-"))
                    date(2000, month, day)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"Invalid birthday '{birthday}' on row {row_number}; use MM-DD."
                    ) from None

                contacts.append(
                    Contact(
                        name=(row.get("name") or "").strip(),
                        birthday=birthday,
                        email=(row.get("email") or "").strip(),
                        relationship=(row.get("relationship") or "").strip(),
                        context=(row.get("context") or "").strip(),
                        tone=(row.get("tone") or "warm").strip(),
                    )
                )
            return contacts

    def birthdays_on(self, day: date) -> list[Contact]:
        return [contact for contact in self.load() if contact.has_birthday_on(day)]


class SentLog:
    """Small CSV log that prevents duplicate sends on the same birthday."""

    HEADERS = ["date", "email", "name", "status"]

    def __init__(self, path: Path):
        self.path = Path(path)

    def was_sent(self, day: date, email: str) -> bool:
        if not self.path.exists():
            return False
        with self.path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if (
                    row.get("date") == day.isoformat()
                    and row.get("email", "").lower() == email.lower()
                    and row.get("status") == "sent"
                ):
                    return True
        return False

    def record_sent(self, day: date, contact: Contact) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        exists = self.path.exists()
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.HEADERS)
            if not exists:
                writer.writeheader()
            writer.writerow(
                {
                    "date": day.isoformat(),
                    "email": contact.email,
                    "name": contact.name,
                    "status": "sent",
                }
            )

