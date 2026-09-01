#!/usr/bin/env python3

import json
from datetime import datetime

import pika

from src.app import app, db, WikipediaEdit


QUEUE_NAME = "wikipedia_edits"


def save_event(message):
    """Store one RabbitMQ Wikipedia event in the database."""

    event_time = None

    event_time_string = message.get("event_time")

    if event_time_string:
        try:
            event_time = datetime.fromisoformat(
                event_time_string.replace("Z", "+00:00")
            )
        except ValueError:
            pass

    # Keep ordinary Python values outside the SQLAlchemy session.
    saved_user = message.get("user")
    saved_title = message.get("title", "Unknown")

    with app.app_context():
        edit = WikipediaEdit(
            title=saved_title,
            user=saved_user,
            wiki=message.get("wiki"),
            change_type=message.get("change_type"),
            bot=message.get("bot", False),
            event_time=event_time
        )

        db.session.add(edit)
        db.session.commit()

    return saved_user, saved_title


def main():
    print("Connecting to RabbitMQ...")

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")
    )

    channel = connection.channel()

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body)

            saved_user, saved_title = save_event(message)

            print(
                f"Stored: {saved_user} edited {saved_title}"
            )

            # Only remove the message after the DB commit succeeds.
            ch.basic_ack(
                delivery_tag=method.delivery_tag
            )

        except Exception as exc:
            print(f"Error processing message: {exc}")

            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True
            )

    channel.basic_qos(
        prefetch_count=10
    )

    # This is the critical registration step.
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
        auto_ack=False
    )

    print("Waiting for Wikipedia edit events...")
    print("Press CTRL+C to stop.")

    try:
        channel.start_consuming()

    except KeyboardInterrupt:
        print("\nStopping consumer...")

        if channel.is_open:
            channel.stop_consuming()

    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()