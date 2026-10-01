"""
Synapse Knowledge Base - SQLite Database Manager with Security & Hash-Chaining
"""

import os
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.seed_data import INITIAL_SOURCES, INITIAL_DOCUMENTS, INITIAL_FINDINGS

DB_PATH = Path(os.getenv("SYNAPSE_DB_PATH", str(Path(__file__).parent / "synapse.db")))

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db(reset: bool = False):
    from backend.security import hash_password

    conn = get_db_connection()
    with conn:
        if reset:
            conn.execute("DROP TABLE IF EXISTS users")
            conn.execute("DROP TABLE IF EXISTS history_events")
            conn.execute("DROP TABLE IF EXISTS findings")
            conn.execute("DROP TABLE IF EXISTS documents")
            conn.execute("DROP TABLE IF EXISTS sources")
            conn.execute("DROP TABLE IF EXISTS audit_runs")
            conn.execute("DROP TABLE IF EXISTS policies")

        # 1. Users table (RBAC & Authentication)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        # 2. Sources table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                documents_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'connected',
                last_synced TEXT DEFAULT 'Just now'
            );
        """)

        # 3. Documents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                owner TEXT NOT NULL,
                path TEXT NOT NULL,
                updated TEXT NOT NULL,
                status TEXT DEFAULT 'healthy',
                text TEXT NOT NULL
            );
        """)

        # 4. Findings table (anomalies / claims awaiting review)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                path TEXT NOT NULL,
                type TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                severity TEXT NOT NULL,
                owner TEXT NOT NULL,
                updated TEXT NOT NULL,
                current_claim TEXT NOT NULL,
                proposed TEXT NOT NULL,
                evidence TEXT NOT NULL,
                evidence_text TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                quarantine INTEGER DEFAULT 0,
                evidence_source TEXT,
                applied_text TEXT
            );
        """)

        # 5. Cryptographic Tamper-Evident History Events table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history_events (
                id TEXT PRIMARY KEY,
                issue_id TEXT NOT NULL,
                title TEXT NOT NULL,
                action TEXT NOT NULL,
                before_text TEXT,
                after_text TEXT,
                note TEXT,
                evidence TEXT,
                actor TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                rollback_of TEXT,
                prev_hash TEXT NOT NULL DEFAULT '0000000000000000000000000000000000000000000000000000000000000000',
                event_hash TEXT NOT NULL DEFAULT ''
            );
        """)

        # 6. Audit Runs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_runs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                scope TEXT NOT NULL,
                documents_checked INTEGER NOT NULL,
                findings_count INTEGER NOT NULL,
                applied_count INTEGER NOT NULL,
                status TEXT DEFAULT 'Completed'
            );
        """)

        # 7. Policies table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                threshold INTEGER NOT NULL DEFAULT 95,
                auto_heal INTEGER NOT NULL DEFAULT 0,
                last_audit TEXT NOT NULL DEFAULT '12 minutes ago'
            );
        """)

        # Seed pre-configured users if empty
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            seed_users = [
                ("USR-01", "alex.sterling@synapse.internal", "SynapseAdmin2026!", "Admin", "Alex Sterling"),
                ("USR-02", "jordan.lee@synapse.internal", "Reviewer2026!", "Reviewer", "Jordan Lee"),
                ("USR-03", "morgan.vance@synapse.internal", "Auditor2026!", "Auditor", "Morgan Vance")
            ]
            for uid, email, raw_pwd, role, name in seed_users:
                pwd_hash, salt = hash_password(raw_pwd)
                conn.execute(
                    "INSERT INTO users (id, email, hashed_password, salt, role, name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (uid, email, pwd_hash, salt, role, name, "2026-09-30T12:00:00Z")
                )

        # Seed policies if empty
        row = conn.execute("SELECT * FROM policies WHERE id = 1").fetchone()
        if not row:
            conn.execute("INSERT INTO policies (id, threshold, auto_heal, last_audit) VALUES (1, 95, 0, '12 minutes ago')")

        # Seed sources if empty
        if conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 0:
            for s in INITIAL_SOURCES:
                conn.execute(
                    "INSERT INTO sources (id, name, type, documents_count, status, last_synced) VALUES (?, ?, ?, ?, ?, ?)",
                    (s["id"], s["name"], s["type"], s["documents_count"], s["status"], s["last_synced"])
                )

        # Seed documents if empty
        if conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0:
            for d in INITIAL_DOCUMENTS:
                conn.execute(
                    "INSERT INTO documents (id, title, source, owner, path, updated, status, text) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (d["id"], d["title"], d["source"], d["owner"], d["path"], d["updated"], d["status"], d["text"])
                )

        # Seed findings if empty
        if conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0] == 0:
            for f in INITIAL_FINDINGS:
                conn.execute(
                    """INSERT INTO findings (
                        id, title, source, path, type, confidence, severity, owner, updated,
                        current_claim, proposed, evidence, evidence_text, reason, status,
                        quarantine, evidence_source, applied_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f["id"], f["title"], f["source"], f["path"], f["type"], f["confidence"],
                        f["severity"], f["owner"], f["updated"], f["current"], f["proposed"],
                        f["evidence"], f["evidence_text"], f["reason"], f["status"],
                        1 if f.get("quarantine") else 0, f.get("evidence_source"), None
                    )
                )

        # Seed initial audit runs if empty
        if conn.execute("SELECT COUNT(*) FROM audit_runs").fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO audit_runs (id, timestamp, scope, documents_checked, findings_count, applied_count, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("AUD-0294", "Just now", "All connected sources", 2846, 6, 0, "Completed")
            )
            conn.execute(
                "INSERT INTO audit_runs (id, timestamp, scope, documents_checked, findings_count, applied_count, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("AUD-0293", "Sep 29, 16:00", "Changed documents", 128, 12, 1, "Completed")
            )

    conn.close()

# Auto-initialize database on import
init_db(reset=False)
