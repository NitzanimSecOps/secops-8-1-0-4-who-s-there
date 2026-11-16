"""Local tester for protocol.py - not the hidden grader.

    python3 selftest.py

Runs your functions on a connected pair of sockets: a message, two messages sent together, a closed
connection and a reset connection. Each check prints OK or FAILED. Change the examples and try your own.
"""
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import recv_exact, recv_msg, send_msg


def tcp_pair():
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    a = socket.create_connection(listener.getsockname())
    b, _ = listener.accept()
    listener.close()
    for s in (a, b):
        s.settimeout(5)
    return a, b


def check(name, func, expected, hint=None):
    """Run func(), compare with expected, print OK / FAILED (an exception is a failure, not a crash)."""
    try:
        got = func()
    except Exception as e:
        print(f"FAILED  {name}: raised {type(e).__name__}: {e}")
        if hint:
            print(f"        hint: {hint}")
        return False
    if got == expected:
        print(f"OK      {name}: {got!r}")
        return True
    print(f"FAILED  {name}: expected {expected!r}, got {got!r}")
    return False


def main():
    results = []

    a, b = tcp_pair()
    send_msg(a, b"hello")
    results.append(check("one message", lambda: recv_msg(b), b"hello"))

    send_msg(a, b"first")
    send_msg(a, b"second")
    results.append(check("two messages", lambda: (recv_msg(b), recv_msg(b)), (b"first", b"second")))

    a.sendall(b"abcdef")
    results.append(check("recv_exact 4 then 2", lambda: (recv_exact(b, 4), recv_exact(b, 2)), (b"abcd", b"ef")))

    a.sendall(b"abc")
    a.close()
    results.append(check("closed in the middle", lambda: recv_exact(b, 10), None))
    b.close()

    a, b = tcp_pair()
    a.sendall(b"abc")
    a.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    a.close()
    results.append(check(
        "reset in the middle", lambda: recv_exact(b, 10), None,
        hint="a reset connection makes sock.recv raise ConnectionResetError instead of returning b''. "
             "recv_exact must catch it and return None.",
    ))
    b.close()

    print(f"\n{sum(results)}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
