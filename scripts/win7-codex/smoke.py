"""Check CSGClaw's app-server protocol without credentials or a model call."""

import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading

binary = Path(sys.argv[1]).resolve()
subprocess.run([str(binary), "--version"], check=True, timeout=30)
with tempfile.TemporaryDirectory(prefix="codex-win7-smoke-") as home:
    import os

    process = subprocess.Popen(
        [str(binary), "app-server", "--disable", "plugins", "--disable", "code_mode", "--disable", "code_mode_host", "--listen", "stdio://"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        env={**os.environ, "CODEX_HOME": home},
    )
    lines = queue.Queue()

    def read_lines():
        for line in process.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=read_lines, daemon=True).start()
    try:
        process.stdin.write(json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "clientInfo": {"name": "csgclaw-agent-sdk", "title": "CSGClaw Agent SDK", "version": "0.1.0"},
                "capabilities": {"experimentalApi": True},
            },
        }) + "\n")
        process.stdin.flush()
        while True:
            line = lines.get(timeout=30)
            if line is None:
                raise RuntimeError("Codex exited before app-server initialization")
            message = json.loads(line)
            if message.get("id") == 1:
                if "result" not in message or "error" in message:
                    raise RuntimeError(f"App-server rejected initialization: {message}")
                print("PASS: CSGClaw stdio app-server initialize")
                break
    finally:
        process.kill()
        process.wait(timeout=10)
