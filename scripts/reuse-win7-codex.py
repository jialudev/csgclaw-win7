"""Find a verified runtime from this repo with the identical build-input tree.

Tag builds can reuse a branch's artifact even though GitHub caches are scoped
by ref. Expired artifacts or changed inputs fall back to the normal source build.
"""
import json
import os
from pathlib import Path
import subprocess


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def find_runtime(repo, current_run, expected):
    runs = api(f"repos/{repo}/actions/workflows/win7-compat.yml/runs?event=push&per_page=30")
    for run in runs["workflow_runs"]:
        if str(run["id"]) == current_run:
            continue
        artifacts = api(f"repos/{repo}/actions/runs/{run['id']}/artifacts")["artifacts"]
        name = "codex-win7-x64-" + run["head_sha"]
        if not any(a["name"] == name and not a["expired"] for a in artifacts):
            continue
        jobs = api(f"repos/{repo}/actions/runs/{run['id']}/jobs")["jobs"]
        if not any(j["name"] == "codex-runtime" and j["conclusion"] == "success" for j in jobs):
            continue
        entries = api(f"repos/{repo}/contents/scripts?ref={run['head_sha']}")
        if any(e["name"] == "win7-codex" and e["type"] == "dir" and e["sha"] == expected for e in entries):
            return {"found": "true", "run_id": str(run["id"]), "head_sha": run["head_sha"]}
    return {"found": "false"}


if __name__ == "__main__":
    try:
        expected = subprocess.check_output(
            ["git", "rev-parse", "HEAD:scripts/win7-codex"], text=True
        ).strip()
        result = find_runtime(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_RUN_ID"], expected)
    except (subprocess.CalledProcessError, KeyError, ValueError, OSError, TypeError):
        print("Runtime lookup unavailable; compiling from pinned sources instead.")
        result = {"found": "false"}
    print("Reusable runtime:", result)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.writelines(f"{key}={value}\n" for key, value in result.items())
