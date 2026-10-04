"""A local fake Gemini server for offline tests: no real API call, no real key.

Point the SDK at it with GOOGLE_GEMINI_BASE_URL=server.url (and a dummy GEMINI_API_KEY). Each connection takes
the next behaviour from server.queue (default "ok"):
    ok          200 + one SSE chunk, then close
    slow:N      the same after N seconds
    stall       read the request, never answer (silent from the start)
    stall_mid   send the headers and one chunk, then go silent (stall mid-stream, like the 415 s hang)
"""

import socket
import threading
import time

ANSWER = "OK từ server giả"
HEADERS = b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nConnection: close\r\n\r\n"
CHUNK = ('data: {"candidates":[{"content":{"parts":[{"text":"' + ANSWER + '"}],"role":"model"},'
         '"finishReason":"STOP"}],"usageMetadata":{"promptTokenCount":5,"candidatesTokenCount":4}}\r\n\r\n').encode()


class FakeGemini:
    def __init__(self):
        self.queue, self.connections, self.keys = [], 0, set()
        self.stop = threading.Event()
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen()
        self.url = f"http://127.0.0.1:{self.sock.getsockname()[1]}"
        threading.Thread(target=self.serve, daemon=True).start()

    def serve(self):
        while not self.stop.is_set():
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            self.connections += 1
            behaviour = self.queue.pop(0) if self.queue else "ok"
            threading.Thread(target=self.handle, args=(conn, behaviour), daemon=True).start()

    def handle(self, conn, behaviour):
        with conn:
            head = self.read_request(conn)
            for line in head.split(b"\r\n"):
                if line.lower().startswith(b"x-goog-api-key:"):
                    self.keys.add(line.split(b":", 1)[1].strip().decode())
            if behaviour.startswith("slow:"):
                self.stop.wait(float(behaviour.split(":")[1]))  # Event.wait: unaffected by patching time.sleep
            if behaviour == "ok" or behaviour.startswith("slow:"):
                conn.sendall(HEADERS + CHUNK)
                return
            if behaviour == "stall_mid":
                conn.sendall(HEADERS + CHUNK)
            self.hold(conn)

    @staticmethod
    def read_request(conn):
        data = b""
        while b"\r\n\r\n" not in data:
            data += conn.recv(65536)
        head, body = data.split(b"\r\n\r\n", 1)
        length = next((int(line.split(b":")[1]) for line in head.split(b"\r\n")
                       if line.lower().startswith(b"content-length:")), 0)
        while len(body) < length:
            body += conn.recv(65536)
        return head

    def hold(self, conn):
        """Keep the connection open and silent until the client gives up (or 60 s)."""
        conn.settimeout(0.2)
        deadline = time.monotonic() + 60
        while not self.stop.is_set() and time.monotonic() < deadline:
            try:
                if conn.recv(1024) == b"":
                    return
            except socket.timeout:
                continue
            except OSError:
                return

    def close(self):
        self.stop.set()
        self.sock.close()
