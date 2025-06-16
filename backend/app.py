import asyncio
import threading
import time
import os
import requests
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
JENKINS_URL = os.environ.get("JENKINS_URL")  # Default Jenkins URL
JENKINS_JOB = os.environ.get("JENKINS_JOB")  # Default pipeline name
JENKINS_USER = os.environ.get("JENKINS_USER")  # Jenkins username
JENKINS_API_TOKEN = os.environ.get("JENKINS_API_TOKEN")  # API token from env


# Background task for queue processing
def process_queue():
    with queue_lock:
        conn = init_db()
        instances = get_task_instances(["pending"])
        for instance in instances:
            try:
                # Use content from get_task_instances
                params = {
                    "build_content": instance["build_archetype_content"],
                    "task_content": instance["task_archetype_content"],
                    "num_jobs": instance["num_jobs_remaining"],
                    "task_instance_id": instance["id"],
                }

                # Construct Jenkins build trigger URL
                trigger_url = f"{JENKINS_URL}/job/{JENKINS_JOB}/buildWithParameters"

                # Validate JENKINS_API_TOKEN
                if not JENKINS_API_TOKEN:
                    raise ValueError("JENKINS_API_TOKEN is not set")

                # Send HTTP request to Jenkins
                response = requests.post(trigger_url, params=params, auth=(JENKINS_USER, JENKINS_API_TOKEN), timeout=30)

                # Check response
                if response.status_code == 201:
                    print(f"Successfully triggered Jenkins pipeline for task {instance['id']}")
                    update_task_instance(instance["id"], "done", 0)
                else:
                    print(
                        f"Failed to trigger Jenkins pipeline for task {instance['id']}: {response.status_code} {response.text}"
                    )
                    # Reprioritize: Reset to pending, update timestamp
                    c = conn.cursor()
                    c.execute(
                        """UPDATE task_instances 
                           SET state = ?, created_at = CURRENT_TIMESTAMP 
                           WHERE id = ?""",
                        ("pending", instance["id"]),
                    )
                    conn.commit()
                    print(f"Task {instance['id']} reprioritized for retry")

            except Exception as e:
                print(f"Error processing task {instance['id']}: {e}")
                # Reprioritize: Reset to pending, update timestamp
                c = conn.cursor()
                c.execute(
                    """UPDATE task_instances 
                       SET state = ?, created_at = CURRENT_TIMESTAMP 
                       WHERE id = ?""",
                    ("pending", instance["id"]),
                )
                conn.commit()
                print(f"Task {instance['id']} reprioritized for retry")
        conn.close()


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
        if "num_jobs" not in data["content"] or "pipeline" not in data["content"]:
            return jsonify({"error": "num_jobs and pipeline are required"}), 400
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
        instance_id = create_task_instance(data["build_archetype_id"], data["task_archetype_id"], data["num_jobs"])
        process_queue()
        return jsonify({"id": instance_id}), 201
    state = request.args.get("state", "pending")
    return jsonify(get_task_instances(state.split(",")))


@app.route("/api/task_instances/<int:id>", methods=["PUT"])
def update_task_instance_route(id):
    data = request.json
    conn = init_db()
    c = conn.cursor()

    try:
        if "reorder" in data:
            # Handle relative reordering
            reorder = data["reorder"]
            move = reorder.get("move")  # "before" or "after"
            relative_to_id = reorder.get("relativeTo")  # Target task ID

            if not move or not relative_to_id or move not in ["before", "after"]:
                return jsonify({"error": "Invalid reorder parameters"}), 400

            # Get the target task's created_at
            c.execute("SELECT created_at FROM task_instances WHERE id = ?", (relative_to_id,))
            target = c.fetchone()
            if not target:
                return jsonify({"error": "Target task not found"}), 404
            target_timestamp = target[0]

            # Get surrounding tasks to determine new timestamp
            c.execute(
                """SELECT id, created_at FROM task_instances 
                   WHERE state = 'pending' AND id != ? 
                   ORDER BY created_at ASC""",
                (id,),
            )
            pending_tasks = c.fetchall()

            new_timestamp = None
            if move == "before":
                # Find the task just before the target
                prev_timestamp = None
                for task in pending_tasks:
                    if task[0] == relative_to_id:
                        break
                    prev_timestamp = task[1]
                if prev_timestamp:
                    # Set new timestamp halfway between prev and target
                    prev_time = datetime.strptime(prev_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    target_time = datetime.strptime(target_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    delta = (target_time - prev_time) / 2
                    new_timestamp = (prev_time + delta).strftime("%Y-%m-%d %H:%M:%S.%f")
                else:
                    # No previous task; set slightly before target
                    target_time = datetime.strptime(target_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    new_timestamp = (target_time - timedelta(microseconds=1)).strftime("%Y-%m-%d %H:%M:%S.%f")
            else:  # move == "after"
                # Find the task just after the target
                next_timestamp = None
                found_target = False
                for task in pending_tasks:
                    if found_target:
                        next_timestamp = task[1]
                        break
                    if task[0] == relative_to_id:
                        found_target = True
                if next_timestamp:
                    # Set new timestamp halfway between target and next
                    target_time = datetime.strptime(target_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    next_time = datetime.strptime(next_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    delta = (next_time - target_time) / 2
                    new_timestamp = (target_time + delta).strftime("%Y-%m-%d %H:%M:%S.%f")
                else:
                    # No next task; set slightly after target
                    target_time = datetime.strptime(target_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    new_timestamp = (target_time + timedelta(microseconds=1)).strftime("%Y-%m-%d %H:%M:%S.%f")

            # Update the task's created_at
            c.execute(
                """UPDATE task_instances 
                   SET created_at = ? 
                   WHERE id = ?""",
                (new_timestamp, id),
            )
            conn.commit()

        else:
            # Handle existing state and num_jobs_remaining updates
            update_task_instance(id, data.get("state"), data.get("num_jobs_remaining"))
            if data.get("state") == "pending" or data.get("num_jobs_remaining") is not None:
                process_queue()

        conn.close()
        return "", 204

    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route("/api/task_instances/<int:id>/rerun", methods=["POST"])
def rerun_task_instance(id):
    data = request.json
    update_task_instance(id, "pending", data["num_jobs_remaining"])
    process_queue()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
