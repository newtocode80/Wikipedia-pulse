import json
from unittest.mock import MagicMock, patch

from src.collector import collect_edits, QUEUE_NAME


def test_collector_publishes_wikipedia_event_with_mocks():
    fake_event = {
        "title": "Artificial intelligence",
        "user": "TestEditor",
        "wiki": "enwiki",
        "type": "edit",
        "bot": False,
        "server_name": "en.wikipedia.org",
        "meta": {
            "domain": "en.wikipedia.org",
            "dt": "2026-09-02T18:00:00Z"
        }
    }

    fake_response = MagicMock()
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False
    fake_response.raise_for_status.return_value = None
    fake_response.iter_lines.return_value = [
        "data:" + json.dumps(fake_event)
    ]

    fake_connection = MagicMock()
    fake_channel = MagicMock()

    with patch(
        "src.collector.requests.get",
        return_value=fake_response
    ), patch(
        "src.collector.create_rabbit_connection",
        return_value=(fake_connection, fake_channel)
    ):
        collect_edits(limit=1)

    fake_channel.basic_publish.assert_called_once()

    publish_call = fake_channel.basic_publish.call_args

    assert publish_call.kwargs["exchange"] == ""
    assert publish_call.kwargs["routing_key"] == QUEUE_NAME

    published_message = json.loads(
        publish_call.kwargs["body"]
    )

    assert published_message["title"] == "Artificial intelligence"
    assert published_message["user"] == "TestEditor"
    assert published_message["wiki"] == "enwiki"
    assert published_message["change_type"] == "edit"
    assert published_message["bot"] is False
    assert published_message["event_time"] == "2026-09-02T18:00:00Z"

    fake_connection.close.assert_called_once()
