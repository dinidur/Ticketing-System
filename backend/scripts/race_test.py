"""Fire many concurrent claims at ONE ticket and check that exactly one wins.

Usage (API must be running):
    uv run python -m scripts.race_test --agents 20
"""

import argparse
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import httpx

BASE_URL = "http://localhost:8000/api/v1"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agents", type=int, default=20)
    args = parser.parse_args()

    # 1. Create a fresh, unassigned ticket
    ticket = httpx.post(
        f"{BASE_URL}/tickets",
        json={"title": "Race test ticket", "description": "Who gets it?", "priority": "critical"},
    ).json()
    ticket_id = ticket["id"]
    print(f"Created ticket #{ticket_id}. Sending {args.agents} claims at the same moment...")

    # 2. A barrier makes all threads fire at (almost) exactly the same time
    barrier = threading.Barrier(args.agents)

    def claim(agent_no: int) -> tuple[str, int]:
        email = f"agent{agent_no}@support.io"
        barrier.wait()
        response = httpx.post(f"{BASE_URL}/tickets/{ticket_id}/assign", json={"email": email})
        return email, response.status_code

    with ThreadPoolExecutor(max_workers=args.agents) as pool:
        results = list(pool.map(claim, range(1, args.agents + 1)))

    # 3. Check the results
    codes = Counter(code for _, code in results)
    winners = [email for email, code in results if code == 200]
    final_owner = httpx.get(f"{BASE_URL}/tickets/{ticket_id}").json()["assigned_to"]

    print(f"Status codes: {dict(codes)}")
    print(f"Winner(s):    {winners}")
    print(f"Owner in DB:  {final_owner}")

    ok = len(winners) == 1 and codes[409] == args.agents - 1 and final_owner == winners[0]
    print("✅ PASS: exactly one agent won" if ok else "❌ FAIL: race condition!")


if __name__ == "__main__":
    main()