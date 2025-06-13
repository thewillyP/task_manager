from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sock import Sock
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
import threading
import time
import requests
import json

app = Flask(__name__)
CORS(app)
sock = Sock(app)

# Lock for synchronizing queue processing
queue_lock = threading.Lock()
clients = set()


@sock.route("/ws")
def ws(ws):
    clients.add(ws)
    try:
        while True:
            ws.receive()  # Keep connection alive
    finally:
        clients.remove(ws)


def notify_clients():
    for client in clients.copy():
        try:
            client.send(json.dumps({"type": "update"}))
        except:
            clients.remove(client)


# Background task for queue processing
def process_queue():
    with queue_lock:
        conn = init_db()
        instances = get_task_instances(["pending"])
        for instance in instances:
            try:
                # TODO: Replace with your HTTP command
                print(f"Processing task {instance['id']} with HTTP command")
                update_task_instance(instance["id"], "done", 0)
                notify_clients()
            except Exception as e:
                print(f"Error processing task {instance['id']}: {e}")
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
        notify_clients()
        return jsonify({"id": archetype_id}), 201
    return jsonify(get_build_archetypes())


@app.route("/api/build_archetypes/<int:id>", methods=["DELETE"])
def delete_build_archetype(id):
    delete_archetype("build_archetypes", id)
    notify_clients()
    return "", 204


@app.route("/api/task_archetypes", methods=["GET", "POST"])
def handle_task_archetypes():
    if request.method == "POST":
        data = request.json
        if "num_jobs" not in data["content"] or "pipeline" not in data["content"]:
            return jsonify({"error": "num_jobs and pipeline are required"}), 400
        archetype_id = create_task_archetype(data["content"])
        notify_clients()
        return jsonify({"id": archetype_id}), 201
    return jsonify(get_task_archetypes())


@app.route("/api/task_archetypes/<int:id>", methods=["DELETE"])
def delete_task_archetype(id):
    delete_archetype("task_archetypes", id)
    notify_clients()
    return "", 204


@app.route("/api/task_instances", methods=["GET", "POST"])
def handle_task_instances():
    if request.method == "POST":
        data = request.json
        instance_id = create_task_instance(data["build_archetype_id"], data["task_archetype_id"], data["num_jobs"])
        notify_clients()
        process_queue()
        return jsonify({"id": instance_id}), 201
    state = request.args.get("state", "pending")
    return jsonify(get_task_instances(state.split(",")))


@app.route("/api/task_instances/<int:id>", methods=["PUT"])
def update_task_instance_route(id):
    data = request.json
    update_task_instance(id, data.get("state"), data.get("num_jobs_remaining"), data.get("position"))
    notify_clients()
    if data.get("state") == "pending" or data.get("num_jobs_remaining") is not None:
        process_queue()
    return "", 204


@app.route("/api/task_instances/<int:id>/rerun", methods=["POST"])
def rerun_task_instance(id):
    data = request.json
    update_task_instance(id, "pending", data["num_jobs_remaining"])
    notify_clients()
    process_queue()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
