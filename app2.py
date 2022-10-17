from datetime import timedelta

from flask import Flask, jsonify, abort, make_response, request
from flask import url_for

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "SuperSecretKey"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=5)
jwt = JWTManager(app)


@app.route("/login", methods=["POST"])
def login():
    # from IPython import embed

    # embed()
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    if username != "test" or password != "test":
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)


tasks = [
    {
        "id": 1,
        "title": "Buy groceries",
        "description": "Milk, Cheese, Pizza, Fruit, Tylenol",
        "done": False,
    },
    {
        "id": 2,
        "title": "Learn Python",
        "description": "Need to find a good Python tutorial on the web",
        "done": False,
    },
]


@app.route("/")
def index():
    return "Hello, World!"


@app.route("/todo/api/v1.0/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    return jsonify({"tasks": [make_public_task(task) for task in tasks]})


@app.route("/todo/api/v1.0/tasks/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    task = [task for task in tasks if task["id"] == task_id]
    if not task:
        abort(404)
    return jsonify(task)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error": "Not found"}), 404)


@app.route("/todo/api/v1.0/tasks", methods=["POST"])
@jwt_required()
def create_task():

    if not request.json or "title" not in request.json:
        abort(400)
    task = {
        "id": tasks[-1]["id"] + 1,
        "title": request.json["title"],
        "description": request.json.get("description", ""),
        "done": False,
    }
    tasks.append(task)
    return jsonify({"task": task}), 201


@app.route("/todo/api/v1.0/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    task = [task for task in tasks if task["id"] == task_id]
    if not task:
        abort(404)
    if not request.json:
        abort(400)
    if "title" in request.json and type(request.json["title"]) != str:
        abort(400)
    if "description" in request.json and type(request.json["description"]) is not str:
        abort(400)
    task[0]["title"] = request.json.get("title", task[0]["title"])
    task[0]["description"] = request.json.get("description", task[0]["description"])
    task[0]["done"] = request.json.get("done", task[0]["done"])
    return jsonify({"task": task[0]})


@app.route("/todo/api/v1.0/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    task = [task for task in tasks if task["id"] == task_id]
    if not task:
        abort(404)
    tasks.remove(task[0])
    return jsonify({"result": True})


def make_public_task(task):
    new_task = {}
    for field in task:
        if field == "id":
            new_task["uri"] = url_for("get_task", task_id=task["id"], _external=True)
        else:
            new_task[field] = task[field]
    return new_task


def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()


@app.route("/shutdown", methods=["GET"])
def shutdown():
    shutdown_server()
    return "Server shutting down..."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8080", debug=True)
