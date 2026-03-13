#!/usr/bin/env python3
"""
🤖 AGENT SYNC TOOL v2.0 - MULTI-AGENT COOPERATION PROTOCOL (MACP)
---------------------------------------------------------
Enhanced collaboration commands for seamless multi-agent synergy.

QUICK COMMANDS:
  @research <topic>     - Start a joint research topic
  @join <topic>         - Join an active research topic
  @find <topic> <content> - Post a finding to research topic
  @consensus <topic>    - Generate consensus document
  @assign <agent> <task> - Assign task to specific agent
  @notify <message>     - Broadcast to all agents
  @handover <agent>     - Handover current task
  @poll <question>      - Start a quick poll
  @switch <agent>        - Request switch to specific agent

WORKFLOW: @research -> @find (xN) -> @consensus -> @assign
"""
import sqlite3
import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

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
            current_research TEXT,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS file_locks (
            file_path TEXT PRIMARY KEY,
            agent_id TEXT,
            lock_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(agent_id) REFERENCES agents(id)
        );
        CREATE TABLE IF NOT EXISTS research_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            topic TEXT,
            content TEXT,
            finding_type TEXT DEFAULT 'note',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(agent_id) REFERENCES agents(id)
        );
        CREATE TABLE IF NOT EXISTS research_topics (
            topic TEXT PRIMARY KEY,
            status TEXT DEFAULT 'active',
            initiated_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS agent_research_participation (
            agent_id TEXT,
            topic TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (agent_id, topic)
        );
        CREATE TABLE IF NOT EXISTS task_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            task TEXT,
            assigned_by TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            message TEXT,
            is_broadcast BOOLEAN DEFAULT 0,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            created_by TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS poll_votes (
            poll_id INTEGER,
            agent_id TEXT,
            vote TEXT,
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (poll_id, agent_id)
        );
        CREATE TABLE IF NOT EXISTS global_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    ''')
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('mode', 'isolation')")
    conn.commit()
    conn.close()
    print(f"✅ Agent Hub v2.0 initialized at {DB_PATH}")

# ============ AGENT MANAGEMENT ============

def register_agent(agent_id, name, task, status="idle"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO agents (id, name, task, status, last_seen)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (agent_id, name, task, status))
    conn.commit()
    conn.close()
    print(f"🤖 Agent '{name}' ({agent_id}) registered.")

def update_agent_status(agent_id, status, research_topic=None):
    conn = get_connection()
    cursor = conn.cursor()
    if research_topic:
        cursor.execute('''
            UPDATE agents SET status = ?, current_research = ?, last_seen = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, research_topic, agent_id))
    else:
        cursor.execute('''
            UPDATE agents SET status = ?, last_seen = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, agent_id))
    conn.commit()
    conn.close()

# ============ RESEARCH COLLABORATION ============

def start_research(agent_id, topic):
    """@research - Start a new research topic and notify all agents"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create research topic
    try:
        cursor.execute('''
            INSERT INTO research_topics (topic, status, initiated_by)
            VALUES (?, 'active', ?)
        ''', (topic, agent_id))
    except sqlite3.IntegrityError:
        print(f"⚠️ Research topic '{topic}' already exists")
        conn.close()
        return
    
    # Add initiator as participant
    cursor.execute('''
        INSERT OR IGNORE INTO agent_research_participation (agent_id, topic)
        VALUES (?, ?)
    ''', (agent_id, topic))
    
    # Update agent status
    cursor.execute('''
        UPDATE agents SET status = 'researching', current_research = ?
        WHERE id = ?
    ''', (topic, agent_id))
    
    # Notify all other agents
    cursor.execute("SELECT id FROM agents WHERE id != ?", (agent_id,))
    other_agents = cursor.fetchall()
    for (other_id,) in other_agents:
        cursor.execute('''
            INSERT INTO notifications (agent_id, message, is_broadcast)
            VALUES (?, ?, 0)
        ''', (other_id, f"🔬 New research started: '{topic}' by {agent_id}. Use '@join {topic}' to participate."))
    
    conn.commit()
    conn.close()
    
    print(f"🔬 Research topic '{topic}' started by {agent_id}")
    print(f"📢 Notified {len(other_agents)} other agents")

def join_research(agent_id, topic):
    """@join - Join an active research topic"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if topic exists and is active
    cursor.execute("SELECT status FROM research_topics WHERE topic = ?", (topic,))
    result = cursor.fetchone()
    if not result:
        print(f"❌ Research topic '{topic}' not found")
        conn.close()
        return
    if result[0] != 'active':
        print(f"⚠️ Research topic '{topic}' is {result[0]}")
        conn.close()
        return
    
    # Add participant
    cursor.execute('''
        INSERT OR IGNORE INTO agent_research_participation (agent_id, topic)
        VALUES (?, ?)
    ''', (agent_id, topic))
    
    # Update agent status
    cursor.execute('''
        UPDATE agents SET status = 'researching', current_research = ?
        WHERE id = ?
    ''', (topic, agent_id))
    
    conn.commit()
    conn.close()
    print(f"✅ {agent_id} joined research: '{topic}'")

def post_finding(agent_id, topic, content, finding_type="note"):
    """@find - Post a finding to research topic"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if topic exists
    cursor.execute("SELECT status FROM research_topics WHERE topic = ?", (topic,))
    result = cursor.fetchone()
    if not result:
        print(f"❌ Research topic '{topic}' not found")
        conn.close()
        return
    if result[0] != 'active':
        print(f"⚠️ Research topic '{topic}' is {result[0]}")
    
    # Add finding
    cursor.execute('''
        INSERT INTO research_log (agent_id, topic, content, finding_type)
        VALUES (?, ?, ?, ?)
    ''', (agent_id, topic, content, finding_type))
    
    # Update agent status
    cursor.execute('''
        UPDATE agents SET last_seen = CURRENT_TIMESTAMP WHERE id = ?
    ''', (agent_id,))
    
    conn.commit()
    conn.close()
    print(f"📝 Finding added to '{topic}' by {agent_id}")

def generate_consensus(topic):
    """@consensus - Generate consensus document from research findings"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all findings
    cursor.execute('''
        SELECT agent_id, content, finding_type, created_at
        FROM research_log
        WHERE topic = ?
        ORDER BY created_at
    ''', (topic,))
    findings = cursor.fetchall()
    
    if not findings:
        print(f"⚠️ No findings found for topic '{topic}'")
        conn.close()
        return
    
    # Get participants
    cursor.execute('''
        SELECT agent_id FROM agent_research_participation WHERE topic = ?
    ''', (topic,))
    participants = [row[0] for row in cursor.fetchall()]
    
    # Mark topic as completed
    cursor.execute('''
        UPDATE research_topics
        SET status = 'completed', completed_at = CURRENT_TIMESTAMP
        WHERE topic = ?
    ''', (topic,))
    
    conn.commit()
    conn.close()
    
    # Generate consensus document
    consensus_dir = os.path.join(os.getcwd(), ".agent/consensus")
    os.makedirs(consensus_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{topic.replace(' ', '_').replace('/', '_')}_{timestamp}.md"
    filepath = os.path.join(consensus_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# 🎯 Consensus: {topic}\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Participants**: {', '.join(participants)}\n\n")
        f.write("---\n\n")
        
        for agent_id, content, finding_type, created_at in findings:
            f.write(f"## [{finding_type.upper()}] {agent_id}\n\n")
            f.write(f"*{created_at}*\n\n")
            f.write(f"{content}\n\n")
    
    print(f"✅ Consensus generated: {filepath}")
    print(f"📊 Total findings: {len(findings)}")
    print(f"👥 Participants: {len(participants)}")
    
    return filepath

# ============ TASK MANAGEMENT ============

def assign_task(assigned_by, agent_id, task):
    """@assign - Assign task to specific agent"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO task_assignments (agent_id, task, assigned_by)
        VALUES (?, ?, ?)
    ''', (agent_id, task, assigned_by))
    
    # Notify the agent
    cursor.execute('''
        INSERT INTO notifications (agent_id, message, is_broadcast)
        VALUES (?, ?, 0)
    ''', (agent_id, f"📋 New task assigned by {assigned_by}: {task}"))
    
    conn.commit()
    conn.close()
    print(f"📋 Task assigned to {agent_id} by {assigned_by}")

def list_tasks(agent_id=None):
    """List tasks for an agent or all agents"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if agent_id:
        cursor.execute('''
            SELECT id, task, assigned_by, status, created_at
            FROM task_assignments
            WHERE agent_id = ? AND status != 'completed'
            ORDER BY created_at DESC
        ''', (agent_id,))
        tasks = cursor.fetchall()
        
        print(f"\n📋 Tasks for {agent_id}:")
        for task_id, task, assigned_by, status, created_at in tasks:
            print(f"  [{status.upper()}] #{task_id}: {task} (from {assigned_by})")
    else:
        cursor.execute('''
            SELECT agent_id, id, task, assigned_by, status
            FROM task_assignments
            WHERE status != 'completed'
            ORDER BY agent_id
        ''')
        tasks = cursor.fetchall()
        
        print(f"\n📋 All pending tasks:")
        current_agent = None
        for agent, task_id, task, assigned_by, status in tasks:
            if agent != current_agent:
                print(f"\n  {agent}:")
                current_agent = agent
            print(f"    [{status.upper()}] #{task_id}: {task}")
    
    conn.close()

def complete_task(task_id):
    """Mark a task as completed"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE task_assignments
        SET status = 'completed', completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (task_id,))
    
    if cursor.rowcount > 0:
        print(f"✅ Task #{task_id} marked as completed")
    else:
        print(f"❌ Task #{task_id} not found")
    
    conn.commit()
    conn.close()

# ============ NOTIFICATIONS ============

def broadcast_message(from_agent, message):
    """@notify - Broadcast message to all agents"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM agents WHERE id != ?", (from_agent,))
    other_agents = cursor.fetchall()
    
    for (agent_id,) in other_agents:
        cursor.execute('''
            INSERT INTO notifications (agent_id, message, is_broadcast)
            VALUES (?, ?, 1)
        ''', (agent_id, f"📢 Broadcast from {from_agent}: {message}"))
    
    conn.commit()
    conn.close()
    print(f"📢 Broadcast sent to {len(other_agents)} agents")

def get_notifications(agent_id, unread_only=False):
    """Get notifications for an agent"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if unread_only:
        cursor.execute('''
            SELECT id, message, is_broadcast, created_at
            FROM notifications
            WHERE agent_id = ? AND is_read = 0
            ORDER BY created_at DESC
        ''', (agent_id,))
    else:
        cursor.execute('''
            SELECT id, message, is_broadcast, created_at
            FROM notifications
            WHERE agent_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (agent_id,))
    
    notifications = cursor.fetchall()
    
    print(f"\n🔔 Notifications for {agent_id}:")
    for notif_id, message, is_broadcast, created_at in notifications:
        prefix = "📢" if is_broadcast else "🔔"
        print(f"  {prefix} {message}")
        print(f"     {created_at}")
    
    # Mark as read
    cursor.execute('''
        UPDATE notifications SET is_read = 1
        WHERE agent_id = ? AND is_read = 0
    ''', (agent_id,))
    
    conn.commit()
    conn.close()

# ============ POLLS ============

def start_poll(agent_id, question):
    """@poll - Start a quick poll"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO polls (question, created_by, status)
        VALUES (?, ?, 'active')
    ''', (question, agent_id))
    poll_id = cursor.lastrowid
    
    # Notify all agents
    cursor.execute("SELECT id FROM agents WHERE id != ?", (agent_id,))
    other_agents = cursor.fetchall()
    for (other_id,) in other_agents:
        cursor.execute('''
            INSERT INTO notifications (agent_id, message, is_broadcast)
            VALUES (?, ?, 0)
        ''', (other_id, f"🗳️ New poll from {agent_id}: '{question}' (Poll #{poll_id}). Vote with: @vote {poll_id} <yes/no/maybe>"))
    
    conn.commit()
    conn.close()
    print(f"🗳️ Poll #{poll_id} started: {question}")
    return poll_id

def vote_poll(agent_id, poll_id, vote):
    """@vote - Vote on a poll"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO poll_votes (poll_id, agent_id, vote)
        VALUES (?, ?, ?)
    ''', (poll_id, agent_id, vote))
    
    conn.commit()
    conn.close()
    print(f"✅ Vote recorded for poll #{poll_id}: {vote}")

def show_poll_results(poll_id):
    """Show poll results"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT question FROM polls WHERE id = ?", (poll_id,))
    result = cursor.fetchone()
    if not result:
        print(f"❌ Poll #{poll_id} not found")
        conn.close()
        return
    
    question = result[0]
    
    cursor.execute('''
        SELECT vote, COUNT(*) FROM poll_votes
        WHERE poll_id = ?
        GROUP BY vote
    ''', (poll_id,))
    votes = dict(cursor.fetchall())
    
    cursor.execute('''
        SELECT agent_id, vote FROM poll_votes
        WHERE poll_id = ?
    ''', (poll_id,))
    details = cursor.fetchall()
    
    conn.close()
    
    print(f"\n🗳️ Poll #{poll_id}: {question}")
    print("Results:")
    for vote, count in votes.items():
        print(f"  {vote}: {count}")
    print("\nVotes:")
    for agent, vote in details:
        print(f"  {agent}: {vote}")

# ============ HANDOVER ============

def request_handover(from_agent, to_agent, context=""):
    """@handover - Request task handover to another agent"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current task of from_agent
    cursor.execute("SELECT task FROM agents WHERE id = ?", (from_agent,))
    result = cursor.fetchone()
    current_task = result[0] if result else "current task"
    
    # Create handover notification
    message = f"🔄 Handover request from {from_agent}: '{current_task}'"
    if context:
        message += f" | Context: {context}"
    
    cursor.execute('''
        INSERT INTO notifications (agent_id, message, is_broadcast)
        VALUES (?, ?, 0)
    ''', (to_agent, message))
    
    # Update from_agent status
    cursor.execute('''
        UPDATE agents SET status = 'idle', task = NULL
        WHERE id = ?
    ''', (from_agent,))
    
    conn.commit()
    conn.close()
    print(f"🔄 Handover requested: {from_agent} -> {to_agent}")

def switch_to(agent_id, to_agent):
    """@switch - Request to switch to specific agent"""
    conn = get_connection()
    cursor = conn.cursor()
    
    message = f"🔄 {agent_id} requests to switch to you for continuation"
    
    cursor.execute('''
        INSERT INTO notifications (agent_id, message, is_broadcast)
        VALUES (?, ?, 0)
    ''', (to_agent, message))
    
    conn.commit()
    conn.close()
    print(f"🔄 Switch request sent: {agent_id} -> {to_agent}")

# ============ STATUS & MONITORING ============

def get_status():
    """Enhanced status view"""
    conn = get_connection()
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("🛰️  ACTIVE AGENTS")
    print("="*60)
    
    for row in cursor.execute('''
        SELECT name, task, status, current_research, last_seen 
        FROM agents
        ORDER BY last_seen DESC
    '''):
        status_emoji = {
            'active': '🟢',
            'idle': '⚪',
            'researching': '🔬',
            'busy': '🔴'
        }.get(row[2], '⚪')
        
        research_info = f" | Research: {row[3]}" if row[3] else ""
        print(f"{status_emoji} [{row[2].upper()}] {row[0]}: {row[1]}{research_info}")
        print(f"   Last seen: {row[4]}")

    print("\n" + "="*60)
    print("🔬 ACTIVE RESEARCH TOPICS")
    print("="*60)
    
    for row in cursor.execute('''
        SELECT t.topic, t.initiated_by, t.created_at,
               (SELECT COUNT(*) FROM agent_research_participation WHERE topic = t.topic) as participants,
               (SELECT COUNT(*) FROM research_log WHERE topic = t.topic) as findings
        FROM research_topics t
        WHERE t.status = 'active'
        ORDER BY t.created_at DESC
    '''):
        print(f"🔬 {row[0]}")
        print(f"   Initiated by: {row[1]} | Participants: {row[3]} | Findings: {row[4]}")
        print(f"   Started: {row[2]}")

    print("\n" + "="*60)
    print("🔒 FILE LOCKS")
    print("="*60)
    
    locks = list(cursor.execute('''
        SELECT file_path, agent_id, lock_type 
        FROM file_locks
        ORDER BY timestamp DESC
    '''))
    
    if locks:
        for file_path, agent_id, lock_type in locks:
            lock_emoji = '🔒' if lock_type == 'write' else '🔍'
            print(f"{lock_emoji} {file_path} -> {agent_id} ({lock_type})")
    else:
        print("  No active locks")

    print("\n" + "="*60)
    print("📋 PENDING TASKS")
    print("="*60)
    
    for row in cursor.execute('''
        SELECT agent_id, COUNT(*) 
        FROM task_assignments 
        WHERE status = 'pending'
        GROUP BY agent_id
    '''):
        print(f"  {row[0]}: {row[1]} pending tasks")

    cursor.execute("SELECT value FROM global_settings WHERE key = 'mode'")
    mode = cursor.fetchone()[0]
    print(f"\n🌍 Global Mode: {mode.upper()}")
    print("="*60)
    
    conn.close()

def show_research_topic(topic):
    """Show detailed view of a research topic"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT status, initiated_by, created_at FROM research_topics WHERE topic = ?", (topic,))
    result = cursor.fetchone()
    if not result:
        print(f"❌ Topic '{topic}' not found")
        conn.close()
        return
    
    status, initiated_by, created_at = result
    
    print(f"\n🔬 Research: {topic}")
    print(f"Status: {status} | Initiated by: {initiated_by} | Started: {created_at}")
    
    cursor.execute('''
        SELECT agent_id FROM agent_research_participation WHERE topic = ?
    ''', (topic,))
    participants = [row[0] for row in cursor.fetchall()]
    print(f"Participants: {', '.join(participants)}")
    
    print("\n--- Findings ---")
    cursor.execute('''
        SELECT agent_id, content, finding_type, created_at
        FROM research_log
        WHERE topic = ?
        ORDER BY created_at
    ''', (topic,))
    
    for agent_id, content, finding_type, created_at in cursor.fetchall():
        emoji = {'note': '📝', 'finding': '🔍', 'concern': '⚠️', 'solution': '✅'}.get(finding_type, '📝')
        print(f"\n{emoji} [{finding_type.upper()}] {agent_id} ({created_at})")
        print(f"   {content}")
    
    conn.close()

# ============ MAIN CLI ============

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🤖 Agent Sync v2.0 - Multi-Agent Cooperation Protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
QUICK COMMANDS:
  @research <topic>              Start joint research
  @join <topic>                  Join active research  
  @find <topic> <content>        Post finding to research
  @consensus <topic>             Generate consensus document
  @assign <agent> <task>         Assign task to agent
  @notify <message>              Broadcast to all agents
  @handover <agent> [context]    Handover task
  @switch <agent>                Request switch to agent
  @poll <question>               Start a poll
  @vote <poll_id> <vote>         Vote on poll
  @tasks [agent]                 List tasks
  @complete <task_id>            Complete task
  @notifications [agent]         Check notifications
  @topic <topic>                 View research topic details

EXAMPLES:
  python3 agent_sync_v2.py research claude-code "API Design"
  python3 agent_sync_v2.py find copilot "API Design" "Use REST instead of GraphQL"
  python3 agent_sync_v2.py assign claude-code copilot "Implement REST endpoints"
  python3 agent_sync_v2.py consensus "API Design"
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Legacy commands
    subparsers.add_parser("init", help="Initialize the database")
    
    reg = subparsers.add_parser("register", help="Register an agent")
    reg.add_argument("id", help="Agent ID")
    reg.add_argument("name", help="Agent name")
    reg.add_argument("task", help="Current task")
    reg.add_argument("--status", default="idle", help="Agent status")

    lock = subparsers.add_parser("lock", help="Lock a file")
    lock.add_argument("id", help="Agent ID")
    lock.add_argument("path", help="File path")
    lock.add_argument("--type", default="write", choices=["write", "research"], help="Lock type")

    unlock = subparsers.add_parser("unlock", help="Unlock a file")
    unlock.add_argument("id", help="Agent ID")
    unlock.add_argument("path", help="File path")

    subparsers.add_parser("status", help="Show status dashboard")

    # New v2.0 commands
    research = subparsers.add_parser("research", help="@research - Start joint research topic")
    research.add_argument("agent_id", help="Agent initiating research")
    research.add_argument("topic", help="Research topic")

    join = subparsers.add_parser("join", help="@join - Join active research")
    join.add_argument("agent_id", help="Agent joining")
    join.add_argument("topic", help="Topic to join")

    find = subparsers.add_parser("find", help="@find - Post finding to research")
    find.add_argument("agent_id", help="Agent posting finding")
    find.add_argument("topic", help="Research topic")
    find.add_argument("content", help="Finding content")
    find.add_argument("--type", default="note", choices=["note", "finding", "concern", "solution"], help="Type of finding")

    consensus = subparsers.add_parser("consensus", help="@consensus - Generate consensus document")
    consensus.add_argument("topic", help="Topic to generate consensus for")

    assign = subparsers.add_parser("assign", help="@assign - Assign task to agent")
    assign.add_argument("from_agent", help="Agent assigning the task")
    assign.add_argument("to_agent", help="Agent to assign task to")
    assign.add_argument("task", help="Task description")

    tasks = subparsers.add_parser("tasks", help="@tasks - List pending tasks")
    tasks.add_argument("--agent", help="Filter by agent ID")

    complete = subparsers.add_parser("complete", help="@complete - Mark task as completed")
    complete.add_argument("task_id", type=int, help="Task ID to complete")

    notify = subparsers.add_parser("notify", help="@notify - Broadcast message to all agents")
    notify.add_argument("from_agent", help="Agent sending notification")
    notify.add_argument("message", help="Message to broadcast")

    handover = subparsers.add_parser("handover", help="@handover - Handover task to another agent")
    handover.add_argument("from_agent", help="Current agent")
    handover.add_argument("to_agent", help="Agent to handover to")
    handover.add_argument("--context", default="", help="Handover context")

    switch = subparsers.add_parser("switch", help="@switch - Request switch to specific agent")
    switch.add_argument("from_agent", help="Current agent")
    switch.add_argument("to_agent", help="Agent to switch to")

    poll = subparsers.add_parser("poll", help="@poll - Start a quick poll")
    poll.add_argument("agent_id", help="Agent starting poll")
    poll.add_argument("question", help="Poll question")

    vote = subparsers.add_parser("vote", help="@vote - Vote on a poll")
    vote.add_argument("agent_id", help="Agent voting")
    vote.add_argument("poll_id", type=int, help="Poll ID")
    vote.add_argument("vote_choice", choices=["yes", "no", "maybe"], help="Your vote")

    poll_results = subparsers.add_parser("poll-results", help="Show poll results")
    poll_results.add_argument("poll_id", type=int, help="Poll ID")

    notifications = subparsers.add_parser("notifications", help="@notifications - Check notifications")
    notifications.add_argument("agent_id", help="Agent to check notifications for")
    notifications.add_argument("--unread", action="store_true", help="Show only unread")

    topic = subparsers.add_parser("topic", help="@topic - View research topic details")
    topic.add_argument("topic_name", help="Topic name")

    args = parser.parse_args()

    if args.command == "init":
        init_db()
    elif args.command == "register":
        register_agent(args.id, args.name, args.task, args.status)
    elif args.command == "lock":
        lock_file(args.id, args.path, args.type)
    elif args.command == "unlock":
        unlock_file(args.id, args.path)
    elif args.command == "status":
        get_status()
    elif args.command == "research":
        start_research(args.agent_id, args.topic)
    elif args.command == "join":
        join_research(args.agent_id, args.topic)
    elif args.command == "find":
        post_finding(args.agent_id, args.topic, args.content, args.type)
    elif args.command == "consensus":
        generate_consensus(args.topic)
    elif args.command == "assign":
        assign_task(args.from_agent, args.to_agent, args.task)
    elif args.command == "tasks":
        list_tasks(args.agent)
    elif args.command == "complete":
        complete_task(args.task_id)
    elif args.command == "notify":
        broadcast_message(args.from_agent, args.message)
    elif args.command == "handover":
        request_handover(args.from_agent, args.to_agent, args.context)
    elif args.command == "switch":
        switch_to(args.from_agent, args.to_agent)
    elif args.command == "poll":
        start_poll(args.agent_id, args.question)
    elif args.command == "vote":
        vote_poll(args.agent_id, args.poll_id, args.vote_choice)
    elif args.command == "poll-results":
        show_poll_results(args.poll_id)
    elif args.command == "notifications":
        get_notifications(args.agent_id, args.unread)
    elif args.command == "topic":
        show_research_topic(args.topic_name)
    else:
        parser.print_help()
