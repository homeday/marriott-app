import os
import re

from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text


app = Flask(__name__)

username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")
endpoint = os.environ.get("ENDPOINT")
db_port = os.environ.get("DB_PORT", "5432")
db_name = os.environ.get("DB_NAME", "appdb")
table_name = os.environ.get("INIT_TABLE_NAME", "app_table")

if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
    raise ValueError("INIT_TABLE_NAME must be a valid SQL identifier")

connection_string = f"postgresql+psycopg2://{username}:{password}@{endpoint}:{db_port}/{db_name}"
engine = create_engine(connection_string, pool_pre_ping=True)

@app.get("/")
def ok() -> tuple:
    env_val = os.environ.get("APP_ENV", "n/a")
    return jsonify({"status": "ok", "env": env_val}), 200


@app.post("/db-insert")
def db_insert() -> tuple:
    payload = request.get_json(silent=True) or {}
    note = payload.get("note") or request.args.get("note") or "created by api"
    query = text(f"INSERT INTO {table_name} (note) VALUES (:note) RETURNING id, created_at, note")

    with engine.begin() as conn:
        row = conn.execute(query, {"note": note}).mappings().first()

    result = dict(row)
    if result.get("created_at") is not None:
        result["created_at"] = result["created_at"].isoformat()
    return jsonify({"status": "inserted", "data": result}), 201


@app.get("/db-query")
def db_query() -> tuple:
    requested_limit = request.args.get("limit", "10")
    try:
        limit = int(requested_limit)
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    limit = max(1, min(limit, 100))
    query = text(f"SELECT id, created_at, note FROM {table_name} ORDER BY id DESC LIMIT :limit")

    with engine.connect() as conn:
        rows = conn.execute(query, {"limit": limit}).mappings().all()

    data = []
    for row in rows:
        item = dict(row)
        if item.get("created_at") is not None:
            item["created_at"] = item["created_at"].isoformat()
        data.append(item)
    return jsonify({"status": "ok", "count": len(data), "data": data}), 200


@app.get("/health/live")
def health_live() -> tuple:
    return jsonify({"status": "live"}), 200


@app.get("/health/ready")
def health_ready() -> tuple:
    return jsonify({"status": "ready"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)