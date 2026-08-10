from __future__ import annotations

from collections.abc import Callable
from datetime import date

from .composer import MessageComposer
from .models import Contact, RunResult
from .senders import MessageSender, PreviewSender
from .store import CsvContactStore, SentLog


Approver = Callable[[Contact, str], bool]


class BirthdayAgent:
    def __init__(
        self,
        contacts: CsvContactStore,
        composer: MessageComposer,
        sent_log: SentLog,
    ):
        self.contacts = contacts
        self.composer = composer
        self.sent_log = sent_log

    def run(
        self,
        day: date,
        mode: str = "preview",
        sender: MessageSender | None = None,
        approver: Approver | None = None,
    ) -> list[RunResult]:
        if mode not in {"preview", "approve", "auto"}:
            raise ValueError("mode must be preview, approve, or auto")

        matches = self.contacts.birthdays_on(day)
        results: list[RunResult] = []

        for contact in matches:
            if self.sent_log.was_sent(day, contact.email):
                results.append(RunResult(contact.name, contact.email, "already-sent"))
                continue

            message = self.composer.compose(contact)

            if mode == "preview":
                PreviewSender().send(contact, message)
                results.append(RunResult(contact.name, contact.email, "previewed", message))
                continue

            if sender is None:
                raise RuntimeError("A sender is required for approve or auto mode.")

            if mode == "approve":
                if approver is None:
                    raise RuntimeError("An approver is required in approve mode.")
                if not approver(contact, message):
                    results.append(RunResult(contact.name, contact.email, "not-approved", message))
                    continue

            sender.send(contact, message)
            self.sent_log.record_sent(day, contact)
            results.append(RunResult(contact.name, contact.email, "sent", message))

        return results

