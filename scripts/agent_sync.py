#!/usr/bin/env python3
"""
🤖 AGENT SYNC TOOL v2.2 (Unified Semantic Edition)
-------------------------------------------------
Consolidated and simplified command set based on Copilot's architectural feedback.
Native support for Study, Task, and Broadcast workflows.
Maintains Sisyphus's advanced task management (task_queue, subscriptions).
"""
import sqlite3
import os
import sys
import argparse
from datetime import datetime

DB_PATH = os.path.join(os.getcwd(), ".agent/agent_hub.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT,
            task TEXT,
            status TEXT DEFAULT 'idle',
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS file_locks (
            file_path TEXT PRIMARY KEY,
            agent_id TEXT,
            lock_type TEXT DEFAULT 'write',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS research_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            topic TEXT,
            content TEXT,
            note_type TEXT DEFAULT 'note', -- 'note', 'study', 'conclusion'
            is_resolved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS task_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            initiator TEXT,
            task_type TEXT, -- 'research', 'collab', 'fix'
            topic TEXT,
            description TEXT,
            priority TEXT DEFAULT 'normal',
            status TEXT DEFAULT 'pending', -- 'pending', 'active', 'completed'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS task_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            agent_id TEXT,
            role TEXT, -- 'lead', 'reviewer', 'worker', 'observer'
            FOREIGN KEY(task_id) REFERENCES task_queue(id)
        );
        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id TEXT,
            type TEXT,
            payload TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS global_settings (
            key TEXT PRIMARY KEY, value TEXT
        );
    ''')
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('mode', 'isolation')")
    conn.commit()
    conn.close()
    print(f"✅ MACP 2.2 Semantic Kernel Active")

def get_status():
    conn = get_connection(); cursor = conn.cursor()
    print("\n--- 🛰️  Agent Fleet ---")
    for r in cursor.execute("SELECT id, name, status, task FROM agents"):
        print(f"[{r[2].upper()}] {r[1]} ({r[0]}) | Task: {r[3]}")

    print("\n--- 📋 Global Task Queue ---")
    for r in cursor.execute("SELECT id, topic, task_type, priority, status FROM task_queue WHERE status != 'completed'"):
        print(f"  #{r[0]} [{r[2].upper()}] {r[1]} | {r[3]} | {r[4]}")

    print("\n--- 📚 Active Studies ---")
    for r in cursor.execute("SELECT topic, agent_id FROM research_log WHERE note_type='study' AND is_resolved=0"):
        print(f"  🔬 {r[0]} (by {r[1]})")

    print("\n--- 📢 Live Broadcasts ---")
    for r in cursor.execute("SELECT sender_id, type, payload FROM broadcasts WHERE active=1 ORDER BY created_at DESC LIMIT 3"):
        print(f"📣 {r[0]} [{r[1].upper()}]: {r[2]}")

    print("\n--- 🔒 File Locks ---")
    for r in cursor.execute("SELECT file_path, agent_id, lock_type FROM file_locks ORDER BY timestamp DESC LIMIT 20"):
        print(f"  {r[0]} -> {r[1]} ({r[2]})")

    cursor.execute("SELECT value FROM global_settings WHERE key='mode'")
    mode = cursor.fetchone()[0]
    print(f"\n🌍 Project Mode: {mode.upper()}")
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    # Base commands
    subparsers.add_parser("init")
    subparsers.add_parser("status")
    subparsers.add_parser("check")
    subparsers.add_parser("ping")

    reg = subparsers.add_parser("register")
    reg.add_argument("id"); reg.add_argument("name"); reg.add_argument("task")

    # Lock commands
    lock = subparsers.add_parser("lock")
    lock.add_argument("id"); lock.add_argument("path")
    unlock = subparsers.add_parser("unlock")
    unlock.add_argument("id"); unlock.add_argument("path")

    # Research & Note commands
    note = subparsers.add_parser("note")
    note.add_argument("id"); note.add_argument("topic"); note.add_argument("content")
    note.add_argument("--type", default="note")

    # Semantic Workflows (The Unified Commands)
    study = subparsers.add_parser("study")
    study.add_argument("id"); study.add_argument("topic"); study.add_argument("--desc", default=None)

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("id"); resolve.add_argument("topic"); resolve.add_argument("conclusion")

    # Task Management (The Advanced Commands)
    assign = subparsers.add_parser("assign")
    assign.add_argument("id"); assign.add_argument("target"); assign.add_argument("topic")
    assign.add_argument("--role", default="worker"); assign.add_argument("--priority", default="normal")

    bc = subparsers.add_parser("broadcast")
    bc.add_argument("id"); bc.add_argument("type"); bc.add_argument("payload")

    args = parser.parse_args()
    if args.command == "init": init_db()
    elif args.command == "status" or args.command == "check" or args.command == "ping": get_status()
    elif args.command == "register":
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO agents (id, name, task, status, last_seen) VALUES (?, ?, ?, 'active', CURRENT_TIMESTAMP)", (args.id, args.name, args.task))
        conn.commit(); conn.close()
        print(f"🤖 Registered: {args.id}")
    elif args.command == "lock":
        conn = get_connection(); cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO file_locks (file_path, agent_id) VALUES (?, ?)", (args.path, args.id))
            conn.commit(); print(f"🔒 Locked {args.path}")
        except: print(f"❌ Lock conflict on {args.path}"); sys.exit(1)
        finally: conn.close()
    elif args.command == "unlock":
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute("DELETE FROM file_locks WHERE file_path=? AND agent_id=?", (args.path, args.id))
        conn.commit(); conn.close(); print(f"🔓 Unlocked {args.path}")
    elif args.command == "study":
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute("INSERT INTO research_log (agent_id, topic, content, note_type) VALUES (?, ?, ?, 'study')", (args.id, args.topic, args.desc or "Study started"))
        cursor.execute("UPDATE agents SET status = 'researching'")
        cursor.execute("INSERT INTO broadcasts (sender_id, type, payload) VALUES (?, 'research', ?)", (args.id, f"NEW STUDY: {args.topic}"))
        cursor.execute("UPDATE global_settings SET value = ? WHERE key = 'mode'", (f"RESEARCH: {args.topic}",))
        conn.commit(); conn.close()
        print(f"🔬 Study '{args.topic}' initiated.")
    elif args.command == "resolve":
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute("UPDATE research_log SET is_resolved = 1 WHERE topic = ?", (args.topic,))
        cursor.execute("INSERT INTO research_log (agent_id, topic, content, note_type, is_resolved) VALUES (?, ?, ?, 'conclusion', 1)", (args.id, args.topic, args.conclusion))
        cursor.execute("UPDATE global_settings SET value = 'isolation' WHERE key = 'mode'")
        cursor.execute("UPDATE agents SET status = 'active' WHERE status = 'researching'")
        conn.commit(); conn.close()
        print(f"✅ Study '{args.topic}' resolved.")
    elif args.command == "assign":
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO task_queue (initiator, task_type, topic, description, priority, status) VALUES (?, 'task', ?, ?, ?, 'pending')",
            (args.id, args.topic, f"Assigned to {args.target}: {args.topic}", args.priority),
        )
        task_id = cursor.lastrowid
        cursor.execute("INSERT INTO task_subscriptions (task_id, agent_id, role) VALUES (?, ?, ?)", (task_id, args.target, args.role))
        conn.commit(); conn.close()
        print(f"📋 Task #{task_id} assigned to {args.target}")
    elif args.command == "broadcast":
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute("UPDATE broadcasts SET active = 0 WHERE type = ?", (args.type,))
        cursor.execute("INSERT INTO broadcasts (sender_id, type, payload) VALUES (?, ?, ?)", (args.id, args.type, args.payload))
        conn.commit(); conn.close()
        print(f"📡 Broadcast: {args.payload}")
    elif args.command == "note":
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute("INSERT INTO research_log (agent_id, topic, content, note_type) VALUES (?, ?, ?, ?)", (args.id, args.topic, args.content, args.type))
        conn.commit(); conn.close()
        print(f"📝 Note added.")
