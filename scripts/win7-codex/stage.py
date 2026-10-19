"""Stage the self-contained runtime and its licenses from fixed build inputs."""

import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import urllib.request
import zipfile

from prepare import BASELINE

source, output = map(Path, sys.argv[1:3])
output.mkdir(parents=True, exist_ok=True)
binary = source / "codex-rs/target/x86_64-win7-windows-msvc/dev-small/codex.exe"
shutil.copyfile(binary, output / "codex.exe")
shutil.copyfile(source / "LICENSE", output / "CODEX-LICENSE.txt")
archive = urllib.request.urlopen(
    "https://github.com/rprichard/winpty/releases/download/0.4.3/winpty-0.4.3-msvc2015.zip",
    timeout=120,
).read()
if hashlib.sha256(archive).hexdigest() != "35a48ece2ff4acdcbc8299d4920de53eb86b1fb41e64d2fe5ae7898931bcee89":
    raise SystemExit("winpty archive SHA-256 mismatch")
with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
    for name in ["winpty.dll", "winpty-agent.exe"]:
        (output / name).write_bytes(zipped.read("x64/bin/" + name))
    (output / "WINPTY-LICENSE.txt").write_bytes(zipped.read("LICENSE"))
(output / "codex-runtime.json").write_text(json.dumps({
    "version": "0.130.0-alpha.5",
    "source": "https://github.com/openai/codex",
    "source_commit": BASELINE,
    "compatibility_source": "https://github.com/HaiKuoTianKong179/codex-win7-port",
    "compatibility_commit": "31899c3041c5934c027da052d41797dac76d7eaf",
    "target": "x86_64-win7-windows-msvc",
    "rust": "1.95.0",
    "winpty": "0.4.3",
    "sha256": hashlib.sha256((output / "codex.exe").read_bytes()).hexdigest(),
}, indent=2) + "\n")
