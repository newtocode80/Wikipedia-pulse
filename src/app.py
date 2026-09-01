#!/usr/bin/env python3

import os
from datetime import datetime
from pathlib import Path

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


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