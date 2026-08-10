from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from .agent import BirthdayAgent
from .composer import OpenAIComposer, TemplateComposer
from .senders import SmtpSender
from .store import CsvContactStore, SentLog


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path) -> None:
    """Tiny .env loader so the MVP needs only the OpenAI package."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Birthday Agent MVP")
    parser.add_argument(
        "--date",
        help="Date to run as YYYY-MM-DD. Defaults to today.",
    )
    parser.add_argument(
        "--contacts",
        type=Path,
        default=PROJECT_ROOT / "data" / "contacts.csv",
        help="Path to the private contacts CSV.",
    )
    parser.add_argument(
        "--mode",
        choices=["preview", "approve", "auto"],
        default="preview",
        help="preview is safe default; approve asks before sending; auto sends without a prompt.",
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Use a fixed template instead of OpenAI; useful for testing the workflow.",
    )
    return parser.parse_args()


def interactive_approver(contact, message: str) -> bool:
    print(f"\nDraft for {contact.name} <{contact.email}>:\n{message}\n")
    answer = input("Send this message? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    args = parse_args()
    run_date = date.fromisoformat(args.date) if args.date else date.today()

    contacts_path = args.contacts
    if contacts_path == PROJECT_ROOT / "data" / "contacts.csv" and not contacts_path.exists():
        contacts_path = PROJECT_ROOT / "data" / "contacts.example.csv"
        print("Using sample contacts because data/contacts.csv does not exist yet.")

    composer = (
        TemplateComposer()
        if args.template
        else OpenAIComposer(PROJECT_ROOT / "prompts" / "birthday_message.txt")
    )

    agent = BirthdayAgent(
        contacts=CsvContactStore(contacts_path),
        composer=composer,
        sent_log=SentLog(PROJECT_ROOT / "data" / "sent_log.csv"),
    )

    sender = None
    approver = None
    if args.mode == "approve":
        sender = SmtpSender()
        approver = interactive_approver
    elif args.mode == "auto":
        if os.getenv("AUTO_SEND_ENABLED", "false").lower() != "true":
            raise RuntimeError(
                "Auto-send is locked. Set AUTO_SEND_ENABLED=true only after preview testing."
            )
        sender = SmtpSender()

    results = agent.run(
        day=run_date,
        mode=args.mode,
        sender=sender,
        approver=approver,
    )

    if not results:
        print(f"No birthdays found for {run_date.isoformat()}.")
    else:
        for result in results:
            print(f"{result.name}: {result.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

