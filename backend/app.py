import asyncio
import datetime
import threading
import time
import os
import requests
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import (
    init_db,
    create_build_archetype,
    create_task_archetype,
    get_build_archetypes,
    get_task_archetypes,
    delete_archetype,
    create_task_instance,
    get_task_instances,
    update_task_instance,
)

app = Flask(__name__)
CORS(app)

# Lock for synchronizing queue processing
queue_lock = threading.Lock()

# Jenkins configuration
JENKINS_URL = os.environ.get("JENKINS_URL")
JENKINS_JOB = os.environ.get("JENKINS_JOB")
JENKINS_USER = os.environ.get("JENKINS_USER")
JENKINS_API_TOKEN = os.environ.get("JENKINS_API_TOKEN")
JENKINS_BUILD_TOKEN = os.environ.get("JENKINS_BUILD_TOKEN")

# Validate environment variables at startup
required_env_vars = ["JENKINS_URL", "JENKINS_JOB", "JENKINS_USER", "JENKINS_API_TOKEN", "JENKINS_BUILD_TOKEN"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")


def process_queue():
    with queue_lock:
        print(f"[{datetime.datetime.now()}] Starting process_queue")

        conn = init_db()
        instances = get_task_instances(["pending"])
        print(f"[{datetime.datetime.now()}] Found {len(instances)} pending task(s)")

        for instance in instances:
            task_id = instance.get("id")
            print(f"\n--- Processing Task {task_id} ---")

            try:
                # Prepare parameters
                build_content = instance.get("build_archetype_content")
                task_content = instance.get("task_archetype_content")

                if not build_content or not task_content:
                    print(
                        f"❌ Missing content in task {task_id}: build={bool(build_content)}, task={bool(task_content)}"
                    )
                    continue

                params = {
                    "build_content": build_content,
                    "task_content": task_content,
                    "task_instance_id": task_id,
                    "token": JENKINS_BUILD_TOKEN,
                }

                trigger_url = f"{JENKINS_URL}/job/{JENKINS_JOB}/buildWithParameters"
                print(f"🔗 Trigger URL: {trigger_url}")
                print(f"📤 Params: {params}")

                # Send to Jenkins
                response = requests.post(
                    trigger_url,
                    params=params,
                    auth=(JENKINS_USER, JENKINS_API_TOKEN),
                    timeout=30,
                )

                print(f"📥 Response: {response.status_code} {response.text}")

                if response.status_code == 201:
                    print(f"✅ Successfully triggered Jenkins job for task {task_id}")
                    update_task_instance(task_id, "done")
                else:
                    print(f"❌ Failed to trigger Jenkins for task {task_id}: {response.status_code}")
                    if response.status_code == 401:
                        print("🔐 Jenkins auth failed. Check JENKINS_API_TOKEN.")
                    elif response.status_code == 403:
                        print("⛔ Invalid Jenkins build token.")
                    else:
                        print("⚠️ Unhandled Jenkins response.")

                    reprioritize_task(conn, task_id)

            except Exception as e:
                print(f"💥 Exception processing task {task_id}: {e}")
                reprioritize_task(conn, task_id)

        print(f"[{datetime.datetime.now()}] Finished process_queue")
        conn.close()


def reprioritize_task(conn, task_id):
    print(f"🔄 Reprioritizing task {task_id} (set to pending, update timestamp)")
    try:
        c = conn.cursor()
        c.execute(
            """UPDATE task_instances 
               SET state = ?, created_at = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            ("pending", task_id),
        )
        conn.commit()
        print(f"🔁 Task {task_id} reprioritized successfully")
    except Exception as e:
        print(f"🚫 Failed to reprioritize task {task_id}: {e}")


# Background thread for periodic queue processing
def periodic_queue_processing():
    while True:
        process_queue()
        time.sleep(300)


# Start periodic queue processing
threading.Thread(target=periodic_queue_processing, daemon=True).start()


@app.route("/api/build_archetypes", methods=["GET", "POST"])
def handle_build_archetypes():
    if request.method == "POST":
        data = request.json
        archetype_id = create_build_archetype(data["content"])
        return jsonify({"id": archetype_id}), 201
    return jsonify(get_build_archetypes())


@app.route("/api/build_archetypes/<int:id>", methods=["DELETE"])
def delete_build_archetype(id):
    delete_archetype("build_archetypes", id)
    return "", 204


@app.route("/api/task_archetypes", methods=["GET", "POST"])
def handle_task_archetypes():
    if request.method == "POST":
        data = request.json
        archetype_id = create_task_archetype(data["content"])
        return jsonify({"id": archetype_id}), 201
    return jsonify(get_task_archetypes())


@app.route("/api/task_archetypes/<int:id>", methods=["DELETE"])
def delete_task_archetype(id):
    delete_archetype("task_archetypes", id)
    return "", 204


@app.route("/api/task_instances", methods=["GET", "POST"])
def handle_task_instances():
    if request.method == "POST":
        data = request.json
        instance_id = create_task_instance(data["build_archetype_id"], data["task_archetype_id"])
        process_queue()
        return jsonify({"id": instance_id}), 201
    state = request.args.get("state", "pending")
    return jsonify(get_task_instances(state.split(",")))


@app.route("/api/task_instances/<int:id>", methods=["GET", "PUT"])
def update_task_instance_route(id):
    if request.method == "GET":
        conn = init_db()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            """SELECT ti.*, ta.content as task_content, ba.content as build_content
            FROM task_instances ti
            JOIN task_archetypes ta ON ti.task_archetype_id = ta.id
            JOIN build_archetypes ba ON ti.build_archetype_id = ba.id
            WHERE ti.id = ?""",
            (id,),
        )
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Task instance not found"}), 404
        instance = {
            "id": row["id"],
            "build_archetype_id": row["build_archetype_id"],
            "task_archetype_id": row["task_archetype_id"],
            "state": row["state"],
            "sweep_id": row["sweep_id"],
            "task_archetype_content": json.loads(row["task_content"]),
            "build_archetype_content": json.loads(row["build_content"]),
        }
        conn.close()
        return jsonify(instance)

    data = request.json
    conn = init_db()
    c = conn.cursor()

    try:
        if "reorder" in data:
            reorder = data["reorder"]
            move = reorder.get("move")
            relative_to_id = reorder.get("relativeTo")

            if not move or not relative_to_id or move not in ["before", "after"]:
                return jsonify({"error": "Invalid reorder parameters"}), 400

            c.execute("SELECT created_at FROM task_instances WHERE id = ?", (relative_to_id,))
            target = c.fetchone()
            if not target:
                return jsonify({"error": "Target task not found"}), 404
            target_timestamp = target[0]

            c.execute(
                """SELECT id, created_at FROM task_instances 
                   WHERE state = 'pending' AND id != ? 
                   ORDER BY created_at ASC""",
                (id,),
            )
            pending_tasks = c.fetchall()

            new_timestamp = None
            if move == "before":
                prev_timestamp = None
                for task in pending_tasks:
                    if task[0] == relative_to_id:
                        break
                    prev_timestamp = task[1]
                if prev_timestamp:
                    prev_time = datetime.datetime.strptime(prev_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    target_time = datetime.datetime.strptime(target_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    delta = (target_time - prev_time) / 2
                    new_timestamp = (prev_time + delta).strftime("%Y-%m-%d %H:%M:%S.%f")
                else:
                    target_time = datetime.datetime.strptime(target_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    new_timestamp = (target_time - datetime.timedelta(microseconds=1)).strftime("%Y-%m-%d %H:%M:%S.%f")
            else:
                next_timestamp = None
                found_target = False
                for task in pending_tasks:
                    if found_target:
                        next_timestamp = task[1]
                        break
                    if task[0] == relative_to_id:
                        found_target = True
                if next_timestamp:
                    target_time = datetime.datetime.strptime(target_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    next_time = datetime.datetime.strptime(next_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    delta = (next_time - target_time) / 2
                    new_timestamp = (target_time + delta).strftime("%Y-%m-%d %H:%M:%S.%f")
                else:
                    target_time = datetime.datetime.strptime(target_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    new_timestamp = (target_time + datetime.timedelta(microseconds=1)).strftime("%Y-%m-%d %H:%M:%S.%f")

            c.execute(
                """UPDATE task_instances 
                   SET created_at = ? 
                   WHERE id = ?""",
                (new_timestamp, id),
            )
            conn.commit()
        else:
            state = data.get("state")
            sweep_id = data.get("sweep_id")
            if state or sweep_id:
                fields = []
                values = []
                if state:
                    fields.append("state = ?")
                    values.append(state)
                if sweep_id:
                    fields.append("sweep_id = ?")
                    values.append(sweep_id)
                values.append(id)
                c.execute(f"UPDATE task_instances SET {', '.join(fields)} WHERE id = ?", values)
                conn.commit()
            if data.get("state") == "pending":
                process_queue()

        conn.close()
        return "", 204

    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route("/api/task_instances/<int:id>/rerun", methods=["POST"])
def rerun_task_instance(id):
    update_task_instance(id, "pending")
    process_queue()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=40378)
