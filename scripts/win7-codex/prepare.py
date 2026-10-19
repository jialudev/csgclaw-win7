"""Apply the audited patch to its exact baseline and remove local-only paths."""

import argparse
import os
from pathlib import Path
import subprocess

BASELINE = "2685e3a4cec1cf6ec8df5231bf2311ff7ae9551f"
ROOT = Path(__file__).resolve().parent
OLD_HOOK = "C:/Users/haiku/ZCodeProject/win7-codex-port/tools/delayhook-logging2.obj"
OLD_LIB = "C:/Users/haiku/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/windows_x86_64_msvc-0.48.5/lib"


def prepare(source):
    actual = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != BASELINE:
        raise SystemExit(f"Unexpected Codex source revision: {actual}")
    patch = str(ROOT / "compat.patch")
    for options in (["--check"], []):
        subprocess.run(["git", "-C", str(source), "apply", *options, patch], check=True)
    rs = source / "codex-rs"
    replacements = {
        rs / "cli/build.rs": (
            f'"{OLD_HOOK}"',
            'std::env::var("CSGCLAW_WIN7_DELAYHOOK_OBJECT").expect("missing delay-load hook")',
        ),
        rs / "windows-sandbox-rs/build.rs": (
            f'"{OLD_HOOK}"',
            'env::var("CSGCLAW_WIN7_DELAYHOOK_OBJECT").expect("missing delay-load hook")',
        ),
    }
    for path, (old, new) in replacements.items():
        text = path.read_text()
        if text.count(old) != 1:
            raise SystemExit(f"Unexpected delay hook source layout: {path}")
        path.write_text(text.replace(old, new))


def configure(source):
    cargo_home = Path(os.environ.get("CARGO_HOME", str(Path.home() / ".cargo")))
    libraries = list(cargo_home.glob("registry/src/*/windows_x86_64_msvc-0.48.5/lib"))
    if len(libraries) != 1:
        raise SystemExit(f"Expected one windows-targets 0.48.5 library: {libraries}")
    path = source / "codex-rs/.cargo/config.toml"
    text = path.read_text()
    if text.count(OLD_LIB) != 1:
        raise SystemExit("Unexpected windows-targets search path in compatibility patch")
    path.write_text(text.replace(OLD_LIB, libraries[0].as_posix()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["apply", "configure"])
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    {"apply": prepare, "configure": configure}[args.command](args.source.resolve())
