"""Seed the database with fake tickets for local testing.

Usage (from the backend folder):
    uv run python -m scripts.seed --count 5000
"""

import argparse
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import insert

from app.db.session import SessionLocal
from app.models import Priority, Ticket

TAGS = [
    "billing",
    "login",
    "bug",
    "network",
    "email",
    "hardware",
    "vpn",
    "security",
    "performance",
    "ui",
]
SUBJECTS = [
    "Cannot log in",
    "VPN keeps disconnecting",
    "Invoice is incorrect",
    "Email not syncing",
    "Laptop overheating",
    "Dashboard is slow",
    "Password reset link expired",
    "Suspicious login alert",
    "Printer offline",
    "2FA code not received",
]
AGENTS = ["alice@support.io", "bob@support.io", "carol@support.io"]


def build_rows(count: int) -> list[dict]:
    now = datetime.now(UTC)
    rows = []
    for i in range(count):
        created_at = now - timedelta(minutes=i * 7 + random.randint(0, 6))
        is_assigned = random.random() < 0.2  # ~20% already assigned
        rows.append(
            {
                "title": f"{random.choice(SUBJECTS)} #{i + 1}",
                "description": "Auto-generated ticket for local testing.",
                "priority": random.choice(list(Priority)),
                "tags": random.sample(TAGS, k=random.randint(0, 3)),
                "assigned_to": random.choice(AGENTS) if is_assigned else None,
                "assigned_at": created_at + timedelta(hours=1) if is_assigned else None,
                "created_at": created_at,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed fake tickets.")
    parser.add_argument("--count", type=int, default=5000)
    args = parser.parse_args()

    with SessionLocal() as db:
        db.execute(insert(Ticket), build_rows(args.count))  # one bulk insert
        db.commit()
    print(f"Inserted {args.count} tickets.")


if __name__ == "__main__":
    main()
