from src.app import format_echo

def test_format_echo():
    result = format_echo("Tony")

    assert result == "You entered: Tony"