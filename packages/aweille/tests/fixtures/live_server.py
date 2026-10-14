"""Run the public application in a restartable process against test storage."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest


class LiveServer:
    def __init__(self, database_path: Path):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self.database_path = database_path
        self.log_path = database_path.parent / "server.log"
        self.process: subprocess.Popen | None = None

    def start(self) -> None:
        with self.log_path.open("ab") as log:
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "aweille.api.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(self.port),
                ],
                env={**os.environ, "AWEILLE_DB_PATH": str(self.database_path)},
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        deadline = time.monotonic() + 15
        while self.process.poll() is None and time.monotonic() < deadline:
            try:
                with urlopen(f"{self.url}/openapi.json", timeout=0.2):
                    return
            except (URLError, TimeoutError):
                time.sleep(0.05)
        self.stop()
        raise RuntimeError(self.log_path.read_text())

    def stop(self) -> None:
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None

    def restart(self) -> None:
        self.stop()
        self.start()


@pytest.fixture
def live_server(database_path: Path):
    server = LiveServer(database_path)
    try:
        server.start()
        yield server
    finally:
        server.stop()
