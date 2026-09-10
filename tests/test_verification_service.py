from src.verification_service import SignupRequest, send_verification


class FakeClient:
    def __init__(self):
        self.calls = []

    def send(self, **kwargs):
        self.calls.append(kwargs)
        return {"message_id": "msg_test"}


def test_signup_dispatches_link_and_records_release_events():
    client = FakeClient()
    result = send_verification(SignupRequest("maker@example.com", "Mina"), client, base_link="https://x.test/verify")
    assert result.message_id == "msg_test"
    assert result.events[0].name == "signup.accepted"
    assert "token=" in client.calls[0]["html"]
    assert client.calls[0]["to"] == "maker@example.com"
