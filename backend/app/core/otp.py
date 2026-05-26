"""
OTP storage and verification.

Current backend: in-memory dict.
WARNING: This does NOT work across multiple workers or server restarts.
         Swap OTPStore._backend for a Redis client before going to production.

To migrate:
  1. Implement RedisOTPStore with the same .save() / .verify() interface
  2. Replace the instantiation at the bottom of this file
  3. No other file needs to change
"""
from datetime import datetime, timedelta, timezone
from abc import ABC, abstractmethod

OTP_TTL_MINUTES = 10


class BaseOTPStore(ABC):
    @abstractmethod
    def save(self, email: str, otp: str) -> None: ...

    @abstractmethod
    def verify(self, email: str, otp: str) -> bool: ...


class InMemoryOTPStore(BaseOTPStore):
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def save(self, email: str, otp: str) -> None:
        self._store[email] = {
            "otp": otp,
            "expiry": datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES),
        }

    def verify(self, email: str, otp: str) -> bool:
        record = self._store.get(email)
        if not record:
            return False
        if record["expiry"] < datetime.now(timezone.utc):
            self._store.pop(email, None)
            return False
        if record["otp"] != otp:
            return False
        self._store.pop(email, None)
        return True


# Single instance — import this everywhere
otp_store = InMemoryOTPStore()