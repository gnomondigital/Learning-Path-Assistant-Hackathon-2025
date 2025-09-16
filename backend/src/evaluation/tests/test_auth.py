import pytest


class User:
    def __init__(self, identifier):
        self.identifier = identifier


def fake_auth_callback(username, password):
    if username == "alice" and password == "pw":
        return User(identifier=username)
    return None


class Context:
    def __init__(self, auth_info=None):
        self.auth_info = auth_info


class Message:
    def __init__(self, content):
        self.content = content


class AuthInfo:
    def __init__(self, user):
        self.user = user


async def fake_on_message(msg, context):
    if not getattr(context, "auth_info", None):
        return "Not logged in"
    return f"Hello {context.auth_info.user.identifier}"


def test_auth_allows():
    user = fake_auth_callback("alice", "pw")
    assert user.identifier == "alice"


@pytest.mark.asyncio
async def test_on_message_blocks_when_not_logged_in():
    msg = Message(content="hi")
    context = Context(auth_info=None)
    resp = await fake_on_message(msg, context)
    assert resp == "Not logged in"
