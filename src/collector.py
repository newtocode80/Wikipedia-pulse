#!/usr/bin/env python3

import json

import pika
import requests


STREAM_URL = "https://stream.wikimedia.org/v2/stream/recentchange"

QUEUE_NAME = "wikipedia_edits"

HEADERS = {
    "Accept": "text/event-stream",
    "User-Agent": "WikipediaPulse/0.1"
}


def create_rabbit_connection():
    """Connect to RabbitMQ and create the Wikipedia edits queue."""

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")
    )

    channel = connection.channel()

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    return connection, channel


def collect_edits(limit=20):
    """
    Collect recent English Wikipedia edits and publish
    each edit as an event to RabbitMQ.
    """

    collected = 0

    print("Connecting to RabbitMQ...")

    connection, channel = create_rabbit_connection()

    print("Connecting to Wikimedia EventStreams...")

    try:
        with requests.get(
            STREAM_URL,
            headers=HEADERS,
            stream=True,
            timeout=60
        ) as response:

            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):

                if not line:
                    continue

                # Server-Sent Event payloads begin with "data:"
                if not line.startswith("data:"):
                    continue

                try:
                    event = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue

                # Ignore Wikimedia test/canary events
                if event.get("meta", {}).get("domain") == "canary":
                    continue

                # Keep Wikipedia Pulse focused on English Wikipedia
                if event.get("server_name") != "en.wikipedia.org":
                    continue

                message = {
                    "title": event.get("title", "Unknown"),
                    "user": event.get("user"),
                    "wiki": event.get("wiki"),
                    "change_type": event.get("type"),
                    "bot": event.get("bot", False),
                    "event_time": event.get("meta", {}).get("dt")
                }

                channel.basic_publish(
                    exchange="",
                    routing_key=QUEUE_NAME,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2
                    )
                )

                collected += 1

                print(
                    f"{collected}: published "
                    f"{message['user']} edited {message['title']}"
                )

                if collected >= limit:
                    break

    finally:
        connection.close()

    print(
        f"\nPublished {collected} Wikipedia edit events "
        f"to RabbitMQ."
    )


if __name__ == "__main__":
    collect_edits()