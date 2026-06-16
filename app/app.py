import os

from flask import Flask, jsonify


app = Flask(__name__)


@app.get("/")
def ok() -> tuple:
    env_val = os.environ.get("APP_ENV", "n/a")
    return jsonify({"status": "ok", "env": env_val}), 200


@app.get("/health/live")
def health_live() -> tuple:
    return jsonify({"status": "live"}), 200


@app.get("/health/ready")
def health_ready() -> tuple:
    return jsonify({"status": "ready"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)