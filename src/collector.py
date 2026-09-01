import json
from datetime import datetime

import requests

from src.app import app, db, WikipediaEdit


STREAM_URL = "https://stream.wikimedia.org/v2/stream/recentchange"

HEADERS = {
    "Accept": "text/event-stream",
    "User-Agent": "WikipediaPulse/0.1"
}


def collect_edits(limit=20):
    """
    Collect recent Wikipedia edit events and save them
    to the database.
    """

    collected = 0

    print("Connecting to Wikimedia EventStreams...")

    with requests.get(
        STREAM_URL,
        headers=HEADERS,
        stream=True,
        timeout=60
    ) as response:

        response.raise_for_status()

        with app.app_context():

            for line in response.iter_lines(decode_unicode=True):

                if not line:
                    continue

                # SSE data messages begin with "data:"
                if not line.startswith("data:"):
                    continue

                try:
                    event = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue

                # Wikimedia recommends ignoring canary/test events.
                if event.get("meta", {}).get("domain") == "canary":
                    continue

                # Keep the first version of our project focused
                # on English Wikipedia.
                if event.get("server_name") != "en.wikipedia.org":
                    continue

                event_time = None

                event_time_string = event.get("meta", {}).get("dt")

                if event_time_string:
                    try:
                        event_time = datetime.fromisoformat(
                            event_time_string.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

                edit = WikipediaEdit(
                    title=event.get("title", "Unknown"),
                    user=event.get("user"),
                    wiki=event.get("wiki"),
                    change_type=event.get("type"),
                    bot=event.get("bot", False),
                    event_time=event_time
                )

                db.session.add(edit)

                collected += 1

                print(
                    f"{collected}: "
                    f"{edit.user} edited {edit.title}"
                )

                if collected >= limit:
                    break

            db.session.commit()

    print(f"\nSaved {collected} Wikipedia events to the database.")


if __name__ == "__main__":
    collect_edits()