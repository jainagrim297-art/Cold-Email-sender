"""
Sent Emails Database
====================
SQLite-backed store that tracks every email address ever contacted.
Used to prevent duplicate outreach across multiple agent runs.

Table: sent_emails
  - id          : auto-increment primary key
  - email       : the recipient address
  - company     : the company name
  - sent_at     : UTC timestamp of when the pitch was sent
  - category    : AI classification that triggered the send
"""

import os
import sqlite3
from datetime import datetime, timezone
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "outreach.db")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates the sent_emails table if it doesn't exist yet."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_emails (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                email    TEXT    NOT NULL,
                company  TEXT    NOT NULL,
                sent_at  TEXT    NOT NULL,
                category TEXT    NOT NULL,
                domain   TEXT
            )
        """)
        # Migration: Add domain column if missing from older versions
        try:
            conn.execute("ALTER TABLE sent_emails ADD COLUMN domain TEXT")
        except sqlite3.OperationalError:
            pass # already exists

        conn.execute("CREATE INDEX IF NOT EXISTS idx_email ON sent_emails(email)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_domain ON sent_emails(domain)")
        conn.commit()


def already_contacted_domain(domain: str) -> bool:
    """Returns True if any email from this domain has already been pitched."""
    if not domain:
        return False
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM sent_emails WHERE domain = ? LIMIT 1", (domain.lower(),)
        ).fetchone()
        return row is not None


def already_contacted(email: str) -> bool:
    """Returns True if this email address has already been pitched."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM sent_emails WHERE email = ? LIMIT 1", (email.lower(),)
        ).fetchone()
        return row is not None


def record_sent(email: str, company: str, category: str, domain: str = None):
    """Records a successful send so it's never repeated."""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sent_emails (email, company, sent_at, category, domain) VALUES (?, ?, ?, ?, ?)",
            (email.lower(), company, datetime.now(timezone.utc).isoformat(), category, domain.lower() if domain else None),
        )
        conn.commit()


def show_all_sent() -> list[dict]:
    """Returns all sent emails as a list of dicts (useful for the CLI viewer)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT email, company, sent_at, category FROM sent_emails ORDER BY sent_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def clear_db():
    """Wipes all records (use carefully — for testing only)."""
    with _connect() as conn:
        conn.execute("DELETE FROM sent_emails")
        conn.commit()
    print("🗑️  Database cleared.")


# ─────────────────────────────────────────────────────────────────────────────
# CLI: python src/processor/sent_db.py  → prints history
#      python src/processor/sent_db.py --clear  → wipes all records
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    init_db()

    if "--clear" in sys.argv:
        confirm = input("⚠️  Are you sure you want to wipe the outreach history? (yes/no): ")
        if confirm.strip().lower() == "yes":
            clear_db()
        else:
            print("Cancelled.")
        sys.exit(0)

    rows = show_all_sent()
    if not rows:
        print("📭 No emails sent yet.")
    else:
        print(f"\n{'─'*70}")
        print(f"  {'EMAIL':<35} {'COMPANY':<25} SENT AT (UTC)")
        print(f"{'─'*70}")
        for r in rows:
            ts = r["sent_at"][:19].replace("T", " ")
            print(f"  {r['email']:<35} {r['company'][:24]:<25} {ts}")
        print(f"{'─'*70}")
        print(f"  Total: {len(rows)} pitch(es) sent.\n")
