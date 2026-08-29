from src.app import app

def test_echo_route():
    client = app.test_client()

    response = client.post(
        "/echo_user_input",
        data={"user_input": "Tony"}
    )

    assert response.status_code == 200
    assert response.data == b"You entered: Tony"
    