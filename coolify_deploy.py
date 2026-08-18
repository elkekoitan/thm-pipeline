#!/usr/bin/env python3
"""Deploy thm-pipeline to Coolify via API (GitHub source)."""
import json
import os
import sys
import urllib.request
import urllib.error

TOKEN = "2|6O7SL3JavwY4mfKsg0HAQdkmc7hx7qITx8N9kMix92ea5a27"
BASE = "http://84.46.255.141:8000"


def api(path, method="GET", payload=None):
    url = f"{BASE}{path}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "status":
        code, body = api("/api/v1/resources")
        names = [r.get("name") for r in body]
        print(f"HTTP {code}: {len(body)} resources -> {names}")
        for r in body:
            if "thm" in str(r.get("name", "")).lower() or "pipeline" in str(r.get("name", "")).lower():
                print(json.dumps({k: r.get(k) for k in
                                  ("id", "name", "status", "fqdn", "subdomain", "ports_mappings")}, indent=2))
    elif action == "create":
        payload = {
            "project_uuid": os.environ.get("PROJECT_UUID", "default"),
            "environment_name": "production",
            "type": "public",
            "public_type": "dockerfile",
            "dockerfile": "Dockerfile",
            "docker_registry_image_name": None,
            "docker_registry_image_tag": None,
            "name": "thm-pipeline",
            "description": "THM Instrumental production pipeline",
            "fqdn": None,
            "ports_exposes": "8000",
            "ports_mappings": "8000:8000",
            "environment_variables": [
                {"key": "YOUTUBE_REFRESH_TOKEN",
                 "value": os.environ.get("YOUTUBE_REFRESH_TOKEN", "PLACEHOLDER")},
            ],
        }
        code, body = api("/api/v1/resources", "POST", payload)
        print(f"create -> HTTP {code}: {json.dumps(body, indent=2)[:800]}")
    elif action == "github":
        payload = {
            "project_uuid": os.environ.get("PROJECT_UUID", "default"),
            "environment_name": "production",
            "type": "github",
            "github_type": "public",
            "repository_project_id": None,
            "git_repository": "elkekoitan/thm-pipeline",
            "git_branch": "main",
            "git_commit_sha": "HEAD",
            "name": "thm-pipeline",
            "description": "THM Instrumental production pipeline",
            "build_pack": "dockerfile",
            "base_directory": "/",
            "dockerfile_location": "Dockerfile",
            "ports_exposes": "8000",
            "ports_mappings": "8000:8000",
            "custom_labels": None,
            "custom_docker_run_options": "-v /data/thm:/data",
            "environment_variables": [
                {"key": "THM_DATA_DIR", "value": "/data"},
            ],
        }
        code, body = api("/api/v1/resources", "POST", payload)
        print(f"github -> HTTP {code}: {json.dumps(body, indent=2)[:1000]}")


if __name__ == "__main__":
    main()
