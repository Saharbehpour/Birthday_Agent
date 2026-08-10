import tempfile
import unittest
from datetime import date
from pathlib import Path

from birthday_agent.store import CsvContactStore


class CsvContactStoreTests(unittest.TestCase):
    def test_finds_birthdays_by_month_and_day(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contacts.csv"
            path.write_text(
                "name,birthday,email,relationship,context,tone\n"
                "Maya,08-07,maya@example.com,friend,,warm\n"
                "David,12-14,david@example.com,friend,,warm\n",
                encoding="utf-8",
            )
            store = CsvContactStore(path)
            matches = store.birthdays_on(date(2026, 8, 7))
            self.assertEqual([contact.name for contact in matches], ["Maya"])

    def test_rejects_bad_birthday_format(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contacts.csv"
            path.write_text(
                "name,birthday,email\nMaya,August 7,maya@example.com\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                CsvContactStore(path).load()


if __name__ == "__main__":
    unittest.main()

