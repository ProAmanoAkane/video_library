import os
import json
from pathlib import Path
from functools import wraps
from flask import Flask, jsonify, request, send_file, abort


DATA_DIR = Path(__file__).parent / "data"

app = Flask(__name__)


def load_data(file_path: Path) -> dict:
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    return data


def save_data(file_path: Path, data: dict) -> None:
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get("x-api-key")
        if key != os.environ.get("API_KEY"):
            abort(401)
        return func(*args, **kwargs)

    return wrapper


@app.route("/library/<username>", methods=["GET", "POST", "DELETE"])
@require_api_key
def handle_json(username):
    file_path = Path(f"{DATA_DIR}/{username}.json")
    data = load_data(file_path)
    if request.method == "GET":
        return send_file(file_path, mimetype="application/json")
    elif request.method == "POST":
        data.update(request.json)
        save_data(file_path, data)
        return jsonify(
            {
                "status": "success",
            }
        )
    elif request.method == "DELETE":
        title = request.args.get("title").lower()
        if title in data:
            del data[title]
            save_data(file_path, data)
            return jsonify(
                {
                    "status": "success",
                }
            )
        return jsonify(
            {
                "status": "error",
                "message": "Title not found",
            }
        )


@app.route("/users.json", methods=["GET", "POST"])
@require_api_key
def handle_users():
    file_path = Path(f"{DATA_DIR}/users.json")
    data = load_data(file_path)
    if request.method == "GET":
        username = request.args.get("username")
        try:
            return jsonify(data[username])
        except KeyError:
            return jsonify(
                {
                    "status": "error",
                    "message": "User not found",
                }
            )
    elif request.method == "POST":
        new_user = request.json
        if new_user["username"] in data:
            return jsonify(
                {
                    "status": "error",
                    "message": "Username already exists",
                }
            )
        data[new_user["username"]] = new_user
        save_data(file_path, data)
        library = Path(f"{DATA_DIR}/{new_user['username']}.json")
        save_data(library, {})
        return jsonify(
            {
                "status": "success",
            }
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
