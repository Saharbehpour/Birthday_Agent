import tempfile
import unittest
from datetime import date
from pathlib import Path

from birthday_agent.agent import BirthdayAgent
from birthday_agent.store import CsvContactStore, SentLog


class FakeComposer:
    def compose(self, contact):
        return f"Happy birthday, {contact.name}!"


class FakeSender:
    def __init__(self):
        self.sent = []

    def send(self, contact, message):
        self.sent.append((contact.email, message))


class BirthdayAgentTests(unittest.TestCase):
    def make_agent(self, directory: str):
        root = Path(directory)
        contacts_path = root / "contacts.csv"
        contacts_path.write_text(
            "name,birthday,email,relationship,context,tone\n"
            "Maya,08-07,maya@example.com,friend,,warm\n",
            encoding="utf-8",
        )
        return BirthdayAgent(
            contacts=CsvContactStore(contacts_path),
            composer=FakeComposer(),
            sent_log=SentLog(root / "sent_log.csv"),
        )

    def test_preview_does_not_record_send(self):
        with tempfile.TemporaryDirectory() as directory:
            agent = self.make_agent(directory)
            results = agent.run(date(2026, 8, 7), mode="preview")
            self.assertEqual(results[0].status, "previewed")
            self.assertFalse(agent.sent_log.path.exists())

    def test_auto_sends_once(self):
        with tempfile.TemporaryDirectory() as directory:
            agent = self.make_agent(directory)
            sender = FakeSender()

            first = agent.run(date(2026, 8, 7), mode="auto", sender=sender)
            second = agent.run(date(2026, 8, 7), mode="auto", sender=sender)

            self.assertEqual(first[0].status, "sent")
            self.assertEqual(second[0].status, "already-sent")
            self.assertEqual(len(sender.sent), 1)

    def test_approval_can_block_send(self):
        with tempfile.TemporaryDirectory() as directory:
            agent = self.make_agent(directory)
            sender = FakeSender()
            results = agent.run(
                date(2026, 8, 7),
                mode="approve",
                sender=sender,
                approver=lambda contact, message: False,
            )
            self.assertEqual(results[0].status, "not-approved")
            self.assertEqual(sender.sent, [])


if __name__ == "__main__":
    unittest.main()

