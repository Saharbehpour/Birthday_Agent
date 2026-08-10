from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Contact:
    name: str
    birthday: str
    email: str
    relationship: str = ""
    context: str = ""
    tone: str = "warm"

    def has_birthday_on(self, day: date) -> bool:
        return self.birthday.strip() == day.strftime("%m-%d")


@dataclass(frozen=True)
class RunResult:
    name: str
    email: str
    status: str
    message: str = ""

