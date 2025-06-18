import sqlite3
from datetime import datetime
import json


def init_db():
    conn = sqlite3.connect("/app/task_queue.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS build_archetypes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS task_archetypes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS task_instances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        build_archetype_id INTEGER,
        task_archetype_id INTEGER,
        state TEXT,
        sweep_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(build_archetype_id) REFERENCES build_archetypes(id),
        FOREIGN KEY(task_archetype_id) REFERENCES task_archetypes(id)
    )""")

    c.execute("CREATE INDEX IF NOT EXISTS idx_state ON task_instances(state)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON task_instances(created_at)")

    conn.commit()
    return conn


def create_build_archetype(content):
    conn = sqlite3.connect("/app/task_queue.db")
    c = conn.cursor()
    c.execute("INSERT INTO build_archetypes (content) VALUES (?)", (json.dumps(content),))
    archetype_id = c.lastrowid
    conn.commit()
    conn.close()
    return archetype_id


def create_task_archetype(content):
    conn = sqlite3.connect("/app/task_queue.db")
    c = conn.cursor()
    c.execute("INSERT INTO task_archetypes (content) VALUES (?)", (json.dumps(content),))
    archetype_id = c.lastrowid
    conn.commit()
    conn.close()
    return archetype_id


def get_build_archetypes():
    conn = sqlite3.connect("/app/task_queue.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, content FROM build_archetypes ORDER BY created_at DESC")
    archetypes = [{"id": row["id"], "content": json.loads(row["content"])} for row in c.fetchall()]
    conn.close()
    return archetypes


def get_task_archetypes():
    conn = sqlite3.connect("/app/task_queue.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, content FROM task_archetypes ORDER BY created_at DESC")
    archetypes = [{"id": row["id"], "content": json.loads(row["content"])} for row in c.fetchall()]
    conn.close()
    return archetypes


def delete_archetype(table, id):
    conn = sqlite3.connect("/app/task_queue.db")
    c = conn.cursor()
    c.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    conn.commit()
    conn.close()


def create_task_instance(build_archetype_id, task_archetype_id, sweep_id=None):
    conn = sqlite3.connect("/app/task_queue.db")
    c = conn.cursor()
    c.execute(
        """INSERT INTO task_instances 
        (build_archetype_id, task_archetype_id, state, sweep_id)
        VALUES (?, ?, 'pending', ?)""",
        (build_archetype_id, task_archetype_id, sweep_id),
    )
    instance_id = c.lastrowid
    conn.commit()
    conn.close()
    return instance_id


def get_task_instances(states):
    conn = sqlite3.connect("/app/task_queue.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    placeholders = ",".join("?" for _ in states)
    c.execute(
        f"""SELECT ti.*, ta.content as task_content, ba.content as build_content
        FROM task_instances ti
        JOIN task_archetypes ta ON ti.task_archetype_id = ta.id
        JOIN build_archetypes ba ON ti.build_archetype_id = ba.id
        WHERE ti.state IN ({placeholders})
        ORDER BY ti.created_at ASC""",
        states,
    )
    instances = [
        {
            "id": row["id"],
            "build_archetype_id": row["build_archetype_id"],
            "task_archetype_id": row["task_archetype_id"],
            "state": row["state"],
            "sweep_id": row["sweep_id"],
            "task_archetype_content": json.loads(row["task_content"]),
            "build_archetype_content": json.loads(row["build_content"]),
        }
        for row in c.fetchall()
    ]
    conn.close()
    return instances


def update_task_instance(id, state=None, sweep_id=None):
    conn = sqlite3.connect("/app/task_queue.db")
    c = conn.cursor()
    fields = []
    values = []
    if state:
        fields.append("state = ?")
        values.append(state)
    if sweep_id:
        fields.append("sweep_id = ?")
        values.append(sweep_id)
    if fields:
        values.append(id)
        c.execute(f"UPDATE task_instances SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    conn.close()
