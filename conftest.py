"""Repository-wide guard: Python tests never reach the network (NOTES.md 2).

Any socket connection to an address other than this machine fails the test at once with a clear message. Browsers are
guarded separately by the `context` fixture in recipes/python/conftest.py.
"""
import ipaddress
import socket

import pytest

_connect = socket.socket.connect


def _is_local(address) -> bool:
    if not isinstance(address, tuple):  # Unix socket path
        return True
    host = address[0]
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _guarded_connect(self, address):
    if not _is_local(address):
        raise OSError(f"test-core: tests never reach the network (tried {address!r}); stub it (recipe network-stub)")
    return _connect(self, address)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
