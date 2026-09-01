#!/usr/bin/env python3

import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_client import Counter, REGISTRY


# Define one explicit location for the SQLite database
BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = INSTANCE_DIR / "wikipedia_pulse.db"


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATABASE_PATH}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)
migrate = Migrate(app, db)

REQUEST_COUNT = Counter(
    "wikipedia_pulse_http_requests",
    "Total HTTP requests received by Wikipedia Pulse"
)

REQUEST_TIMESTAMPS = deque()
REQUEST_TIMESTAMPS_LOCK = Lock()

METRIC_WINDOW_SECONDS = 60

@app.before_request
def record_request():
    now = time.monotonic()

    REQUEST_COUNT.inc()

    with REQUEST_TIMESTAMPS_LOCK:
        REQUEST_TIMESTAMPS.append(now)

        cutoff = now - METRIC_WINDOW_SECONDS

        while REQUEST_TIMESTAMPS and REQUEST_TIMESTAMPS[0] < cutoff:
            REQUEST_TIMESTAMPS.popleft()



class WikipediaEdit(db.Model):
    __tablename__ = "wikipedia_edits"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(500), nullable=False)

    user = db.Column(db.String(255))

    wiki = db.Column(db.String(100))

    change_type = db.Column(db.String(50))

    bot = db.Column(db.Boolean, default=False)

    event_time = db.Column(db.DateTime)

    collected_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
def format_echo(input_text):
    return "You entered: " + input_text


@app.route("/")
def main():
    return '''
    <form action="/echo_user_input" method="POST">
        <input name="user_input">
        <input type="submit" value="Submit!">
    </form>
    '''


@app.route("/echo_user_input", methods=["POST"])
def echo_input():
    input_text = request.form.get("user_input", "")
    return "You entered: " + input_text


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "wikipedia-pulse"
    }), 200

@app.route("/metrics")
def metrics():
    now = time.monotonic()

    with REQUEST_TIMESTAMPS_LOCK:
        cutoff = now - METRIC_WINDOW_SECONDS

        while REQUEST_TIMESTAMPS and REQUEST_TIMESTAMPS[0] < cutoff:
            REQUEST_TIMESTAMPS.popleft()

        requests_last_minute = len(REQUEST_TIMESTAMPS)

    requests_per_second = (
        requests_last_minute / METRIC_WINDOW_SECONDS
    )

    total_requests = (
        REGISTRY.get_sample_value(
            "wikipedia_pulse_http_requests_total"
        ) or 0
    )

    return jsonify({
        "requests_total": int(total_requests),
        "requests_last_60_seconds": requests_last_minute,
        "requests_per_second": round(requests_per_second, 3),
        "window_seconds": METRIC_WINDOW_SECONDS
    }), 200
